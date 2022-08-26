
import asyncio
import json

from indy import pool, ledger, wallet, did, anoncreds
from indy.error import ErrorCode, IndyError

from utils import get_pool_genesis_txn_path, PROTOCOL_VERSION

pool_name = 'pool0'
wallet_config = json.dumps({"id": "wallet"})
wallet_credentials = json.dumps({"key": "wallet_key"})
genesis_file_path = get_pool_genesis_txn_path(pool_name)


class BackOfficeUtils:

    def __init__(self):
        do_nothing = True
        self.pool_handle = -1
        self.steward_did = ""
        self.wallet_handle = ""
        self.trust_anchor = {
            'name': 'BackOffice',
            'wallet_config': json.dumps({"id": "back_office_wallet"}),
            'wallet_credentials': json.dumps({'key': 'back_office_wallet_key'}),
            'role': 'TRUST_ANCHOR'
        }
    
    async def open_pool(self):
        try:
            await pool.set_protocol_version(PROTOCOL_VERSION)
        except IndyError as e:
            print('Error occurred: %s' % e)

        self.print_log("DEBUG", '\nOpening a new local pool ledger configuration that will be used later when connecting to ledger.\n')
        pool_config = json.dumps({'genesis_txn': str(genesis_file_path)})
        
        try:
            await pool.create_pool_ledger_config(config_name=pool_name, config=pool_config)   
        except IndyError as ex:
            if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
                pass
        
        try:
            self.pool_handle = await pool.open_pool_ledger(config_name=pool_name, config=None)
            print(str(self.pool_handle))
        except IndyError as e:
            print('Error occurred: %s' % e)

        print(str(self.pool_handle))
        
        

    async def create_wallet_trust_anchor(self):
        self.print_log("DEBUG", '\nCreating new secure wallet with the given unique name\n')
        try:
            await wallet.create_wallet(wallet_config, wallet_credentials)
        except IndyError as ex:
            if ex.error_code == ErrorCode.WalletAlreadyExistsError:
                pass
        self.print_log("DEBUG", '\nOpen wallet and get handle from libindy to use in methods that require wallet access\n')
        
        try:
            self.wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)
        except IndyError as e:
            print('Error occurred: %s' % e)
        print(self.wallet_handle)

        self.print_log("DEBUG", '\nGenerating and storing steward DID and verkey\n')
        steward_seed = '000000000000000000000000Steward1'
        did_json = json.dumps({'seed': steward_seed})

        try:
            self.steward_did, steward_verkey = await did.create_and_store_my_did(self.wallet_handle, did_json)
        except IndyError as e:
            print('Error occurred: %s' % e)
        
        self.print_log("DEBUG", "Steward DID: {}".format(self.steward_did))
        self.print_log("DEBUG", "Steward Verkey: {}".format(steward_verkey))
        
        self.print_log("DEBUG", '\nGenerating and storing trust anchor DID and verkey\n')
        try:
            self.trust_anchor['trust_anchor_did'], self.trust_anchor['trust_anchor_verkey'] = await did.create_and_store_my_did(self.wallet_handle, "{}")
        except IndyError as e:
            print('Error occurred: %s' % e)

        self.print_log("DEBUG", "Trust anchor DID: {}".format(self.trust_anchor['trust_anchor_did']))
        self.print_log("DEBUG", "Trust anchor Verkey: {}".format(self.trust_anchor['trust_anchor_verkey']))

        self.print_log("DEBUG", '\nBuilding NYM request to add Trust Anchor to the ledger\n')
        try:
            nym_transaction_request = await ledger.build_nym_request(submitter_did=self.steward_did,
                                                                    target_did=self.trust_anchor['trust_anchor_did'],
                                                                    ver_key=self.trust_anchor['trust_anchor_verkey'],
                                                                    alias=None,
                                                                    role='TRUST_ANCHOR')
        except IndyError as e:
            print('Error occurred: %s' % e)

        self.print_log("DEBUG", '\nSending NYM request to the ledger\n')
        print(self.pool_handle)
        print(self.wallet_handle)
        print(self.steward_did)
        print(str(nym_transaction_request))
        try:
            nym_transaction_response = await ledger.sign_and_submit_request(pool_handle=self.pool_handle,
                                                                            wallet_handle=self.wallet_handle,
                                                                            submitter_did=self.steward_did,
                                                                            request_json=nym_transaction_request)
        except IndyError as e:
            print('Error occurred: %s' % e)
        self.print_log("DEBUG", 'NYM transaction response: {} '.format(str(nym_transaction_response)))
        


    async def issue_credential(self):
       
        self.print_log("DEBUG", '\nIssuer create Credential Schema\n')
        schema = {
            'name': 'RSU-Schema',
            'version': '1.0',
            'attributes': ['id', 'localization']
        }
        try:
            self.trust_anchor['issuer_schema_id'], self.trust_anchor['issuer_schema_json'] = await anoncreds.issuer_create_schema(self.steward_did, 
                                                                                    schema['name'],
                                                                                    schema['version'],
                                                                                    json.dumps(schema['attributes']))
        except IndyError as e:
            print('Error occurred: %s' % e)
        
        print(self.trust_anchor['issuer_schema_json'])
        self.print_log("DEBUG", self.trust_anchor['issuer_schema_json'])

        # 10.
        self.print_log("DEBUG", '\nBuild the SCHEMA request to add new schema to the ledger\n')
        try:
            schema_request = await ledger.build_schema_request(self.steward_did, self.trust_anchor['issuer_schema_json'])
        except IndyError as e:
            print('Error occurred: %s' % e)
        self.print_log("DEBUG", str(json.loads(schema_request)))

        # 11.
        self.print_log("DEBUG", '\nSending the SCHEMA request to the ledger\n')
        try:
            schema_response = \
                await ledger.sign_and_submit_request(self.pool_handle,
                                                    self.wallet_handle,
                                                    self.steward_did,
                                                    schema_request)
        except IndyError as e:
            print('Error occurred: %s' % e)
        
        self.print_log("DEBUG", 'Schema response: {}'.format(str(schema_response)))

        # 12.
        self.print_log("DEBUG", '\nCreating and storing Credential Definition using anoncreds as Trust Anchor, for the given Schema\n')
        cred_def_tag = 'TAG1'
        cred_def_type = 'CL'
        cred_def_config = json.dumps({"support_revocation": False})

        try:
            (self.trust_anchor['transcript_cred_def_id'], self.trust_anchor['transcript_cred_def']) = \
                await anoncreds.issuer_create_and_store_credential_def(self.wallet_handle,
                                                                    self.trust_anchor['trust_anchor_did'],
                                                                    self.trust_anchor['issuer_schema_json'],
                                                                    cred_def_tag,
                                                                    cred_def_type,
                                                                    cred_def_config)
        except IndyError as e:
            print('Error occurred: %s' % e)

        self.print_log("DEBUG", 'Credential definition: ')

        self.print_log("DEBUG", '\n12. Creating credential offer for RSU\n')
        try:
            self.trust_anchor['transcript_cred_offer'] = \
                await anoncreds.issuer_create_credential_offer(self.wallet_handle, self.trust_anchor['transcript_cred_def_id'])
        except IndyError as e:
            print('Error occurred: %s' % e)
        
        self.print_log("WARNING", self.trust_anchor['transcript_cred_offer'])
        
        return (self.trust_anchor['transcript_cred_offer'], self.trust_anchor['transcript_cred_def'])

    
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

