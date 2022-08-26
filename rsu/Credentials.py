from MyWallet import MyWallet

import os
import socket
import json
import asyncio
import random
import string

RSU_IP = "127.0.0.1"
RSU_PORT = 5556 # random server port

from indy import pool, ledger, wallet, did, crypto
from indy.error import IndyError, ErrorCode

class Credentials:
    """ This class comprises all RSU actions """
    
    def __init__(self, myWallet):

        self.myWallet = myWallet
        self.__stop_listening = False

        loop2 = asyncio.new_event_loop()
        openWallet_task = loop2.create_task(self.myWallet.create_new_context_keys())
        self.myDid, self.myVerkey = loop2.run_until_complete(openWallet_task)
        loop2.close()
        
        print(self.myDid)
        print(self.myVerkey)

        self.connect_back_office()

        

    def connect_back_office(self):

        self.ip = RSU_IP
        self.port = RSU_PORT
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serverAddress = (self.ip, self.port)

        self.print_log("DEBUG", "RSU is trying to listening on {0}:{1}".format(self.ip, self.port))

        self.socket.bind(serverAddress)

        self.loop()
    
    def loop(self):
        
        rawData = ""

        while True:
            if self.__stop_listening:
                self.print_log("WARNING", "Issuer is not listening.")
                return None
            else:
                self.print_log("DEBUG", "Issuer is waiting for RSU connection...")
                self.socket.settimeout(None)
                rawData, address = self.socket.recvfrom(8192)
            
            self.print_log("DEBUG", ("Received {} bytes from {} \n").format(len(rawData), address))
            print(rawData)

            if rawData:
                message_to_send = None
                decodedData = rawData.decode()
                tmp = json.loads(decodedData)
                message = json.loads(tmp)
                print(message)

                #1. get schema id and definition
                #transcript_schema_id = message['schema_id']
                #transcript_cred_def_id = message['cred_def_id']

                #2. create master secret
                #master_secret = self.create_master_secret()
                #print('transcript_cred_def_id')
                #print(transcript_cred_def_id)

                #3. get transcript credential definition from ledger
                #(back_office_transcript_cred_def_id, back_office_transcript_cred_def)  = self.get_credential_definition(transcript_cred_def_id)
                #print('AQUI')
                #print('back_office_transcript_cred_def')
                # print(back_office_transcript_cred_def)
                # print('master_secret')
                # print(master_secret)
                
                # #4. create credential request
                # (transcript_cred_request, transcript_cred_request_metadata) = self.create_credential_request(message, back_office_transcript_cred_def, master_secret)
                # meesage_to_send = self.send_credential_request(transcript_cred_request)
                
                # #5. send credential request
                # if message_to_send != None:
                #     self.socket.sendto(json.dumps(message_to_send).encode(), address)
                #     self.print_log("DEBUG", "Sending credential request to Back Office.")

                #data = message["info"]
                #message_to_send = None

                # if data["type"] == "credential_offer":
                #     meesage_to_send = self.create_credential_request()

  
    
    # def create_credential_request(self, message_received):
    #     transcript_cred_offer_object = json.loads(message_received['transcript_cred_offer'])

    #     transcript_schema_id = transcript_cred_offer_object['schema_id']
    #     transcript_cred_def_id = transcript_cred_offer_object['cred_def_id']
    #     # create loop and call cred def request from my wallet
    #     loop = asyncio.get_event_loop()
    #     task = loop.create_task(self.myWallet.create_cred_request(transcript_cred_def_id))
    #     loop.run_until_complete(task)
    #     loop.close()
    #     loop.stop()


    def create_master_secret(self):
        # master_secret = self.myWallet.create_master_secret()
        loop = asyncio.new_event_loop()
        task = loop.create_task(self.myWallet.create_master_secret())
        master_secret = loop.run_until_complete(task)
        loop.close()
        loop.stop()
        return master_secret

    def get_credential_definition(self, transcript_cred_def_id):
        # (back_office_transcript_cred_def_id, back_office_transcript_cred_def) = self.myWallet.get_credential_def(transcript_cred_def_id)
        loop = asyncio.new_event_loop()
        task = loop.create_task(self.myWallet.get_credential_definition(transcript_cred_def_id))
        (back_office_transcript_cred_def_id, back_office_transcript_cred_def) = loop.run_until_complete(task)
        loop.close()
        loop.stop()
        return (back_office_transcript_cred_def_id, back_office_transcript_cred_def)

    def create_credential_request(self, message, back_office_transcript_cred_def, master_secret):
        # (transcript_cred_request, transcript_cred_request_metadata) = self.myWallet.create_credential_request(message, back_office_transcript_cred_def, master_secret)
        loop = asyncio.new_event_loop()
        task = loop.create_task(self.myWallet.create_credential_request(message, back_office_transcript_cred_def, master_secret))
        (transcript_cred_request, transcript_cred_request_metadata) = loop.run_until_complete(task)
        loop.close()
        loop.stop()
        return (transcript_cred_request, transcript_cred_request_metadata)
    
    def send_credential_request(self, msg):
        do_nothing = True

    
    def print_log(self, type="DEBUG", value_color="", value_noncolor=""):
        """
        Set the colors for prints.
        """
        HEADER = '\033[92m'
        ENDC = '\033[0m'
        if type == "ERROR" :
            HEADER = '\u001B[31m'
        if type == "WARNING" :
            HEADER = '\033[93m'
        if type == "DEBUG" :
            HEADER = '\033[92m'
        print(HEADER + value_color + ENDC + str(value_noncolor))


    