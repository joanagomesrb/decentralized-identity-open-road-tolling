from RSUActions import RSUActions
from MyWallet import MyWallet
from Credentials import Credentials
from MyIota import MyIota
from RSUTest import RSUTest
#from test_indy import test_indy

from struct import unpack

from time import sleep
import logging
import time
import os
import asyncio
import sys
import socket
import json

class RSU:
    
    def __init__(self):
        """
        Initiates RSU wallet, and its actions.
        """

        # self.conn = ""
    
        # self.myWallet = MyWallet()
        # self.print_log("DEBUG" , 'Creating wallet')
        # loop = asyncio.get_event_loop()
        # task = loop.create_task(self.myWallet.create_wallet())
        # loop.run_until_complete(task)
        # loop.close()
        # loop.stop()

        # loop2 = asyncio.new_event_loop()
        # openWallet_task = loop2.create_task(self.myWallet.create_new_context_keys())
        # loop2.run_until_complete(openWallet_task)
        # loop2.close()

        # # self.print_log("DEBUG" , 'Creating Master Secret')
        # # loop2 = asyncio.new_event_loop()
        # # task2 = loop2.create_task(self.myWallet.create_master_secret())
        # # loop2.run_until_complete(task2)
        # # loop2.close()
        # # loop2.stop()

        # self.print_log("DEBUG" , 'Creating pool config')
        # loop2 = asyncio.new_event_loop()
        # task2 = loop2.create_task(self.myWallet.create_pool())
        # loop2.run_until_complete(task2)
        # loop2.close()
        # loop2.stop()

        # self.send_request()

        
        #self.print_log("DEBUG" , 'Create Credential Request')
        #(transcript_cred_request, transcript_cred_request_metadata) = self.myWallet.create_credential_request({"type" : "cred_req"})

        #self.send_request(transcript_cred_request, transcript_cred_request_metadata)

        #self.myIota = MyIota()

        #self.rsu_actions = RSUActions(self.myWallet, self.myIota)


        while True:
            print('\nChoose an option:')
            print("1 - Configure")
            print("2 - Init")
            try:
                print(">> ", end='')
                op = int(input())
            except KeyboardInterrupt:
                print("Press CTRL-C again within 2 seconds to quit")
                time.sleep(2)
                sys.exit(2)
          
            if((op != 1) and (op != 2)):
                    print("Something went wrong! Try again please.") 
            else:
                if op == 1:
                    # Get credentials
                    #self.credentials = self.send_request()
                    self.myWallet = RSUTest()
                elif op == 2:
                    self.myIota = MyIota()
                    # self.rsu_actions = RSUActions(self.myWallet, self.myIota)
                    self.rsu_actions = RSUActions(self.myWallet, self.myIota)

    def myreceive(self):
        MSGLEN = 16777216
        chunks = []
        bytes_recd = 0
        while bytes_recd < MSGLEN:
            chunk = self.sock.recv(min(MSGLEN - bytes_recd, 2048))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return b''.join(chunks)
    
    def send_request(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # server_address = ("localhost", 5556)
        server_address = ("192.168.94.108", 5556)
        self.sock.bind(server_address)
        self.sock.listen(2)
        self.print_log("DEBUG", "RSU is listening! \n")

        listening = True
        self.conn, addr = self.sock.accept()

        HEADERSIZE = 10

        #while listening:
        if self.conn: 
            new_connection = True

            raw_data = ""
            full_msg = '' 
            new_msg = True
            receiving = True
            while receiving:
                msg = self.conn.recv(4096)
                if new_msg:
                    l = int(msg[:HEADERSIZE])
                    new_msg = False

                full_msg += msg.decode("utf-8")
                if len(full_msg)-HEADERSIZE == l:
                    print("received full message")
                    raw_data = full_msg[HEADERSIZE:]
                    #print(full_msg)
                    full_msg = '' 
                    new_msg = True
                    receiving = False
            # msg = self.myreceive()
            # raw_data = self.conn.recv(max(1024, 4096))
            print(raw_data)
            data = raw_data
            # print(data)
            # data = data.replace("'", "\"")
            msg = json.loads(data)
            msg_type = msg["type"]

            if msg_type == "credoffer":
                self.cred_offer = msg["credoffer"]
                self.cred_def = msg["creddef"]
                print(self.cred_offer)

                # tmp = {"type" : "ack"}
                # send = json.dumps(tmp)
                # self.conn.send(send.encode("utf-8"))
                    

                    # raw_data = self.conn.recv(16777216)
                    # data = raw_data.decode("utf-8")
                    # print(data)
                    # msg = json.loads(data)
                    # msg_type = msg["type"]

                    # if msg_type == "creddef":
                    #     self.cred_def = msg["creddef"]
                    #     print(self.creddef)

                # create master secret
                loop3 = asyncio.new_event_loop()
                link_secret_id_task = loop3.create_task(self.myWallet.create_master_secret())
                loop3.run_until_complete(link_secret_id_task)
                loop3.close()

                # get cred def from ledger
                loop5 = asyncio.new_event_loop()
                link_secret_id_task = loop5.create_task(self.myWallet.get_cred_def(self.cred_def))
                (rsu_transcript_cred_def_id, rsu_transcript_cred_def) = loop5.run_until_complete(link_secret_id_task)
                loop5.close()
                
                self.print_log("OK", rsu_transcript_cred_def)

                # create cred req & send it to back-office
                loop4 = asyncio.new_event_loop()
                link_secret_id_task = loop4.create_task(self.myWallet.create_credential_request(self.cred_offer, rsu_transcript_cred_def))
                (cred_req_json) = loop4.run_until_complete(link_secret_id_task)
                loop4.close()

                    
                    # # send ack
                tmp = {"type" : "credreq", "req": str(cred_req_json)}
                send = json.dumps(tmp)
                to_send = f'{len(send):<10}'+send
                self.conn.send(to_send.encode("utf-8"))
                
            else:
                self.print_log("ERROR", "Type message not recognized.")
            



        # raw_data = None

        # self.conn, addr = self.sock.accept()
        # new_connection = True

        # try:
        #     raw_data = self.conn.recv(4096)
        #     data = raw_data.decode("utf-8")
        #     print("ABC")
        #     print(raw_data)
        #     print("DEF")
        #     print(data)
        #     print("GHI")
        #     tmp = json.loads(data)
        #     print(tmp["info"])
        #     print(tmp["type"])
            

        # except:
        #     #self.conn, client_addr = sock.accept()
        #     #self.sock.accept()
        #     new_connection = True

        #     #raw_data = self.conn.recv(4096)
        #     #data = raw_data.decode("utf-8")
            
        #     #print(message_received)

        # while True:
        #     # try:
        #     #     if self.conn:
        #     try:
        #         raw_data = self.conn.recv(4096)
        #         new_connection = False

        #         data = raw_data.decode("utf-8")
        #         message_received = json.loads(data)
        #         #cred_offer_json = json.loads(message_received)
        #         #print(cred_offer_json["schema_id"])
        #     except:
        #         #self.conn, client_addr = sock.accept()
        #         self.sock.accept()
        #         new_connection = True

        #         raw_data = self.conn.recv(4096)
        #         data = raw_data.decode("utf-8")
        #         message_received = json.loads(data)
        #         print("message_received")
        #         print(message_received)

        #     if raw_data:
        #         if new_connection:
        #             if message_received["type"] == "cred_offer":
        #                 tmp = {"type" : "ack"}
        #                 self.conn.send(str(tmp).encode("utf-8"))
                
        #                 # create master secret
        #                 loop3 = asyncio.new_event_loop()
        #                 link_secret_id_task = loop3.create_task(self.myWallet.create_master_secret())
        #                 loop3.run_until_complete(link_secret_id_task)
        #                 loop3.close()

        #                 self.cred_offer = message_received["info"]

        #             elif message_received["type"] == "cred_def":
        #                 #self.conn.send(str(cred_req_json).encode("utf-8"))
        #                 #self.conn.send(('\n').encode("utf-8"))
        #                 self.cred_def = message_received["info"]

        #                 print("rcvd cred_def, creating cred request")


        #                 # get cred def from ledger
        #                 # not needed
        #                 # create cred req & send it to back-office
        #                 loop4 = asyncio.new_event_loop()
        #                 link_secret_id_task = loop4.create_task(self.myWallet.create_credential_request(self.cred_offer, cred_def))
        #                 (cred_req_json, cred_req_metadata_json) = loop4.run_until_complete(link_secret_id_task)
        #                 loop4.close()

                      
        
    def print_log(self, type="DEBUG", value_color="", value_noncolor=""):
        """
        Set the colors for prints.
        """
        HEADER = '\033[92m'
        ENDC = '\033[0m'
        if type == "ERROR" :
            HEADER = '\u001B[31m'
        elif type == "WARNING" :
            HEADER = '\033[93m'
        elif type == "DEBUG" :
            HEADER = '\033[92m'
        elif type == "OK" :    
            HEADER = '\033[96m'
        print(HEADER + value_color + ENDC + str(value_noncolor))

        
        

    def start(self):
        """
        Starts RSU connections.
        """
        self.rsu_actions.start_connections()

    def stop(self):
        """
        Stops RSU connections.
        """
        self.rsu_actions.stop_connections()

if __name__ == "__main__":
    
    try:
        rsuInit = RSU()
        # rsuInit.start()
    except KeyboardInterrupt:
        print("\n")
        try:
            print("Press CTRL-C again within 2 seconds to quit")
            # os.system('sudo kill create_ap')
            time.sleep(2)
            sys.exit(2)
        except KeyboardInterrupt:
            print("CTRL-C pressed twice: Quitting!")
            
