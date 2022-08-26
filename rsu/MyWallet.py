
import json
import logging
import asyncio
import tracemalloc
import pprint
import time

from iota import Iota
from iota import ProposedTransaction
from iota import Address
from iota import Tag
from iota import TryteString
from indy import pool, ledger, wallet, did, crypto, anoncreds
from indy.error import IndyError, ErrorCode

from utils import get_pool_genesis_txn_path, run_coroutine, PROTOCOL_VERSION, ensure_previous_request_applied

pool_name = 'pool2'
wallet_config = json.dumps({"id": "wallet"})
wallet_credentials = json.dumps({"key": "wallet_key"})
genesis_file_path = get_pool_genesis_txn_path(pool_name)

WALLET_CONFIG = json.dumps({"id": "wallet"})
WALLET_CREDENTIALS = json.dumps({"key": "wallet_key"})


class MyWallet:

    def __init__(self):
        self.myDid = ""
        self.myVerkey = ""
        self.walletHandle = ""
        self.encrypted_response = ""
        self.pool_handle = ""
        self.master_secret_id = ""

    async def encrypt_message(self, response, client_verkey):
        """ 
        Encrypts message to be sent.

        :param: response - message to be sent in str
        :param: client_verkey - client verkey in array
        :return: encrypted message
        """
        #self.encrypted_response = await crypto.auth_crypt(self.walletHandle, self.myVerkey, client_verkey, response)
        self.encrypted_response = await crypto.pack_message(self.walletHandle, response, client_verkey, self.myVerkey)
        return self.encrypted_response
    
    async def decrypt_message(self, response):
        """ 
        Decrypts message to be sent.

        :param: response - message to be sent in str
        :return: decrypted message
        """
        # decrypted_response = await crypto.auth_decrypt(self.walletHandle, client_verkey, response)
        decrypted_response = await crypto.unpack_message(self.walletHandle, response)
        return decrypted_response

    async def decrypt2_message(self, response):
        """ 
        Decrypts message to be sent (uses deprecated method "auth_decrypt").

        :param: response - message to be sent in str
        :return: decrypted message
        """
        # decrypted_response = await crypto.auth_decrypt(self.walletHandle, client_verkey, response)
        self.print_log("OK", str(response))
        self.print_log("OK", str(isinstance(response, bytes)))
        self.print_log("OK", str(self.walletHandle))
        self.print_log("OK", str(isinstance(self.walletHandle, int)))
        self.print_log("OK", str(self.myVerkey))
        self.print_log("OK", str(isinstance(self.myVerkey, str)))
        decrypted_response = await crypto.auth_decrypt(self.walletHandle, self.myVerkey, response)
        return decrypted_response

    async def create_master_secret(self):
        try:
            self.master_secret_id = await anoncreds.prover_create_master_secret(self.walletHandle, None)
            return self.master_secret_id
        except IndyError as e:
            print('Error occurred: %s' % e)
    
    async def get_cred_def(self, cred_def):
        self.print_log("OK", "Get cred def")

        # cred_offer_json = json.loads(json.dumps(cred_offer))
        #cred_offer_tmp = cred_offer.replace("'", "\"")
        #cred_offer_json =  json.loads(cred_offer_tmp)
        # transcript_cred_def_id = cred_offer_json["cred_def_id"]
        
        #print("ced_def")
        #print(json.loads(cred_def))
        #print(json.dumps(cred_def))
        #print(str(cred_def))
        #print("self.myDid")
        #print(self.myDid)
        #cred_def = cred_def.replace("'", "\"")
        print("cred_def")
        #cred_def_json = json.loads(cred_def)
        print(cred_def)

        get_cred_def_request = await ledger.build_get_cred_def_request(self.myDid, cred_def)
        get_cred_def_response =\
            await ensure_previous_request_applied(self.pool_handle, get_cred_def_request, lambda response: response['result']['data'] is not None)
        return await ledger.parse_get_cred_def_response(get_cred_def_response)

    async def create_credential_request(self, cred_offer, rsu_transcript_cred_def):


        print("create_credential_request")
        # cred_def_id, transcript_cred_def = self.get_credential_definition()
        # tmp = json.dumps(transcript_cred_def)
    
        try:
            #(transcript_cred_request, transcript_cred_request_metadata) = await anoncreds.prover_create_credential_req(self.walletHandle, self.myDid, message, json.dumps(transcript_cred_def), self.master_secret)
            # print("DEBUG", self.walletHandle)
            # print("DEBUG", self.myDid)
            cred_offer_json = cred_offer.replace("'", "\"")
            # cred_def_json = cred_def.replace("'", "\"")
            # # print("OK", cred_offer_json)
            # # print("OK", json.loads(cred_def_json))
            # print("OK", self.master_secret_id)
            cred_offer_tmp = cred_offer.replace("'", "\"")
            cred_offer_json =  json.loads(cred_offer_tmp)

            # self.print_log("ERROR", cred_offer_json)
            cred_def_json = rsu_transcript_cred_def
            self.print_log("ERROR", rsu_transcript_cred_def)
            
            # (transcript_cred_request, transcript_cred_request_metadata) = await anoncreds.prover_create_credential_req(self.walletHandle, self.myDid, json.dumps(cred_offer), rsu_transcript_cred_def, self.master_secret_id)
            (transcript_cred_request, transcript_cred_request_metadata) = await anoncreds.prover_create_credential_req(self.walletHandle, self.myDid, json.dumps(cred_offer_json), rsu_transcript_cred_def, self.master_secret_id)
            # print("DEBUG", transcript_cred_request)
            # print("DEBUG", "transcript_cred_request")
            # print("OK", transcript_cred_request_metadata)
            self.print_log("DECBUG", transcript_cred_request)
            return (transcript_cred_request)
        except IndyError as e:
            print('Error occurred: %s' % e)
        return None
       

    async def get_credential_definition(self, cred_def_id):
        try:
            # get_cred_def_request = await ledger.build_get_cred_def_request(self.myDid, str(cred_def_id))
            get_cred_def_request = await ledger.build_get_cred_def_request(self.myDid, cred_def_id)
            print("get_cred_def_request")
            print(get_cred_def_request)
  
            get_cred_def_response = \
                await ensure_previous_request_applied(self.pool_handle, get_cred_def_request,
                                                  lambda response: response['result']['data'] is not None)
            print("get_cred_def_response")
            print(get_cred_def_response)
        
            credential_def_id, credential_def = await ledger.parse_get_cred_def_response(get_cred_def_response)
            print("credential_def_id")
            print(credential_def_id)
            print("credential_def")
            print(credential_def)
            
            return credential_def_id, credential_def
        except IndyError as e:
            print('Error occurred: %s' % e)
            
        return None, None
        

    async def ensure_previous_request_applied(self, pool_handle, checker_request, checker):
        for _ in range(3):
            response = json.loads(await ledger.submit_request(pool_handle, checker_request))
            try:
                if checker(response):
                    return json.dumps(response)
            except TypeError:
                pass
            time.sleep(5)

    async def create_pool(self):
        try:
            await pool.set_protocol_version(PROTOCOL_VERSION)

            pool_config = json.dumps({'genesis_txn': str(genesis_file_path)})
            
            try:
                await pool.create_pool_ledger_config(config_name=pool_name, config=pool_config)
            except IndyError as ex:
                if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
                    pass
            self.pool_handle = await pool.open_pool_ledger(config_name=pool_name, config=None)

        except IndyError as e:
            print('Error occurred: %s' % e)
            self.print_log("ERROR" , 'Creating pool config failed')

            
    async def create_wallet(self, wallet_config=WALLET_CONFIG, wallet_credentials=WALLET_CREDENTIALS ):
        """
        Creates RSU wallet

        :param: wallet_config - wallet configuration in str
        :param: wallet_credentials - wallet credentials in str
        """
        
        try:
            try:
                await wallet.create_wallet(wallet_config, wallet_credentials)
            except IndyError as ex:
                if ex.error_code == ErrorCode.WalletAlreadyExistsError:
                    pass
            self.walletHandle = await wallet.open_wallet(wallet_config, wallet_credentials)
                        
        except IndyError as e:
            print('Error occurred: %s' % e)
            self.print_log("ERROR" , 'Creating wallet config failed')

    async def create_new_context_keys(self):
        """
        Creates context keys pai: did/verkey pair.

        :return: did/verkey pair
        """
        try:
            self.print_log("DEBUG" , "Opening wallet and creating new did/verkey pair\n")
            self.myDid, self.myVerkey =  await did.create_and_store_my_did(self.walletHandle, "{}")

            return self.myDid, self.myVerkey
        except IndyError as e:
            print('Error occurred: %s' % e)

    
   

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

if __name__ == "__main__":
    
    myWalletInit = MyWallet()
    # loop1 = asyncio.get_event_loop()
    # createWallet_task = loop1.create_task(myWalletInit.createWallet())
    # loop1.run_until_complete(createWallet_task)
    # loop1.close()
    
    # loop2 = asyncio.new_event_loop()
    # openWallet_task = loop2.create_task(myWalletInit.createNewContextKeys())
    # loop2.run_until_complete(openWallet_task)
    # loop2.close()
