import requests
import json
import threading


import logging
import os
import time
import bs4
import datetime

cacheFile = "Symphony1/cache"
roomOthersLogs = "Symphony1/roomOthers"
CACHE_ENABLE = False

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter(

    '[%(asctime)s] - %(name)s - %(levelname)-8s - [%(filename)s:%(lineno)-5d} %(message)s','%Y-%m-%d %H:%M:%S'
))
output_dir = 'Symphony1/logs'

fh = logging.FileHandler(os.path.join(output_dir,"botDaemon.log"),"a", encoding=None, delay="true")
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter(

    '[%(asctime)s] - %(name)s - %(levelname)-8s - [%(filename)s:%(lineno)-5d} %(message)s', '%Y-%m-%d %H:%M:%S'

))

logger = logging.getLogger('Bridge')
logger.addHandler(ch)
logger.addHandler(fh)
logger.setLevel(logging.INFO)

from threading import Event


class Bridge:
    REAUTH_INTERVAL = 7200
    MAX_RETRY_INTERVAL = 1800

    def __init__(self, botname=None, baseurl=None, baseurlAuth=None, certPath=None):
        dataPath = "Symphony1/logs"
        self.tokens = {}
        self.certFile = certPath + str(botname) +"-cert.pem"
        self.keyFile = certPath + str(botname) + "-key-decrypted.pem"
        self.botname = botname
        self.baseurlAuth = baseurlAuth
        self.baseurl = baseurl
        self.updateDatafeedThread = None
        self.exit = Event()
        self.knownUsers = {}


        if (self.isTokenSaved(dataPath)):
            self.loadTokens(dataPath)
        else:
            self.openSession()
            self.saveTokens(dataPath)

        self.VERIFY=True
        self.botId = self.sessionUser()["id"]

    def isTokenSaved(self,pathToSave):
        return os.path.isfile(pathToSave + "/" + str(self.botname) + "-sessionToken.txt") \
               and os.path.isfile(pathToSave + "/" + str(self.botname)  + "-keyManagerToken.txt")

    def saveTokens(self,pathToSave):
        file = open(pathToSave + "/" + str(self.botname) + "-sessionToken.txt", "w")
        file.write(self.tokens["sessionToken"])
        file.close()

        file = open(pathToSave + "/" + str(self.botname) + "-keyManagerToken.txt", "w")
        file.write(self.tokens["keyManagerToken"])
        file.close()

    def loadTokens(self,pathToSave):
        file = open(pathToSave + "/" + str(self.botname) + "-sessionToken.txt", "r")
        self.tokens["sessionToken"]="".join(file.readlines()).strip()
        file.close()

        file = open(pathToSave + "/" + str(self.botname) + "-keyManagerToken.txt", "r")
        self.tokens["keyManagerToken"] = "".join(file.readlines()).strip()
        file.close()


    def getTextFromHTML(self,messageToConvert):

        soup = bs4.BeautifulSoup(messageToConvert, "html.parser")
        convertedMessage = soup.get_text()
        return convertedMessage

    def saveAllTheMessageOfRoom(self,roomId):
        messages = self.getAllMessagesOfAChatRoom(roomId, 500)
        stringToWrite =""
        for message in messages:
            timeMilliseconds = message["timestamp"]
            dateTimeMessage = datetime.datetime.fromtimestamp(timeMilliseconds / 1000.0)
            # strftime("%Y-%m-%d %H:%M:%S", gmtime())
            timeString = dateTimeMessage.strftime('%d-%b-%Y %H:%M:%S')
            # roomOthers = "D:\D-DRIVE\DOCUMENT\python\Symphony1\\roomOthers"
            fileToUse = "{}\{}-{}.txt".format(roomOthersLogs,self.botname,roomId)

            if(stringToWrite!=""): stringToWrite += "\n"
            stringToWrite+="[{}] {} said {}".format(timeString, message["user"]["displayName"],
                                             self.getTextFromHTML(message["message"]))
            file = open(fileToUse, "w")

            file.write(stringToWrite.encode('ascii', 'ignore').decode('ascii'))
            file.close()

    def  saveAllTheChatsInAllTheRooms(self):
        #listTheChatRooms(entry["id"])
        for entry in self.listUserStream():
            self.saveAllTheMessageOfRoom(entry["id"])
            #messages = bridge.getAllMessagesOfAChatRoom("_9yyUPV4J8KwfZhBqywD8X___pxWBvKgdA", "notyetrequired")



    def get_botId(self):
        return self.botId

    def cleanUrlForWindowsFileName(self,url):
        url = url.replace("/", "_")
        url = url.replace(":", "")
        url = url.replace("?", "_")
        return url

    def urlToRequestIsInCache(self,url):
        url = self.cleanUrlForWindowsFileName(url)

        filePath = cacheFile + "/" + url + ".txt"
        return os.path.isfile(filePath)

    def timeStampOfCachedContent(self,url):
        print("herePutTimeStamp")

    def dumpResultToCache(self,url,json_data):
        url = self.cleanUrlForWindowsFileName(url)

        filePath = cacheFile + "/" + url +".txt"
        with open(filePath,"w") as json_cache:
            # print(filePath)

            json.dump(json_data,json_cache)

    def loadResultFromCache(self,url):
        url = self.cleanUrlForWindowsFileName(url)
        filePath = cacheFile + "/" + url + ".txt"
        with open(filePath) as json_cache:
            d = json.load(json_cache)
            return d

    def api(self, method, path, ttl=3, **kwargs):
        return self.apiWithCache( method, path, "read", ttl=3, **kwargs)

    def apiWithCache(self, method, path, typeOfQuery="read",ttl=3,  **kwargs):
        #typeOfQuery used to decide if we use cache or not
        #because not all read query are get so we can't use get/post to decide

        r = None

        urlToRequest="{}/{}".format("https://develop2.symphony.com", path)

        if(typeOfQuery == "read" and CACHE_ENABLE and self.urlToRequestIsInCache(urlToRequest)):
            logger.info("[API]CACHE {}".format(urlToRequest))
            jsonFromCache = self.loadResultFromCache(urlToRequest)
            return jsonFromCache

        else:
            logger.info("[API]Requesting {}".format(urlToRequest))
            r = requests.request(method, urlToRequest, verify=self.VERIFY, headers=self.tokens, cert=(self.certFile, self.keyFile),**kwargs)
            #r = requests.request(method, "https://develop2.symphony.com/agent/v2/HealthCheck", cert=(self.certFile, self.keyFile),**kwargs)
            r.raise_for_status()

            logger.info("[API]Status {}".format(r.status_code))
            if r.status_code == 200:
                if (typeOfQuery == "read"): self.dumpResultToCache(urlToRequest,r.json())
                return r.json()
            return None


    def testEndPoint(self):
        return self.api("post", "agent/v1/util/echo", json={"message":"echo"})

    def sessionUser(self):
        return self.api("get", "pod/v2/sessioninfo")

    def listUserStream(self,type_=None):
        if type_:
            data = {"streamTypes": [{"type":t} for t in type_]}
            return self.api("post", "pod/v1/streams/list", json=data)
        return self.apiWithCache("post", "pod/v1/streams/list","read")

    def userLookupById(self,userId):
        if userId in self.knownUsers:
            return self.knownUsers[userId]
        else:
            userDetails = self.apiWithCache("get","/pod/v2/user?uid={}&local=true".format(userId),"read")
            self.knownUsers[userId] = userDetails
            return userDetails

    def getUserStreamsInCsvFormat(self):
        userStreamsCsv = ""
        for entry in self.listUserStream():
            # printprettyJSON(entry)
            roomId = entry["id"]
            roomType = entry["streamType"]["type"]
            roomFootPrint = ""
            if ("streamAttributes" in entry):  # can also use entry["streamTye"] ==
                for userInStream in entry["streamAttributes"]["members"]:
                    memberDetails = self.userLookupById(userInStream)
                    if (roomFootPrint != ""): roomFootPrint += " & "
                    roomFootPrint += "{}({})".format(memberDetails["displayName"],userInStream) 
            else:
                roomFootPrint = entry["roomAttributes"]["name"]
            roomStatus = entry["active"]
            if(userStreamsCsv!=""):userStreamsCsv+= '\n'
            userStreamsCsv+="{}`{}`{}`{}".format(roomId, roomType, roomFootPrint, roomStatus)
        return userStreamsCsv

    def searchForRooms(self,roomToFind):

        jsonToQuery = {
            "query": roomToFind,
            "active": True,
            "member": {"id": self.botId}
        }

        return self.api("post", "pod/v3/room/search", json=jsonToQuery)


    def openSession(self):
        logger.info("Requesting {}".format("https://develop2-api.symphony.com:8444/sessionauth/v1/authenticate"))
        r = requests.post('https://develop2-api.symphony.com:8444/sessionauth/v1/authenticate',
                          cert=(self.certFile, self.keyFile))
        data = json.loads(r.text)
        self.tokens["sessionToken"] = data['token']

        logger.info("Requesting {}".format("https://develop2-api.symphony.com:8444/keyauth/v1/authenticate"))
        r = requests.post('https://develop2-api.symphony.com:8444/keyauth/v1/authenticate',
                          cert=(self.certFile, self.keyFile))
        data = json.loads(r.text)
        self.tokens["keyManagerToken"] = data['token']

        logger.info("Tokens retrieved {}".format(self.tokens))

    def _getDatafeed(self, timeout=5):
        r = None
        r = requests.post("{}/agent/v4/datafeed/create".format(self.baseurl), headers=self.tokens, cert=(self.certFile, self.keyFile))
        r.raise_for_status()
        if r.status_code == 200:
            sid = r.json()
            self.tokens["id"] = sid["id"]
            print("The token is {} ".format(self.tokens["id"]))

    def sendMessageToStream(self,messageToSend,userIds, entitydata=None):

        if entitydata:
            entitydataId = list(entitydata.keys())[0]
            logger.info(entitydataId)
            message = '<messageML><p>{}</p><div class="entity" data-entity-id="{}" /></messageML>'.format(messageToSend, entitydataId)
        else:
            message = '<messageML><p>{}</p></messageML>'.format(messageToSend)

        files = {'message': (None, message)}
        if entitydata:
            entitydata[entitydataId]['question'] = messageToSend
            files['data'] = json.dumps(entitydata)
            

        files['symphonyUSERS'] = (None, str(userIds))

        stream = userIds
        urlToSend="{}/v1/stream/{}/message/create".format(self.baseurl, stream)

        import pprint
        pprint.pprint(files)

        self.api("post","agent/v4/stream/{}/message/create".format(stream),files=files)
        #r = requests.post("{}/agent/v4/stream/{}/message/create".format(self.baseurl,stream), files=files, headers=self.tokens,cert=(self.certFile, self.keyFile))
        

    def renameRoom(self,roomId, name, membersCanInvite=True,discoverable=True,public=False,readOnly=False,copyProtected=False,crossPod=False,viewHistory=False):

        data ={"name" : name, "membersCanInvite" : membersCanInvite, "discoverable" : discoverable,
               "public" : public, "readOnly" : readOnly, "copyProtected" : copyProtected, "crossPod" : crossPod, "viewHistory" : viewHistory
               }

        self.apiWithCache("post","pod/v3/room/{}/update".format(roomId),"write",json=data)



    def _updateDatafeed(self):
        while not self.exit.is_set():
            self.exit.wait(Bridge.REAUTH_INTERVAL)
            self._getDatafeed()

    def createRoom(self,name, description, membersCanInvite=True,discoverable=True,public=False,readOnly=False,copyProtected=False,crossPod=False,viewHistory=False):

        data ={"name" : name, "description" : description, "membersCanInvite" : membersCanInvite, "discoverable" : discoverable,
               "public" : public, "readOnly" : readOnly, "copyProtected" : copyProtected, "crossPod" : crossPod, "viewHistory" : viewHistory
               }

        return self.apiWithCache("post","/pod/v3/room/create","write",json=data)

    def addMember(self,roomId,userId):
        return self.apiWithCache("post","pod/v1/room/{}/membership/add".format(roomId),"write",json={"id":userId})

    def roomMembers(self,roomId):
        return self.apiWithCache("get","/pod/v2/room/{}/membership/list".format(roomId),"read")

    def promoteOwner(self,roomId,userId):
        return self.apiWithCache("post", "pod/v1/room/{}/membership/promoteOwner".format(roomId),"write", json={"id": userId})

    def removeMember(self,roomId, userId):
        return self.apiWithCache("post", "pod/v1/room/{}/membership/remove".format(roomId),"write", json={"id": userId})

    def deactivateChatRoom(self,roomId):
        return self.apiWithCache("post","pod/v1/room/{}/setActive?active=false".format(roomId),"write")

    def activateChatRoom(self,roomId):
        return self.apiWithCache("post","pod/v1/room/{}/setActive?active=true".format(roomId),"write")

    def getAllMessagesOfAllChatRoom(self):
        print("todo")

    def getAllMessagesOfAChatRoom(self,roomId,numberOfMessages):

        oneDay = 1000 * 60 * 60 * 24
        startDate = oneDay * 10
        return self.api("get","agent/v4/stream/{}/message?since=1461808167175&limit={}".format(roomId,numberOfMessages,"read"))
        # return self.api("get","agent/v4/stream/{}/message?{}".format(roomId,"since=1808167175&limit=100","read"))


    def subscribe(self, callback):
        self._getDatafeed()
        self.subscribed = True
        def subscribeimpl():
            while self.subscribed:
                print("reading messages")
                r = None
                r = requests.get("{}/agent/v4/datafeed/{}/read".format(self.baseurl,self.tokens["id"]), headers=self.tokens, cert=(self.certFile, self.keyFile))
                r.raise_for_status()
                if r.status_code == 200:
                    callback(r.json())

        if not self.updateDatafeedThread:
            self.updateDatafeedThread = threading.Thread(target=self._updateDatafeed)
            self.updateDatafeedThread.daemon = True
            self.updateDatafeedThread.start()

            t = threading.Thread(target=subscribeimpl)
            t.start()
        else:
            print("noUpdate")