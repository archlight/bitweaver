import requests
import json

authurl = 'https://develop2-api.symphony.com:8444/sessionauth/v1/authenticate'
keymgrurl = 'https://develop2-api.symphony.com:8444/keyauth/v1/authenticate'
podurl = 'https://develop2-api.symphony.com:8444/agent/v4/stream/%s/message/create'
botid = 'bot.user21'

accessToken = {}
r = requests.post(authurl, cert=('bot.user21-cert.pem', 'bot.user21-key-decrypted.pem'))
accessToken['sessionToken'] = r.json()['token']

r = requests.post(keymgrurl, cert=('bot.user21-cert.pem', 'bot.user21-key-decrypted.pem'))
accessToken['keyManagerToken'] = r.json()['token']

d = {
    "object0001":
    {
        "type":     "com.symphony.hackathon.bitweaver",
        "version":  "1.0",
        "data":
        [
            {
                "type":     "com.symphony.hackathon.bitweaver.person",
                "value":    "Wei"
            },
            {
                "type":     "com.symphony.hackathon.bitweaver.person",
                "value":    "Clement"
            }
        ]
    }
}
message = "<messageML><p>{}</p></messageML>".format('Hello')
files = {'message': (None, message), 'data':d}

streamId = 'LeKYFCKLJF6gTk-N4H_3w3___pwyjypqdA'
r = requests.post(podurl % streamId, headers=accessToken, files=files)