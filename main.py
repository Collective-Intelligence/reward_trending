from websocket import create_connection
from steem import Steem
import threading
import steem
import time
import random
import math
import socket
import sys
import socket
from memo_saving import interpret
from memo_saving import main
# Fix imports

import reward_system

import json

class Main():
    def __init__(self):
        self.accounts = {} # {account_name:[account_memo,account_memo2]} account memos also have add_time:int to know when to delete
        self.time_out = 720 # seconds until an account is removed and it is assumed there will be no duplication after this time
        self.locks = {"accounts":threading.Lock()}
        self.main_account = "co-in"
        self.memo_account = "co-in-memo"
        self.active_key = ""
        self.node = "wss://steemd.minnowsupportproject.org"
        self.reward_time_period = 86400 * 12
        self.TCP_IP = '127.0.0.1'
        self.BUFFER_SIZE = 1024
        self.TCP_PORT = 11000
        thread = threading.Thread(target=self.update_rewards)
        thread.daemon = True
        #thread.start()

        thread2 = threading.Thread(target=self.account_loop)
        thread2.daemon = True
        #thread2.start()
        self.communication_loop()
        pass

    def update_rewards(self):
        while True:
            try:
                reward_system.daily_reward_set(self.main_account, self.memo_account,self.active_key, self.reward_time_period, self.node)
            except Exception as e:
                print("err 2")
                print(e)
            time.sleep(86400)

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
                print("STARTING CURATION")
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                print("PORT FOR CURATION",TCP_PORT)
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

    def account_loop(self):
        while True:
            try:
                del_list = []
                time.sleep(10)
                with self.locks["accounts"]:
                    for i in self.accounts:

                        if len(self.accounts[i]) < 1:
                            del_list.append(i)

                        #elif len(self.accounts[i]) > 1:
                         #   self.fix_memo(self.accounts[i])
                        new_list = []
                        for ii in self.accounts[i]:

                            if not ii["added"] + self.time_out < time.time():
                                new_list.append(ii)
                        self.accounts[i] = new_list
                    for i in del_list:
                        del self.accounts[i]

            except Exception as e:
                print("err 1")
                print(e)

    def read_json(self, info):
        print(info)
        info = json.loads(info)
        info["added"] = time.time()
        with self.locks["accounts"]:
            try:
                self.accounts[info["account"]].append(info)
                print("no key error")
                self.fix_memo(self.accounts[info["account"]])
            except KeyError:
                print("key error")
                self.accounts[info["account"]] = [info]





    def fix_memo(self,memo_list):

        # takes memos and checks if any overwrote the changes of the other
        # this can happen if the memos come at intervals that are too close together
        print("FIXING MEMOs")
        print(memo_list)
        highest_version = -1
        same_version = False
        memos_to_fix = []
        for i in memo_list:
            print(i["version"], i )
            if i["version"] == highest_version:

                print("SAME VERSION")
                same_version = True
                memos_to_fix.append(i)
            elif i["version"] > highest_version:
                highest_version = i["version"]
                memos_to_fix = [i]

        if not same_version:
            print("RETURNING")
            return






        changes = []
        og_memo_num = 0
        for i in memos_to_fix:
            for ii in i["changes"]:
                append_to = True
                for iii in changes:
                    if iii[0] == ii[0] and iii[1] == ii[1]:
                        append_to = False

                if append_to:
                    changes.append(ii)
        print("CHANGES")
        print(changes)

        if len(changes) < 2 or len(changes) == len(memos_to_fix[0]["changes"]):
            print("returning before memo")
            return
        try:

            oldest = 0
            for i in memos_to_fix:
                if i["old"] > oldest:
                    oldest = i["old"]
        except Exception as e:
            print(e)

        memo = json.loads(main.retrieve(account=self.main_account,sent_to= self.memo_account, position=oldest, node=self.node)[0][2])
        print("MEMO")
        print(memo)
        for i in memo:
            rel_changes = []
            for ii in changes:
                if i == ii[0]:
                    rel_changes.append(ii)
                    print("REL CHANGES APPEND")
            if len(rel_changes) > 1:
                if rel_changes[0][0] == "vote":
                    for c in rel_changes:
                        memo["vote"].append(c[1])
                elif rel_changes[0][0] == "groups":
                    pass
                elif rel_changes[0][0] == "vote-link":
                    for c in rel_changes:
                        memo["vote-link"].append(c[1])
                else:
                    for c in rel_changes:
                        memo[c[0]] += memo[c[0]] - c[1]
            elif len(rel_changes) < 1:
                pass
            else:
                memo[rel_changes[0][0]] = rel_changes[0][1]
        memo["version"] = highest_version + 1
        print(memo)

        memo["changes"] = changes
        main.save_memo(memo,self.memo_account,self.main_account,self.active_key,node=self.node)


main_ = Main()

