from websocket import create_connection
from steem import Steem
import threading
import steem
import time
import random
import math
import socket
import sys
from memo_saving import interpret
from memo_saving import main
import operator
import copy
# Fix imports

import reward_system

import json

class Main():
    def __init__(self):
        self.posts = {}  #{ratio:[post_link, ad_token]} account memos also have add_time:int to know when to delete
        self.time_out = 86400 * 3 #(three days) # seconds until an account is removed and it is assumed there will be no duplication after this time
        self.locks = {"posts":threading.Lock()}
        self.main_account = "co-in"
        self.memo_account = "comedy-central"
        self.account_memo_account = "co-in-memo"
        self.active_key = ""
        self.node = "wss://steemd.minnowsupportproject.org"

        self.post_time_period = 60 * 10 * 3 # posts an updated trending every 30 min
        self.TCP_IP = '127.0.0.1'
        self.BUFFER_SIZE = 1024
        self.TCP_PORT = 11001

        thread = threading.Thread(target=self.post_loop)
        thread.daemon = True
        thread.start()


        thread2 = threading.Thread(target=self.trending_loop)
        thread2.daemon = True
        thread2.start()

        self.communication_loop()



    def trending_loop(self):
        while True:
            try:
                print("trending start")

                self.create_trending()
            except Exception as e:
                print("err 4")
                print(e)
                pass
            time.sleep(self.post_time_period)

    def communication_loop(self):
        # waits for internal socket connections (from celery in the flask_app sections)
        # takes the json sent, and then makes a new thread to process it
        # also processes jsons sent to get status data of tasks, which is blocking
        TCP_IP = self.TCP_IP
        TCP_PORT = self.TCP_PORT
        BUFFER_SIZE = self.BUFFER_SIZE
        while True:
            try:
                num = 1
                # creates re-usable socket and listens until connection is made.
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((TCP_IP, TCP_PORT))
                s.listen(0)
                print("LISTING")
                while True:
                    num += 1
                    conn, addr = s.accept()
                    data = ""

                    if addr[0] == TCP_IP:
                        try:
                            # gives id for retrieval of status for tasks

                            id_num = random.randrange(1000000000000000000000000)

                            while True:
                                new_data = conn.recv(BUFFER_SIZE)
                                if not new_data: break
                                if not len(new_data) > 0: break
                                data += new_data.decode()
                                if not len(new_data) >= BUFFER_SIZE: break

                            try:
                                new_list = []
                                sent = False


                                if True:
                                    thread = threading.Thread(target=self.read_json, args=([data]))
                                    thread.daemon = True
                                    thread.start()
                                    #conn.send(json.dumps({"idnum": id_num}).encode())

                            except Exception as e:
                                print("err 4")
                                print(e)
                                conn.send(json.dumps({"success": False, "error": -1}).encode())

                        except Exception as e:
                            print("err 3")
                            print(e)
                            pass

                        conn.close()


                        # creates thread to do stuff with inputs


            except Exception as e:
                print("err 2")
                print(e)
                pass

    def post_loop(self):
        while True:
            try:
                del_list = []
                time.sleep(30)
                with self.locks["posts"]:
                    for i in self.posts:
                        print(i, self.posts[i], (self.posts[i][2] + self.time_out) - time.time())


                        if self.posts[i][2] + self.time_out < time.time():
                            del_list.append(i)
                    for i in del_list:
                        del self.accounts[i]

            except Exception as e:
                print("err 1")
                print(e)

    def read_json(self, info):
        print(info)
        info = json.loads(info)

        account = info["post_link"].split("/")[4].split("@")[1]

        account = interpret.get_account_info(account,self.active_key,self.main_account,self.account_memo_account,self.node)

        print(type(account), type(info))
        print(account )
        with self.locks["posts"]:
            if account != None:
                account = account[2]

                self.posts[info["ratio"]] = [info["post_link"],account["ad-token-perm"], time.time()]

            else:
                self.posts[info["ratio"]] = [info["post_link"],0]

        pass

    def create_trending(self):

        trending_list = []
        with self.locks["posts"]:
            for i in self.posts:
                trending_list.append([i *(1 + self.posts[i][1]/100),self.posts[i][0]])
        trending_list.sort(key=operator.itemgetter(0), reverse=True)
        print(trending_list)

        self.publish_trending(trending_list)

    def publish_trending(self, trending_post_list):
        print("PUBLISH TRENDING")
        print(len(trending_post_list))
        trending_json_list = []

        trending_list = {"number":0,"type":"trending","time":round(time.time(),2), "posts":[]}

        while True:
            print("WHILE TRUE")
            print(trending_list)
            print(trending_post_list)
            if len(trending_post_list) == 0:
                trending_json_list.append(json.dumps(trending_list))


                break
            trending_post = trending_post_list.pop(0)
            print("TRENDING POST")
            print(trending_post)
            copy_list = copy.deepcopy(trending_list)
            print(trending_list)
            if len(json.dumps(copy_list["posts"].append(trending_post))) > 1950:

                trending_json_list.append(json.dumps(trending_list))

                trending_list = {"type": "trending","number":trending_list[0]["number"] + 1, "time": round(time.time(), 2), "posts":[]}

            else:
                print("splitting post")
                trending_list["posts"].append([trending_post[0],trending_post[1].split("@")[1]])
            print("END WHILE TRUE")
        for i in trending_json_list:
            print("SAVE MEMO")

            main.save_memo(json.loads(i), self.memo_account, self.main_account, self.active_key, node =self.node)



main = Main()