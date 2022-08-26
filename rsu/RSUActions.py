
# from MyWallet import MyWallet
from RSUTest import RSUTest

import os
import logging
import socket
import json
import asyncio
import random
import string

import datetime

#RSU_IP = "192.168.12.1"
RSU_IP = "192.168.12.115"
RSU_PORT = 5555 # random server port

from indy import pool, ledger, wallet, did, crypto
from indy.error import IndyError, ErrorCode

from iota import Iota

class RSUActions:
    """ This class comprises all RSU actions """
    
    def __init__(self, myWallet, myIota):
        """ 
        
        :param myWallet : Wallet 
        """

        self.myWallet = myWallet
        self.myIota = myIota
        self.__stop_listening = False
        self.clients_list = []
        self.conn = ""
        self.start_connections()
              
    def start_connections(self):
        self.start_listening()
        
    def stop_connections(self):
        """ 
        Makes the RSU to stop listening to more conenctions.
        """

        self.print_log("DEBUG", "RSU is going to stop listening...")
        self.__stop_listening = True
        
    def start_listening(self):
        """ 
        Initiates the RSU socket, binds it to an address.
        """

        self.ip = RSU_IP
        self.port = RSU_PORT
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverAddress = (self.ip, self.port)

        self.print_log("DEBUG", "RSU is trying to listening on {0}:{1}".format(self.ip, self.port))

        self.socket.bind(serverAddress)
        self.socket.listen(20)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self.socket.setblocking(False)

        self.loop()

    def loop(self):
        """
        Listens to new and old connections in loop. Proceeds according.
        """

        new_connection = False
        
        while True:
            if self.__stop_listening:
                self.print_log("WARNING", "RSU is not listening.")
                return None
            else:
                self.print_log("DEBUG", "RSU is listening! \n")
                try:
                    
                    raw_data = self.conn.recv(4096)

                    if(len(raw_data) == 0):
                        self.print_log("OK", "OBU closed connection!")
                        # TODO: retrieve this client from list of clients and close connection
                        pass
                    new_connection = False
                    raw_data = raw_data[raw_data.index(b'{'):]
                    data = raw_data.decode("utf-8")
                    message_received = json.loads(data)
                    
                except:
                    self.conn, addr = self.socket.accept()
                    self.print_log("DEBUG", "New connection")
                    new_connection = True
                    raw_data = self.conn.recv(4096)
                    if(raw_data == b''):
                        print_log("WARNING", "Received 0 bytes, the connection has been broken.")
                    raw_data = raw_data[raw_data.index(b'{'):]
                    data = raw_data.decode("utf-8")
                    message_received = json.loads(data)
                    
                    self.print_log("DEBUG", ("Received {} from {} \n").format(message_received, self.conn))

                if raw_data:
                    print("Received new raw_data")
                    if new_connection:
                        if message_received["type"] == "connectionRequest":
                            create = False
                            if message_received["did_client"] not in self.clients_list:
                                self.clients_list.append({message_received["nonce_client"] : message_received["did_client"]})
                                loop2 = asyncio.new_event_loop()
                                openWallet_task = loop2.create_task(self.myWallet.create_new_context_keys())
                                loop2.run_until_complete(openWallet_task)
                                loop2.close()
                                create = True
                            else:
                                print_log("WARNING", "There is already a connection with this client. ")
                                ## TODO: tell client there is already a connection established; re-send message?
                            if create:
                                self.create_send_connection_response(message_received, message_received["client_verkey"], self.conn)
                    
                    else:    
                        if message_received["type"] == "proofRequest":
                            to_decrypt = message_received["info"].encode("utf-8")
                            # proof_request_info = self.decrypt_message(to_decrypt)
                            self.print_log("DEBUG", "Deciphering proof request")
                            proof_request_info_bytes = self.__asym_decrypt_message(to_decrypt)
                            data = proof_request_info_bytes.decode("utf-8")
                            proof_request_info = json.loads(data)
                            proof_request_info_message = json.loads(proof_request_info["message"])
                            
                            self.create_send_proof_response(proof_request_info_message["client_verkey"], self.conn, proof_request_info_message["proofReq"])
                            # self.create_send_proof_response(proof_request_info_message["client_verkey"], self.conn)

                            #self.create_send_proof_request(proof_request_info_message["client_verkey"], proof_request_info_message["nonce_client"], self.conn)

                        elif message_received["type"] == "proofResponse":
                            to_decrypt = message_received["info"].encode("utf-8")
                            self.print_log("DEBUG", "Deciphering proof response")
                            proof_response_info_bytes = self.__asym_decrypt_message(to_decrypt)
                            data = proof_response_info_bytes.decode("utf-8")
                            proof_response_info = json.loads(data)
                            self.print_log("OK", str(proof_response_info))
                            proof_response_info_message = json.loads(proof_response_info["message"])
                            self.print_log("OK", str(proof_response_info_message))
                            self.create_send_payment_request(proof_response_info_message["client_licensePlate"], proof_response_info_message["client_id"], int(proof_response_info_message["client_class"]), proof_response_info["sender_verkey"], self.conn)
                            self.print_log("DEBUG", "Payment request sent. Closing connection!")
                            # TODO: retrieve this client from list of clients and close connection
                            self.conn.close()
                        elif message_received["type"] == "something":
                            self.print_log("ERROR", "THIS WAS WHAT WAS MISSING")
                            self.create_send_proof_request(proof_request_info_message["client_verkey"], proof_request_info_message["nonce_client"], self.conn)
                        else:
                            self.print_log("WARNING", "Message error.")


    def create_send_payment_request(self, client_LP, client_ID, client_CL, client_verkey, conn):
        """
        Determines the payment value, creates and encrypts payment request.

        :param: client_LP - client license plate in str
        :param: client_ID - client identification in str
        :param: client_CL - client's car class
        :param: client_verkey - verkey of the client
        :param: conn - active socket connection with the client
        """
        self.print_log("DEBUG", "Creating payment request")

        iota_address = self.myIota.get_address()
        
        amount = 1
        if client_CL == 1:
            amount = 0.9
        elif client_CL == 2:
            amount = 1.6
        elif client_CL == 3:
            amount = 2
        elif client_CL == 4:
            amount = 2.25
        elif client_CL >= 5:
            amount = 0.63

        s = datetime.datetime.now()
        current_time = s.strftime('%d-%m-%Y %H:%M:%S')
        
        payment_info = {"amount" : str(amount), "iota_address" : str(iota_address), "ct": str(current_time)}
        self.print_log("OK", str(payment_info))
        encrypted_request = self.__asym_encrypt_message(str(payment_info), [client_verkey])
        self.__send_response("paymentRequest", encrypted_request, conn)

    def create_send_proof_request(self, client_verkey, nonce_client, conn):
        self.print_log("DEBUG", "Creating proof request")
        request = {"nonce_client": nonce_client}
        encrypted_request = self.__asym_encrypt_message(str(request), [client_verkey])
        self.__send_response("proofRequest", encrypted_request, conn)


    def create_send_proof_response(self, client_verkey, conn, proof_request_from_client):
        """
        Creates and encrypts proof request.

        :param: client_verkey - verkey of the client in str
        :param: conn - active socket connection with the client
        """
        self.print_log("DEBUG", "Creating proof response")
        #proof_request_from_client = proof_request_from_client.replace("\"", "'")

        # self.myWallet.prover_seacrh_credentials(proof_req_from_client)

        self.print_log("ERROR", str(proof_request_from_client))

        loop2 = asyncio.new_event_loop()
        tmp = loop2.create_task(self.myWallet.generate_nonce())
        nonce = loop2.run_until_complete(tmp)
        loop2.close()

        proof_request_from_client = json.dumps({
            'nonce': nonce,
            'name': 'Toll-Application',
            'version': '0.1',
            'requested_attributes': {
                'attr1_referent': {
                    'name': 'name'
                },
                'attr2_referent': {
                    'name': 'status'
                }
            },
            'requested_predicates': {
                'predicate1_referent': {
                    'name': 'id',
                    'p_type': '>=',
                    'p_value': 1
                }
            }
        })
        # tmp = json.loads(proof_request_from_client)
        # tmp2 = json.dumps(proof_request_from_client)
        loop2 = asyncio.new_event_loop()
        prover_search = loop2.create_task(self.myWallet.prover_seacrh_credentials_to_client(proof_request_from_client))
        proof_toll_s = loop2.run_until_complete(prover_search)
        loop2.close()
        print("OK", proof_toll_s)
        encrypted_proof_toll_s = self.__asym_encrypt_message(proof_toll_s, [client_verkey])
        
        proof = {"id": "1234", "certificate": "abcd", "revocation_regestry_id": "0001", "localization": "Aveiro"}
        encrypted_proof = self.__asym_encrypt_message(str(proof), [client_verkey])
        self.__send_response("proofResponse", encrypted_proof_toll_s, conn)


    def __send_response(self, msg_type, response, conn):    
        """
        Adds message type header to message and sends it to the connection.

        :param: msg_type - type of the meesage being send in str
        :param: response - message to be sent in JSON
        :param: conn - active socket connection with the client
        """
        if (msg_type == "connectionResponse"):
            self.print_log("DEBUG", "Sending connection response")
            connection_response = {"type": "connectionResponse", "info": response.decode()}
            conn.send(str(connection_response).encode("utf-8"))
            conn.send(('\n').encode("utf-8"))
        elif(msg_type == "proofResponse"):
            self.print_log("DEBUG", "Sending proof response")
            proof_response = {"type": "proofResponse", "info": response.decode()}
            conn.send(str(proof_response).encode("utf-8"))
            conn.send(('\n').encode("utf-8"))
        elif(msg_type == "proofRequest"):
            self.print_log("DEBUG", "Sending proof request")
            proof_request = {"type": "proofRequest", "info": response.decode()}
            conn.send(str(proof_request).encode("utf-8"))
            conn.send(('\n').encode("utf-8"))
        elif(msg_type == "paymentRequest"):
            self.print_log("DEBUG", "Sending payment response")
            payment_response = {"type": "paymentRequest", "info": response.decode()}
            conn.send(str(payment_response).encode("utf-8"))
            conn.send(('\n').encode("utf-8"))

                
    def create_send_connection_response(self, message_received, client_verkey, conn):
        """
        Creates and encrypts new connection response.

        :param: message_received - message received from client in JSON 
        :param: client_verkey - verkey of the client in str
        :param: conn - active socket connection with client
        """
        self.print_log("DEBUG", "Creating connection response")
        self.myDid = self.myWallet.rsu['did']
        # self.print_log("ERROR", self.myDid)
        self.myVerkey = self.myWallet.rsu['key']
        response = {"did_rsu": self.myDid, "verkey_rsu": self.myVerkey, "nonce_client": message_received["nonce_client"]}
        encrypted_response = self.__asym_encrypt_message(str(response), [client_verkey])
        
        self.__send_response("connectionResponse", encrypted_response, conn)

    def __asym_encrypt_message(self, response, client_verkey):
        """
        Creates loop invocation of async Crypto.pack_message method. 

        :param: response - message to be encrypted in str
        :param: client_verkey - client's verkey
        :return: res - encrypted message
        """
        loop3 = asyncio.new_event_loop()
        auth_encrypt_response = loop3.create_task(self.myWallet.encrypt_message(response, client_verkey))
        res = loop3.run_until_complete(auth_encrypt_response)
        loop3.close()
        return res    

    def __asym_decrypt_message(self, response):
        """
        Creates loop invocation of async Crypto.unpack_message method.

        :param: response - message to be decrypted in bytes
        :return: res - decrypted message
        """
        loop4 = asyncio.new_event_loop()
        auth_decrypt_response = loop4.create_task(self.myWallet.decrypt_message(response))
        res = loop4.run_until_complete(auth_decrypt_response)
        loop4.close()
        return res     

    def decrypt_message(self, response):
        """
        Creates loop invocation of async Crypto.auth_decrypt method.

        :param: response - message to be decrypted in bytes
        :return: res - decrypted message
        """
        loop4 = asyncio.new_event_loop()
        auth_decrypt_response = loop4.create_task(self.myWallet.decrypt2_message(response))
        res = loop4.run_until_complete(auth_decrypt_response)
        loop4.close()
        print(res)
        return res   

    def generate_nonce(self):
        """
        Generates random value with integers and upper and lower cases letters.

        :return: nonce 
        """
        nonce = ''.join(random.choices(string.ascii_letters + string.digits, k = 100))
        return nonce

    def print_log(self, type="DEBUG", value_color="", value_noncolor=""):
        """ 
        Set the colors for print.
        """
        HEADER = '\033[92m'
        ENDC = '\033[0m'
        if type == "ERROR" :
            HEADER = '\u001B[31m'
        if type == "WARNING" :
            HEADER = '\033[93m'
        if type == "DEBUG" :
            HEADER = '\033[92m'
        if type == "OK" :    
            HEADER = '\033[96m'
        print(HEADER + value_color + ENDC + str(value_noncolor))

if __name__ == "__main__":
    
    rsuActionsInit = RSUActions()
    rsuActionsInit.start_connections()
    
