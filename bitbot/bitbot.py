import os
import requests
import tornado

import tornado.options

from tornado.options import define, options
from tornado import gen
from tornado.web import RequestHandler, StaticFileHandler
from tornado.template import Template

import bs4
from xml.etree import ElementTree

from Bridge import Bridge
import pprint
from datetime import datetime

class TestRequestHandler(RequestHandler):
    def initialize(self):
        self.entitydata = {
            "object0001":
            {
                "type":     "com.symphony.hackathon.bitweaver",
                "version":  "1.0",
                "data":[]
            }
        }
    def post(self, streamId):
        self.application.bridge.sendMessageToStream('hello', streamId, self.entitydata)


entityDataAll = {
    "recommend" : {
            "object0001":
            {
                "type":     "com.symphony.hackathon.bitweaver",
                "version":  "1.0",
                "data":[]
            }
        }
}

bridge = Bridge("bot.user21", 
                "https://develop2.symphony.com", 
                "https://develop2-api.symphony.com:8444",
                "")

duplicateId = ''

class WhoRequestHandler(RequestHandler):

    voteslip = """
        <style>
            form div.box {
                display: inline-block;
                margin: 10px
            }

            .btn-info {
                color: #fff;
                background-color: #17a2b8;
                border-color: #17a2b8;
            }

            .img-circle {
                border-radius: 50%;
                width: 38px;
                height: 38px;
            }

            .btn {
                display: inline-block;
                text-align: center;
                white-space: nowrap;
                vertical-align: middle;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
                user-select: none;
                border: 1px solid transparent;
                font-size: 10ox;
                border-radius: .25rem;
                transition: color .15s ease-in-out,background-color .15s ease-in-out,border-color .15s ease-in-out,box-shadow .15s ease-in-out;
            }
        </style>
        <div>
            <div> Who do you like to talk to? </div>
            <form method="POST" action="{{askerId}}">
                {% for name, userid in persons %}
                <div class="box">
                    <div>
                        <img src='/images/{{userid}}.jpg' class='img-circle'>
                    </div>
                    <div>{{name}}</div>
                    <div>
                        <input type="radio" name="recommend" value="{{userid}}">
                    </div>
                </div>
                {% end %}
                <input type="hidden" name="question" value="{{question}}">
                <div class="box"><button type="submit" class="btn btn-info">Submit</button></div>		
            </form>
        </div>
    """

    def initialize(self):
        self.template = Template(self.voteslip)


    def get(self, askerId):

        if askerId:
            persons = [
                ('Jimmy','349026222342271'),
                ('Clement', '349026222342283'),
                ('Lucie', '349026222342284'),
            ]
            question = self.get_argument('question', '')
            self.write(self.template.generate(askerId=askerId, persons=persons, question=question))
        else:
            self.write("userId not found")

    def post(self, askerId):
        answerId = self.get_body_argument('recommend')
        question = self.get_body_argument('question')

        roomInfo = self.application.bridge.createRoom('Room %s' % datetime.now(), 'Question V about javascript')
        roomId = roomInfo['roomSystemInfo']['id']
        duplicateId = roomId
        self.application.bridge.addMember(roomId, answerId)
        self.application.bridge.addMember(roomId, askerId)
        self.application.bridge.sendMessageToStream(question, roomId)

        self.write("You are connected")

class Application(tornado.web.Application):
    def __init__(self, bridge):
        self.bridge = bridge

        handlers = [
            (r"/who/([^/]*)", WhoRequestHandler),
            (r"/test/([^/]*)", TestRequestHandler),
            (r"/images/(.*)", StaticFileHandler, {"path": "./images"},)
        ]

        settings = dict(
            autoescape=None,
            debug=True
        )
        tornado.web.Application.__init__(self, handlers, **settings)

def main(bridge, port=443):
    ssl_options={
        "certfile": 'bot.user21-cert.pem',
        "keyfile": 'bot.user21-key-decrypted.pem'
    }
    http_server = tornado.httpserver.HTTPServer(Application(bridge), ssl_options=ssl_options)
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()

def getTextFromHTML(messageToConvert):
    soup = bs4.BeautifulSoup(messageToConvert, "html.parser")
    convertedMessage = soup.get_text()
    return convertedMessage

botId=bridge.get_botId()

duplicates = {
    ('python', 'list'):{
        'roomId':'9DLRz7obGwtJItDI_HivPX___pwxPcdNdA'
    }
}

def checkDuplicate(sentence):
    # tokens = sentence.split(' ')
    # if 'python' in tokens and 'list' in tokens:
    #     return duplicates[('python', 'list')]
    # else:
    #     return
    return duplicateId
    
def callback(messages):
    for message in messages:
        if "messageSent" in message["payload"]:
            # prevent bot replying itself
            fromId = message["payload"]["messageSent"]["message"]["user"]["userId"]
            if fromId != botId:
                # remove tags in te presentationML"
                bodyXML = ElementTree.fromstring(
                    message["payload"]["messageSent"]["message"]["message"].encode("utf-8"))
                body = ElementTree.tostring(bodyXML, encoding="utf-8", method="text")

                # get a message from user
                streamId = message["payload"]["messageSent"]["message"]["stream"]["streamId"]
                streamType = message["payload"]["messageSent"]["message"]["stream"]["streamType"]
                messageToReply = message["payload"]["messageSent"]["message"]["message"]

                messageToReply = getTextFromHTML(messageToReply)
                print(messageToReply)

                if streamType == 'ROOM':
                    if 'thank you' in messageToReply.lower():
                        botmessage = """
                        It looks like you have an anwser. 
                        It would be great to give proper room name for future reference.
                        [write down room name here] 
                        """
                        bridge.sendMessageToStream(botmessage, streamId)
                    elif messageToReply.startswith('[') and messageToReply.endswith(']'):
                        bridge.renameRoom(streamId, messageToReply[1:-1])
                else:
                    roomId = duplicateId
                    print('duplicateId'+roomId)
                    if roomId:
                        botmessage = """
                            It looks like we have duplicate
                            I have added you to previous discussion 
                        """
                        bridge.sendMessageToStream(botmessage, streamId)
                        bridge.removeMember(roomId, fromId)
                        bridge.addMember(roomId, fromId)
                    else:                  
                        entitydata = entityDataAll['recommend']
                        entitydata['object0001']['fromUserId'] = fromId

                        bridge.sendMessageToStream(messageToReply, streamId, entitydata)

if __name__ == "__main__":
    bridge.subscribe(callback)
    main(bridge, port=8092)
