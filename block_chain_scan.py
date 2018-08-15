import requests
import json
import time
import math
import yaml
import websocket
import time
import datetime
from websocket import create_connection
from steem import Steem
import json
import os
from smtplib import SMTP as SMTP
import random
from multiprocessing import Process
import socket


from memo_saving import interpret
from memo_saving import main
sending_account = "co-in"
memo_account = "co-in-memo"
active_key = "5KBKznRHCTT4Un88hHqipyBq9auyoiJoGna4emAWrDB2kYTg3pM"

node_list = ["wss://steemd.minnowsupportproject.org",
             "wss://steemd.privex.io/", "wss://gtg.steem.house:8090/"]
last_block = 24990330


def connect_func(memo):
    print(memo)

    # Takes a memmo for our system and reads it, figuring out what system to send it to
    memo_test = json.loads(memo)
    if memo_test["type"] == "account":
        account_memo(memo)
    elif memo_test["type"] == "post":
        send_post(memo)
    pass

def account_memo(memo):
    # takes an account memo and sends it to the account system for checking
    TCP_IP = '127.0.0.1'
    BUFFER_SIZE = 1024
    TCP_PORT = 11000

    # takes the post_link, ratio, and curation system, and then sends it to flask_app
    trynum = 0
    while trynum < 5:
        try:
            trynum += 1


            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((TCP_IP, TCP_PORT))
            s.send(memo.encode())

            s.close()
            return
        except Exception as e:

            # print("exception in thread1: ",thread_num)
            print(e)
            time.sleep(1)

    pass


def send_post(memo):
    print("sending post")
    TCP_IP = '127.0.0.1'
    BUFFER_SIZE = 1024
    TCP_PORT = 11001

    # takes the post_link, ratio, and curation system, and then sends it to flask_app
    trynum = 0
    while trynum < 5:
        try:
            trynum+=1
            MESSAGE = memo

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((TCP_IP, TCP_PORT))
            s.send(MESSAGE.encode())

            s.close()
            return
        except Exception as e:

            #print("exception in thread1: ",thread_num)
            print(e)
            time.sleep(1)
    pass

def deposit(info,node):

    # Takes a deposit of sbd and adds it in as GP and sends it as a new account memo
    global sending_account, memo_account, active_key
    print(info)
    account_info = interpret.get_account_info(info["from"], active_key, sending_account, memo_account,
                               node)[2]
    print(float(info["amount"].split(" STEEM")[0]))

    interpret.update_account(info["from"], sending_account, memo_account, [["gp",account_info["gp"] + float(info["amount"].split(" STEEM")[0])]],
                             active_key, node)


def check_nodes():
    lowest_node = [1000000000000000000000000000000000000000000000000000000000000]  # lowest_time, node_position]
    second_best = [10000000000000000000000000000000000000000000000000000000000000]
    global node_list
    working_nodes = []
    for i in node_list:
        print(i)

        try:
            start = time.time()
            ws = create_connection(i)

            send = ws.send(json.dumps(
                {"jsonrpc": "2.0", "id": 0, "method": "call", "params": [0, "get_dynamic_global_properties", []]}))

            last_block = json.loads(ws.recv())["result"]["head_block_number"]
            if last_block != 0:
                end = time.time()
                if end - start < lowest_node[0]:
                    lowest_node = [end - start, i]
                elif end - start < second_best[0]:
                    second_best = [end - start, i]
                working_nodes.append(i)
            ws.close()


        except Exception as e:
            print(22222222222222, e, i)
            pass
    working_nodes[0] = lowest_node[1]
    try:
        working_nodes[1] = second_best[1]
    except:
        working_nodes[1] = lowest_node[1]
    print(working_nodes)

    return working_nodes


while True:

    change_last = False
    try:
        last_last_block
    except NameError:
        last_last_block = 0
    try:
        # print("loop")

        try:
            active_nodes

            x = 1 / random.randrange(6000)

        except:
            active_nodes = check_nodes()

        try:
            ws
        except NameError:
            try:

                ws = create_connection(active_nodes[0])

            except:

                active_nodes = check_nodes()
                ws = create_connection(active_nodes[0])
        send = ws.send(json.dumps(
            {"jsonrpc": "2.0", "id": 0, "method": "call", "params": [0, "get_dynamic_global_properties", []]}))
        info = json.loads(ws.recv())["result"]["head_block_number"]
        if last_block == 0 or last_block > info:

            last_block = info
        elif last_block < info:
            last_block += 1
        else:
            time.sleep(3)
        change_last = True

        send = ws.send(
            json.dumps({"jsonrpc": "2.0", "id": 0, "method": "call", "params": [0, "get_block", [last_block]]}))
        res = json.loads(ws.recv())

        # print(last_block, "blocco")


        if res["result"] != None:
            print(str(last_block) + "  " + res["result"]["timestamp"] + "\r", end="")

            if res["result"]["transactions"] != []:
                tx = res["result"]["transactions"]
                for i in tx:

                    # print(i, "11")
                    for o in i["operations"]:
                        txtype = o[0]
                        # print(o, "12")
                        if txtype == "transfer":
                            # print(o[1]["voter"])
                            # weight = o[1]["weight"] / 100 * 70 / 100

                            is_in_list = False
                            o = o[1]
                            if o["from"] == "co-in" and o["to"] == "co-in-memo":


                                p = Process(target=connect_func,
                                            args=([o["memo"]]))
                                p.start()
                            elif o["to"] == "co-in-memo":
                                p = Process(target=deposit,
                                            args=([o,active_nodes[0]]))
                                p.start()
                                pass


    except Exception as e:
        print()
        print("except:", e)

        print("here")
        while True:
            try:
                active_nodes = check_nodes()
                #ws = create_connection(active_nodes[0])
                print("This one")
                break

            except Exception as e:
                print(333333333333333333, e)
                pass

        if change_last:
            last_block -= 1



