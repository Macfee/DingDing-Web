#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import re
import json
import os
import re
import time
import random
from websocket import create_connection
import qrcode_terminal
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy import create_engine 
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

## 消息入库
class DingModel(Base):
    __tablename__ = 'ding'
    mid = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    message_id = Column(String(255))
    message = Column(Text())
    current_time = Column(String(255),unique=True)
    
engine = create_engine("sqlite:///test.db")
Base.metadata.create_all(engine)
db_session = sessionmaker(bind=engine)


## 钉钉主程序
class Ding():
    def __init__(self):
        self.res = requests.session()
        self.code = ''
        self.qr_url = ''
        self.app_key = '85A09F60A599F5E1867EAB915A8BB07F'
        self.ws = create_connection('wss://webalfa-cm10.dingtalk.com/long', header={'Upgrade': 'websocket', 'Connection': 'Upgrade'})
        self.server_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36 OS(windows/10.0) Browser(chrome/84.0.4147.89) DingWeb/3.8.10 LANG/zh_CN"
        self.client_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"
        self.ding_server_url = "https://im.dingtalk.com/"
        
    @staticmethod
    def mid():
        return "".join(random.sample("abcdef0123456789",random.randint(8,8))) + ' 0'
    
    def generate_login_qrcode(self):
        r = self.res.get('https://login.dingtalk.com/user/qrcode/generate.jsonp?callback=angular.callbacks._0')
        html = re.findall('\((.*?)\)', r.text, re.S)[0]
        callback = json.loads(html)
        if callback['success'] == True:
            self.code = callback['result']
            self.qr_url = 'http://qr.dingtalk.com/action/login?code='+self.code
            qrcode_terminal.draw(self.qr_url,3)
            # callback['result']
        else:
            print('Error01:返回值为否')
 
    def check_login_status(self):
            um_data = {'data': '106!woxiangqiaoni','xa': 'dingding','xt': ''}
            r = self.res.post('https://ynuf.aliapp.org/service/um.json', data=um_data)
            um = r.json()
            self.tn = um['tn']
            self.um_id = um['id']
            time.sleep(3)
            
            url = 'https://login.dingtalk.com/user/qrcode/is_logged.jsonp'
            params = {
                'appKey': self.app_key,
                'callback': None,
                'pdmModel': 'Windows Unknown',
                'pdmTitle': 'Windows Unknown Web',
                'pdmToken': self.tn,
                'qrcode': self.code
            }
            headers = {
                'accept': '*/*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'zh-CN,zh;q=0.9',
                'referer': self.ding_server_url,
                'sec-fetch-dest': 'script',
                'sec-fetch-mode': 'no-cors',
                'sec-fetch-site': 'same-site',
                'user-agent': self.client_user_agent
            }
            while True:
                result  = self.res.get(url, params=params, headers=headers)
                content = json.loads(re.findall('onJSONPCallback\((.*?)\);$', result.text, re.S)[0])
                if content['success'] == True:
                    print("登陆成功")
                    break
                time.sleep(2)

            self.access_token = content['result']['accessToken']
            self.app_key = content['result']['appKey']
            self.tmp_code = content['result']['tmpCode']
            self.openid = str(content['result']['openId'])
            self.nick = content['result']['nick']
            return True 
               
    def ws_connect(self, jsondata):
        self.ws.send(json.dumps(jsondata))
        return self.ws.recv()
    
    
    def user_info(self, openid):
        user_info = self.ws_connect({"lwp": "/r/Adaptor/UserMixI/getUserProfileExtensionByUid",
                              "headers": {"mid": self.mid()}, "body": [openid, None]})
        return json.loads(user_info)
    
    def initial(self):
            headers = {
                'accept': '*/*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'zh-CN,zh;q=0.9',
                'referer': self.ding_server_url,
                'sec-fetch-dest': 'script',
                'sec-fetch-mode': 'no-cors',
                'sec-fetch-site': 'same-site',
                'user-agent': self.server_user_agent
            }
            
            did = self.res.get('https://webalfa-cm10.dingtalk.com/setCookie?code={}&appkey={}&isSession=true&callback=__jp0'.format(
                self.tmp_code,self.app_key), headers=headers).headers['set-cookie']
            did = did.split('; ')[0].split('=')[1]
            reg = {"lwp": "/reg", "headers": {"cache-header": "token app-key did ua vhost wv", "vhost": "WK",
                                            "ua": self.server_user_agent, "app-key": self.app_key, "wv": "im:3,au:3,sy:4", "mid": "61880001 0"}, "body": None}
           
            sid = json.loads(self.ws_connect(reg))['headers']['sid']

            ws_data = {
                "lwp": "/subscribe",
                "headers":
                {
                    "token": self.access_token,
                    "sync": "0,0;0;0;",
                    "set-ver": "191175777171",
                    "mid": self.mid(),
                    "ua": self.server_user_agent,
                    "sid": sid,
                    "did": did,
                    'appkey': self.app_key
                }
            }
            self.ws_connect(ws_data)
            
            self.ws_connect({"lwp": "/r/IDLConversation/listNewest",
                            "headers": {"mid": self.mid()}, "body": [1000]})
            
            getState = json.loads(self.ws_connect({"lwp": "/r/Sync/getState", "headers": {"mid": self.mid()}, "body": [{"pts": 0, "highPts": 0, "seq": 0, "timestamp": 0, "tooLong2Tag": ""}]}))
            return True
            
        
    def conversation(self):
        list_newest_conversation = self.ws_connect(self.ws_connect({
            "lwp": "/r/IDLConversation/listNewest", 
            "headers": {
                "mid": self.mid()
                }, 
            "body": [1000]
            }
        ))
        
        list_newest_conversation_data = json.loads(list_newest_conversation)
        if "code" not in list_newest_conversation_data or  list_newest_conversation_data['code'] != 200:
            print(list_newest_conversation_data['reason']) if "reason" in list_newest_conversation_data else print("登陆出现异常")
            return False

        all_data = list_newest_conversation_data['body']
        data = {}
        for v in all_data:
            title = v['baseConversation']['title']
            ### 去掉群号名称为空的群组或者消息体
            if title.strip() == '':
                continue
            data[title]=v['baseConversation']['conversationId']
        return data
    
    def new_message(self, conv_id, wait_time=2):
        message_list = []
        list_message = self.ws_connect({
            "lwp": "/r/IDLMessage/listMessages", 
            "headers": {
                "mid": self.mid()
                }, 
            "body": [conv_id, False, int(time.time()*1000), 14]
            })
        body_data = json.loads(list_message)['body']
       
        for v in body_data:
            if "baseMessage" in v:
                
                if "textContent" in v['baseMessage']['content']:
                    message = ("文字消息：" + v['baseMessage']['content']['textContent']['text'], v['baseMessage']['createdAt'], v['baseMessage']['openIdEx']['openId'])

                elif "attachments" in v['baseMessage']['content']:
                    
                    if "extension" in v['baseMessage']['content']["attachments"][-1] and 'replyContent' in v['baseMessage']['content']["attachments"][-1]['extension']:
                        message = ("引用消息：" + v['baseMessage']['content']['attachments'][-1]['extension'].get('replyContent', ''), v['baseMessage']['createdAt'], v['baseMessage']['openIdEx']['openId'])
                    else:
                        message = ("分享消息：" + v['baseMessage']['content']['attachments'][-1]['extension'].get("title", "") + " url: " + v['baseMessage']['content']['attachments'][-1]['extension'].get("source_url", ""), v['baseMessage']['createdAt'], v['baseMessage']['openIdEx']['openId'])
                else:
                    if "picBytes" in v['baseMessage']['content']["photoContent"]:
                        message = ("图片消息：" + v['baseMessage']['content']["photoContent"].get('picBytes',''), v['baseMessage']['createdAt'], v['baseMessage']['openIdEx']['openId'])
                    else:
                        message = ("图片表情：" + v['baseMessage']['content']["photoContent"]['extension'].get('e_id','') +" "+ v['baseMessage']['content']["photoContent"]['mediaId'], v['baseMessage']['createdAt'], v['baseMessage']['openIdEx']['openId'])
            else:
                continue
            
            session = db_session()
            new_message = DingModel(message_id=message[2],message=message[0],current_time=message[1])
            try:
                session.add(new_message)
                session.commit()
            except:
                pass
                
            if  message not in message_list:
                message_list.append(message)
                
        time.sleep(wait_time)
        message_list.reverse()
        return message_list
    
    
    def send_message(self, conv_id, text):
        self.ws_connect({
            "lwp": "/r/IDLSend/send", 
            "headers": {"mid": self.mid()}, 
            "body": [{
                "uuid": str(int(time.time()*1000000)), 
                "conversationId": conv_id, 
                "type": 1, 
                "creatorType": 1, 
                "content": {
                    "contentType": 1, 
                    "textContent": {
                        "text": text
                        }, 
                    "atOpenIds": {}
                    }, 
                "nickName": self.nick
                }]
            })
        return True
        
    def run(self):
        self.generate_login_qrcode()
        self.check_login_status()
        self.initial()
        
if __name__ == "__main__":
    ding = Ding()
    ding.run()
    cid_dict = ding.conversation()
    cid = cid_dict['测试群号']
    current_time = int(time.time()*1000)
    message_list = []
    while True:
        data = ding.new_message(cid)
        if len(data) == 0:
            continue
        if message_list == data:
            # print("没有新消息")
            continue
        for v in data:
            if v[1] <= current_time:
                # print("旧消息丢弃",v, current_time)
                continue
            print("收到新消息", v , current_time)
            if re.match("关键词", v[0].replace("\n", "")):
                # print("消息指令是: %s" % v[0])
                continue
                time.sleep(2)
        current_time = data[-1][1]
        message_list = data