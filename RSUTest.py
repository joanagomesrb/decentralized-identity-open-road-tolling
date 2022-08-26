
import time

from indy import anoncreds, did, ledger, pool, wallet, blob_storage

import json
import logging
import socket
import asyncio

import argparse
import sys
from ctypes import *
from os.path import dirname

from indy.error import ErrorCode, IndyError

from utils import get_pool_genesis_txn_path, run_coroutine, PROTOCOL_VERSION, ensure_previous_request_applied

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser(description='Run python getting-started scenario (Alice/Faber)')
parser.add_argument('-t', '--storage_type', help='load custom wallet storage plug-in')
parser.add_argument('-l', '--library', help='dynamic library to load for plug-in')
parser.add_argument('-e', '--entrypoint', help='entry point for dynamic library')
parser.add_argument('-c', '--config', help='entry point for dynamic library')
parser.add_argument('-s', '--creds', help='entry point for dynamic library')


args = parser.parse_args()

class RSUTest:

    def __init__(self):
        self.setup()
        self.listening_to_transcript_cred_offer()

    def setup(self):
        # create and open pool
        self.pool_ = {
            'name': 'pool2'
        }
        loop2 = asyncio.new_event_loop()
        task2 = loop2.create_task(self.create_pool())
        loop2.run_until_complete(task2)
        loop2.close()
        loop2.stop()
        # create wallet
        self.rsu = {
            'name': 'Rsu',
            'wallet_config': json.dumps({'id': 'rsu_wallet'}),
            'wallet_credentials': json.dumps({'key': 'rsu_wallet_key'}),
            'pool': self.pool_['handle'],
        }
        loop = asyncio.get_event_loop()
        task = loop.create_task(self.create_wallet(self.rsu))
        loop.run_until_complete(task)
        loop.close()
        loop.stop()
        # create keys
        loop2 = asyncio.new_event_loop()
        openWallet_task = loop2.create_task(self.create_new_context_keys())
        loop2.run_until_complete(openWallet_task)
        loop2.close()
        # create master secret
        loop2 = asyncio.new_event_loop()
        openWallet_task = loop2.create_task(self.create_master_secret())
        loop2.run_until_complete(openWallet_task)
        loop2.close()
    
    async def create_pool(self):
        logger.info("Open Pool Ledger: {}".format(self.pool_['name']))
        self.pool_['genesis_txn_path'] = get_pool_genesis_txn_path(self.pool_['name'])
        self.pool_['config'] = json.dumps({"genesis_txn": str(self.pool_['genesis_txn_path'])})

        # Set protocol version 2 to work with Indy Node 1.4
        await pool.set_protocol_version(PROTOCOL_VERSION)

        try:
            await pool.create_pool_ledger_config(self.pool_['name'], self.pool_['config'])
        except IndyError as ex:
            if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
                pass
        self.pool_['handle'] = await pool.open_pool_ledger(self.pool_['name'], None)
    
    async def create_wallet(self, identity):
        logger.info("\"{}\" -> Create wallet".format(identity['name']))
        try:
            await wallet.create_wallet(self.wallet_config("create", identity['wallet_config']),
                                    self.wallet_credentials("create", identity['wallet_credentials']))
        except IndyError as ex:
            if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
                pass
        identity['wallet'] = await wallet.open_wallet(self.wallet_config("open", identity['wallet_config']),
                                                    self.wallet_credentials("open", identity['wallet_credentials']))

    def wallet_config(self, operation, wallet_config_str):
        if not args.storage_type:
            return wallet_config_str
        wallet_config_json = json.loads(wallet_config_str)
        wallet_config_json['storage_type'] = args.storage_type
        if args.config:
            wallet_config_json['storage_config'] = json.loads(args.config)
        # print(operation, json.dumps(wallet_config_json))
        return json.dumps(wallet_config_json)
    
    def wallet_credentials(self, operation, wallet_credentials_str):
        if not args.storage_type:
            return wallet_credentials_str
        wallet_credentials_json = json.loads(wallet_credentials_str)
        if args.creds:
            wallet_credentials_json['storage_credentials'] = json.loads(args.creds)
        # print(operation, json.dumps(wallet_credentials_json))
        return json.dumps(wallet_credentials_json)
    
    async def create_new_context_keys(self):
        """
        Creates context keys pai: did/verkey pair.

        :return: did/verkey pair
        """
        try:
            (self.rsu['did'], self.rsu['key']) =  await did.create_and_store_my_did(self.rsu['wallet'], "{}")
            print("self.rsu['did']")
            print(self.rsu['did'])
            print("self.rsu['key']")
            print(self.rsu['key'])
            return (self.rsu['did'], self.rsu['key'])
        except IndyError as e:
            print('Error occurred: %s' % e)
    
    async def create_master_secret(self):
        try:
            self.rsu['master_secret_id'] = await anoncreds.prover_create_master_secret(self.rsu['wallet'], None)
            return self.rsu['master_secret_id']
        except IndyError as e:
            print('Error occurred: %s' % e)

    def listening_to_transcript_cred_offer(self):
        RSU_IP = "192.168.94.108"
        RSU_PORT = 5558
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            print("received raw data from the back office")
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            serverAddress = (RSU_IP, RSU_PORT)
            s.bind(serverAddress)
            s.listen(2)
            listening = True
            new_connection = True
            while listening:
                print("listening")
                conn, addr = s.accept()
                if new_connection:
                    new_connection = False
                    with conn:
                        full_msg = ""
                        raw_data = ""
                        HEADERSIZE = 10
                        new_msg = True
                        receiving = True
                        while receiving:
                            msg = conn.recv(8192)
                            if new_msg:
                                l = int(msg[:10])
                                new_msg = False

                            full_msg += msg.decode("utf-8")
                            print(len(full_msg))
                            if len(full_msg)-HEADERSIZE == l:
                                print("received full message")
                                raw_data = full_msg[HEADERSIZE:]
                                full_msg = '' 
                                new_msg = True
                                receiving = False
                        # data = raw_data.decode("utf-8")
                        self.rsu['transcript_cred_offer'] = raw_data
                        transcript_cred_offer_object = json.loads(raw_data)
                        print("CHECK IF SCHEMA ID IS CORRECT")
                        print(transcript_cred_offer_object)
                        self.rsu['transcript_schema_id'] = transcript_cred_offer_object['schema_id']
                        self.rsu['transcript_cred_def_id'] = transcript_cred_offer_object['cred_def_id']
                        loop2 = asyncio.new_event_loop()
                        openWallet_task = loop2.create_task(self.create_credential_request())
                        (self.rsu['transcript_cred_request'], self.rsu['transcript_cred_request_metadata']) = loop2.run_until_complete(openWallet_task)
                        loop2.close()

                        msg2 = {"cred_req": self.rsu['transcript_cred_request'], "cred_req_metadata": self.rsu['transcript_cred_request_metadata']}
                        msgs = json.dumps(msg2)
                        HEADERSIZE = 10
                        i = len(msgs)
                        msg_to_send1 = f'{i:<{HEADERSIZE}}' + (msgs)
                        conn.send(msg_to_send1.encode("utf-8"))
                        print("SENDING... transcript cred req")

                else:
                    with conn:
                        # raw_data2 = conn.recv(8192)
                        print("received new message from same conenction")
                        # print(raw_data2)
                        # print(len(raw_data2))

                        # datas = raw_data2.decode("utf-8")
                        # print(datas)
                        full_msg = ""
                        raw_data2 = ""
                        HEADERSIZE = 10
                        new_msg = True
                        receiving = True
                        while receiving:
                            msg2 = conn.recv(4096)
                            if new_msg:
                                l = int(msg2[:10])
                                new_msg = False

                            full_msg += msg2.decode("utf-8")
                            if len(full_msg)-HEADERSIZE == l:
                                print("received full message")
                                raw_data2 = full_msg[HEADERSIZE:]
                                full_msg = '' 
                                new_msg = True
                                receiving = False

                        dataj = json.loads(raw_data2)
                        print("RECIVED dataj")
                        print(dataj)
                        if(dataj["type"] == "transcript_cred"):
                            print("RECIVED 2nd message")
                            print(dataj)
                            self.rsu['transcript_cred'] = dataj["transcript"]
                            loop2 = asyncio.new_event_loop()
                            openWallet_task = loop2.create_task(self.get_cred_from_ledger())
                            loop2.run_until_complete(openWallet_task)
                            loop2.close()
                        elif(dataj["type"] == "toll_application_proof_req"):
                            print("RECIVED 3rd message")
                            print(dataj)
                            # self.rsu['toll_application_proof_request'] = json.loads(dataj["proof_req"])
                            self.rsu['toll_application_proof_request'] = dataj["proof_req"]
                            print(self.rsu['toll_application_proof_request'])
                            loop2 = asyncio.new_event_loop()
                            openWallet_task = loop2.create_task(self.prover_seacrh_credentials())
                            self.rsu['toll_application_proof'] = loop2.run_until_complete(openWallet_task)
                            loop2.close()

                            HEADERSIZE = 10
                            logger.info("\"RSU\" -> Send \"Toll-Application\" Proof to Toll Company")
                            i = len(self.rsu['toll_application_proof'])
                            msg3 = f'{i:<{HEADERSIZE}}' + (self.rsu['toll_application_proof'])
                             
                            conn.send(msg3.encode("utf-8"))
                            listening = False
            s.close()

                # except Exception:
                #     print("something went wrong. just testing...")
        

    async def prover_seacrh_credentials(self):
        logger.info("\"RSU\" -> Get credentials for \"Toll-Application\" Proof Request")
        search_for_toll_application_proof_request = \
        await anoncreds.prover_search_credentials_for_proof_req(self.rsu['wallet'],
                                                                self.rsu['toll_application_proof_request'], None)

        cred_for_attr1 = await self.get_credential_for_referent(search_for_toll_application_proof_request, 'attr1_referent')
        cred_for_attr2 = await self.get_credential_for_referent(search_for_toll_application_proof_request, 'attr2_referent')
        # cred_for_attr3 = await self.get_credential_for_referent(search_for_toll_application_proof_request, 'attr3_referent')
        # cred_for_attr4 = await get_credential_for_referent(search_for_toll_application_proof_request, 'attr4_referent')
        # cred_for_attr5 = await get_credential_for_referent(search_for_toll_application_proof_request, 'attr5_referent')
        cred_for_predicate1 = \
            await self.get_credential_for_referent(search_for_toll_application_proof_request, 'predicate1_referent')

        await anoncreds.prover_close_credentials_search_for_proof_req(search_for_toll_application_proof_request)

        self.rsu['creds_for_toll_application_proof'] = {cred_for_attr1['referent']: cred_for_attr1,
                                                    cred_for_attr2['referent']: cred_for_attr2,
                                                    cred_for_predicate1['referent']: cred_for_predicate1}

        self.rsu['schemas_for_toll_application'], self.rsu['cred_defs_for_toll_application'], \
        self.rsu['revoc_states_for_toll_application'] = \
            await self.prover_get_entities_from_ledger(self.rsu['pool'], self.rsu['did'],
                                                self.rsu['creds_for_toll_application_proof'], self.rsu['name'])

        logger.info("\"RSU\" -> Create \"Toll-Application\" Proof")
        # 1. attributes values of which will be revealed
        # 2. attributes values of which will be unrevealed
        # 3. attributes for which creating of verifiable proof is not required
        self.rsu['toll_application_requested_creds'] = json.dumps({
            'self_attested_attributes': {
                'attr1_referent': 'rsu'
            },
            'requested_attributes': {
                'attr2_referent': {'cred_id': cred_for_attr2['referent'], 'revealed': True}
            },
            'requested_predicates': {'predicate1_referent': {'cred_id': cred_for_predicate1['referent']}}
        })

        # print("THIIS HERE")
        # print(self.rsu['toll_application_proof_request'])
        # print(self.rsu['toll_application_requested_creds'])
        # print(self.rsu['schemas_for_toll_application'])
        # print(self.rsu['cred_defs_for_toll_application'])
        # print(self.rsu['revoc_states_for_toll_application'])

        self.rsu['toll_application_proof'] = \
            await anoncreds.prover_create_proof(self.rsu['wallet'], self.rsu['toll_application_proof_request'],
                                                self.rsu['toll_application_requested_creds'], self.rsu['master_secret_id'],
                                                self.rsu['schemas_for_toll_application'],
                                                self.rsu['cred_defs_for_toll_application'],
                                                self.rsu['revoc_states_for_toll_application'])

        return self.rsu['toll_application_proof']
    
    

    async def get_credential_for_referent(self, search_handle, referent):
        credentials = json.loads(
            await anoncreds.prover_fetch_credentials_for_proof_req(search_handle, referent, 10))
        return credentials[0]['cred_info']

    async def get_cred_from_ledger(self):
        logger.info("\"RSU\" -> Store \"Transcript\" Credential from Toll Company")
        _, self.rsu['transcript_cred_def'] = await self.get_cred_def(self.rsu['pool'], self.rsu['did'],
                                                            self.rsu['transcript_cred_def_id'])

        await anoncreds.prover_store_credential(self.rsu['wallet'], None, self.rsu['transcript_cred_request_metadata'],
                                                self.rsu['transcript_cred'], self.rsu['transcript_cred_def'], None)

        print("THIS IS THE CREDENTIAL")
        print(self.rsu['transcript_cred_def'])
    
    async def create_credential_request(self):
        logger.info("\"RSU\" -> Get \"Toll Company Transcript\" Credential Definition from Ledger")
        (self.rsu['tollcompany_transcript_cred_def_id'], self.rsu['tollcompany_transcript_cred_def']) = \
            await self.get_cred_def(self.rsu['pool'], self.rsu['did'], self.rsu['transcript_cred_def_id'])

        logger.info("\"RSU\" -> Create \"Transcript\" Credential Request for Toll Company")
        (self.rsu['transcript_cred_request'], self.rsu['transcript_cred_request_metadata']) = \
            await anoncreds.prover_create_credential_req(self.rsu['wallet'], self.rsu['did'],
                                                        self.rsu['transcript_cred_offer'], self.rsu['tollcompany_transcript_cred_def'],
                                                        self.rsu['master_secret_id'])
        return (self.rsu['transcript_cred_request'], self.rsu['transcript_cred_request_metadata'])
        
    async def get_cred_def(self, pool_handle, _did, cred_def_id):
        get_cred_def_request = await ledger.build_get_cred_def_request(_did, cred_def_id)
        get_cred_def_response = \
            await ensure_previous_request_applied(pool_handle, get_cred_def_request,
                                                lambda response: response['result']['data'] is not None)
        return await ledger.parse_get_cred_def_response(get_cred_def_response)
    
    async def prover_get_entities_from_ledger(self, pool_handle, _did, identifiers, actor, timestamp_from=None,
                                          timestamp_to=None):
        schemas = {}
        cred_defs = {}
        rev_states = {}
        print("ITEM")
        print(_did)
        print(identifiers.values())
        for item in identifiers.values():    
            logger.info("\"{}\" -> Get Schema from Ledger".format(actor))
            (received_schema_id, received_schema) = await self.get_schema(pool_handle, _did, item['schema_id'])
            schemas[received_schema_id] = json.loads(received_schema)

            logger.info("\"{}\" -> Get Claim Definition from Ledger".format(actor))
            (received_cred_def_id, received_cred_def) = await self.get_cred_def(pool_handle, _did, item['cred_def_id'])
            cred_defs[received_cred_def_id] = json.loads(received_cred_def)

            if 'rev_reg_id' in item and item['rev_reg_id'] is not None:
                # Create Revocations States
                logger.info("\"{}\" -> Get Revocation Registry Definition from Ledger".format(actor))
                get_revoc_reg_def_request = await ledger.build_get_revoc_reg_def_request(_did, item['rev_reg_id'])

                get_revoc_reg_def_response = \
                    await ensure_previous_request_applied(pool_handle, get_revoc_reg_def_request,
                                                        lambda response: response['result']['data'] is not None)
                (rev_reg_id, revoc_reg_def_json) = await ledger.parse_get_revoc_reg_def_response(get_revoc_reg_def_response)

                logger.info("\"{}\" -> Get Revocation Registry Delta from Ledger".format(actor))
                if not timestamp_to: timestamp_to = int(time.time())
                get_revoc_reg_delta_request = \
                    await ledger.build_get_revoc_reg_delta_request(_did, item['rev_reg_id'], timestamp_from, timestamp_to)
                get_revoc_reg_delta_response = \
                    await ensure_previous_request_applied(pool_handle, get_revoc_reg_delta_request,
                                                        lambda response: response['result']['data'] is not None)
                (rev_reg_id, revoc_reg_delta_json, t) = \
                    await ledger.parse_get_revoc_reg_delta_response(get_revoc_reg_delta_response)

                tails_reader_config = json.dumps(
                    {'base_dir': dirname(json.loads(revoc_reg_def_json)['value']['tailsLocation']),
                    'uri_pattern': ''})
                blob_storage_reader_cfg_handle = await blob_storage.open_reader('default', tails_reader_config)

                logger.info('%s - Create Revocation State', actor)
                rev_state_json = \
                    await anoncreds.create_revocation_state(blob_storage_reader_cfg_handle, revoc_reg_def_json,
                                                            revoc_reg_delta_json, t, item['cred_rev_id'])
                rev_states[rev_reg_id] = {t: json.loads(rev_state_json)}

        return json.dumps(schemas), json.dumps(cred_defs), json.dumps(rev_states)
    

    async def get_schema(self, pool_handle, _did, schema_id):
        print("COMPARE THIS GET SHCEMA RESPONSE")
        print(pool_handle)
        print(_did)
        print(schema_id)
        get_schema_request = await ledger.build_get_schema_request(_did, schema_id)
        print(get_schema_request)
        get_schema_response = await ensure_previous_request_applied(
            pool_handle, get_schema_request, lambda response: response['result']['data'] is not None)
        print(get_schema_response)
        return await ledger.parse_get_schema_response(get_schema_response)
    
    async def get_cred_def(self, pool_handle, _did, cred_def_id):
        get_cred_def_request = await ledger.build_get_cred_def_request(_did, cred_def_id)
        get_cred_def_response = \
            await ensure_previous_request_applied(pool_handle, get_cred_def_request,
                                                lambda response: response['result']['data'] is not None)
        return await ledger.parse_get_cred_def_response(get_cred_def_response)


# async def run():

#     pool_ = {
#         'name': 'pool'
#     }
#     logger.info("Open Pool Ledger: {}".format(pool_['name']))
#     pool_['genesis_txn_path'] = get_pool_genesis_txn_path(pool_['name'])
#     pool_['config'] = json.dumps({"genesis_txn": str(pool_['genesis_txn_path'])})

#     # Set protocol version 2 to work with Indy Node 1.4
#     await pool.set_protocol_version(PROTOCOL_VERSION)

#     try:
#         # await pool.delete_pool_ledger_config(config_name=pool_['name'])
#         await pool.create_pool_ledger_config(pool_['name'], pool_['config'])
#     except IndyError as ex:
#         if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
#             await pool.delete_pool_ledger_config(config_name=pool_['name'])
#             await pool.create_pool_ledger_config(config_name=pool_['name'], config=pool_['config'])
#             pass
#     pool_['handle'] = await pool.open_pool_ledger(pool_['name'], None)

#     logger.info("==============================")
#     logger.info("=== Getting Transcript with Toll Company ==")
#     logger.info("==============================")
#     logger.info("== RSU setup ==")
#     logger.info("------------------------------")

#     rsu = {
#         'name': 'Rsu',
#         'wallet_config': json.dumps({'id': 'rsu_wallet'}),
#         'wallet_credentials': json.dumps({'key': 'rsu_wallet_key'}),
#         'pool': pool_['handle'],
#     }
#     await create_wallet(rsu)
#     (rsu['did'], rsu['key']) = await did.create_and_store_my_did(rsu['wallet'], "{}")

# ########################################################################################################
#     # create socket
#     # listening to tollcompany['transcript_cred_offer'] from toll company
#     # close socket
# ########################################################################################################
#     rsu['transcript_cred_offer'] = listening_to_transcript_cred_offer()


#     transcript_cred_offer_object = json.loads(rsu['transcript_cred_offer'])

#     rsu['transcript_schema_id'] = transcript_cred_offer_object['schema_id']
#     rsu['transcript_cred_def_id'] = transcript_cred_offer_object['cred_def_id']

#     logger.info("\"RSU\" -> Create and store \"RSU\" Master Secret in Wallet")
#     rsu['master_secret_id'] = await anoncreds.prover_create_master_secret(rsu['wallet'], None)

#     logger.info("\"RSU\" -> Get \"Toll Company Transcript\" Credential Definition from Ledger")
#     (rsu['tollcompany_transcript_cred_def_id'], rsu['tollcompany_transcript_cred_def']) = \
#         await get_cred_def(rsu['pool'], rsu['did'], rsu['transcript_cred_def_id'])

#     logger.info("\"RSU\" -> Create \"Transcript\" Credential Request for Toll Company")
#     (rsu['transcript_cred_request'], rsu['transcript_cred_request_metadata']) = \
#         await anoncreds.prover_create_credential_req(rsu['wallet'], rsu['did'],
#                                                     rsu['transcript_cred_offer'], rsu['tollcompany_transcript_cred_def'],
#                                                     rsu['master_secret_id'])

# ########################################################################################################
#     # create socket
#     # send rsu['transcript_cred_request'] to toll company
#     # wait for response
#     # receive rsu['transcript_cred_def']
# ########################################################################################################

#     await anoncreds.prover_store_credential(rsu['wallet'], None, rsu['transcript_cred_request_metadata'],
#                                         rsu['transcript_cred'], rsu['transcript_cred_def'], None)

# async def create_wallet(identity):
#     logger.info("\"{}\" -> Create wallet".format(identity['name']))
#     try:
#         await wallet.create_wallet(wallet_config("create", identity['wallet_config']),
#                                    wallet_credentials("create", identity['wallet_credentials']))
#     except IndyError as ex:
#         if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
#             pass
#     identity['wallet'] = await wallet.open_wallet(wallet_config("open", identity['wallet_config']),
#                                                   wallet_credentials("open", identity['wallet_credentials']))

# def wallet_config(operation, wallet_config_str):
#     if not args.storage_type:
#         return wallet_config_str
#     wallet_config_json = json.loads(wallet_config_str)
#     wallet_config_json['storage_type'] = args.storage_type
#     if args.config:
#         wallet_config_json['storage_config'] = json.loads(args.config)
#     # print(operation, json.dumps(wallet_config_json))
#     return json.dumps(wallet_config_json)

# def wallet_credentials(operation, wallet_credentials_str):
#     if not args.storage_type:
#         return wallet_credentials_str
#     wallet_credentials_json = json.loads(wallet_credentials_str)
#     if args.creds:
#         wallet_credentials_json['storage_credentials'] = json.loads(args.creds)
#     # print(operation, json.dumps(wallet_credentials_json))
#     return json.dumps(wallet_credentials_json)





if __name__ == '__main__':
    test = RSUTest()
    time.sleep(1)  # FIXME waiting for libindy thread complete
