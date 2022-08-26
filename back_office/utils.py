from os import environ
from pathlib import Path
from tempfile import gettempdir

from indy import anoncreds, did, ledger, pool, wallet, blob_storage
from indy.error import ErrorCode, IndyError

import asyncio
import json
import socket
import logging

PROTOCOL_VERSION = 2

# def path_home() -> Path:
#     return Path.home().joinpath(".indy_client")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_pool_genesis_txn_path(pool_name):
    path_temp = Path(gettempdir()).joinpath("indy")
    path = path_temp.joinpath("{}.txn".format(pool_name))
    save_pool_genesis_txn_file(path)
    return path

def pool_genesis_txn_data():
    #pool_ip = environ.get("TEST_POOL_IP", "127.0.0.1")
    #pool_ip = environ.get("TEST_POOL_IP", "192.168.94.27")
    pool_ip = environ.get("TEST_POOL_IP", "192.168.12.141")

    return "\n".join([
        '{{"reqSignature":{{}},"txn":{{"data":{{"data":{{"alias":"Node1","blskey":"4N8aUNHSgjQVgkpm8nhNEfDf6txHznoYREg9kirmJrkivgL4oSEimFF6nsQ6M41QvhM2Z33nves5vfSn9n1UwNFJBYtWVnHYMATn76vLuL3zU88KyeAYcHfsih3He6UHcXDxcaecHVz6jhCYz1P2UZn2bDVruL5wXpehgBfBaLKm3Ba","blskey_pop":"RahHYiCvoNCtPTrVtP7nMC5eTYrsUA8WjXbdhNc8debh1agE9bGiJxWBXYNFbnJXoXhWFMvyqhqhRoq737YQemH5ik9oL7R4NTTCz2LEZhkgLJzB3QRQqJyBNyv7acbdHrAT8nQ9UkLbaVL9NBpnWXBTw4LEMePaSHEw66RzPNdAX1","client_ip":"{}","client_port":9702,"node_ip":"{}","node_port":9701,"services":["VALIDATOR"]}},"dest":"Gw6pDLhcBcoQesN72qfotTgFa7cbuqZpkX3Xo6pLhPhv"}},"metadata":{{"from":"Th7MpTaRZVRYnPiabds81Y"}},"type":"0"}},"txnMetadata":{{"seqNo":1,"txnId":"fea82e10e894419fe2bea7d96296a6d46f50f93f9eeda954ec461b2ed2950b62"}},"ver":"1"}}'.format(
            pool_ip, pool_ip),
        '{{"reqSignature":{{}},"txn":{{"data":{{"data":{{"alias":"Node2","blskey":"37rAPpXVoxzKhz7d9gkUe52XuXryuLXoM6P6LbWDB7LSbG62Lsb33sfG7zqS8TK1MXwuCHj1FKNzVpsnafmqLG1vXN88rt38mNFs9TENzm4QHdBzsvCuoBnPH7rpYYDo9DZNJePaDvRvqJKByCabubJz3XXKbEeshzpz4Ma5QYpJqjk","blskey_pop":"Qr658mWZ2YC8JXGXwMDQTzuZCWF7NK9EwxphGmcBvCh6ybUuLxbG65nsX4JvD4SPNtkJ2w9ug1yLTj6fgmuDg41TgECXjLCij3RMsV8CwewBVgVN67wsA45DFWvqvLtu4rjNnE9JbdFTc1Z4WCPA3Xan44K1HoHAq9EVeaRYs8zoF5","client_ip":"{}","client_port":9704,"node_ip":"{}","node_port":9703,"services":["VALIDATOR"]}},"dest":"8ECVSk179mjsjKRLWiQtssMLgp6EPhWXtaYyStWPSGAb"}},"metadata":{{"from":"EbP4aYNeTHL6q385GuVpRV"}},"type":"0"}},"txnMetadata":{{"seqNo":2,"txnId":"1ac8aece2a18ced660fef8694b61aac3af08ba875ce3026a160acbc3a3af35fc"}},"ver":"1"}}'.format(
            pool_ip, pool_ip),
        '{{"reqSignature":{{}},"txn":{{"data":{{"data":{{"alias":"Node3","blskey":"3WFpdbg7C5cnLYZwFZevJqhubkFALBfCBBok15GdrKMUhUjGsk3jV6QKj6MZgEubF7oqCafxNdkm7eswgA4sdKTRc82tLGzZBd6vNqU8dupzup6uYUf32KTHTPQbuUM8Yk4QFXjEf2Usu2TJcNkdgpyeUSX42u5LqdDDpNSWUK5deC5","blskey_pop":"QwDeb2CkNSx6r8QC8vGQK3GRv7Yndn84TGNijX8YXHPiagXajyfTjoR87rXUu4G4QLk2cF8NNyqWiYMus1623dELWwx57rLCFqGh7N4ZRbGDRP4fnVcaKg1BcUxQ866Ven4gw8y4N56S5HzxXNBZtLYmhGHvDtk6PFkFwCvxYrNYjh","client_ip":"{}","client_port":9706,"node_ip":"{}","node_port":9705,"services":["VALIDATOR"]}},"dest":"DKVxG2fXXTU8yT5N7hGEbXB3dfdAnYv1JczDUHpmDxya"}},"metadata":{{"from":"4cU41vWW82ArfxJxHkzXPG"}},"type":"0"}},"txnMetadata":{{"seqNo":3,"txnId":"7e9f355dffa78ed24668f0e0e369fd8c224076571c51e2ea8be5f26479edebe4"}},"ver":"1"}}'.format(
            pool_ip, pool_ip),
        '{{"reqSignature":{{}},"txn":{{"data":{{"data":{{"alias":"Node4","blskey":"2zN3bHM1m4rLz54MJHYSwvqzPchYp8jkHswveCLAEJVcX6Mm1wHQD1SkPYMzUDTZvWvhuE6VNAkK3KxVeEmsanSmvjVkReDeBEMxeDaayjcZjFGPydyey1qxBHmTvAnBKoPydvuTAqx5f7YNNRAdeLmUi99gERUU7TD8KfAa6MpQ9bw","blskey_pop":"RPLagxaR5xdimFzwmzYnz4ZhWtYQEj8iR5ZU53T2gitPCyCHQneUn2Huc4oeLd2B2HzkGnjAff4hWTJT6C7qHYB1Mv2wU5iHHGFWkhnTX9WsEAbunJCV2qcaXScKj4tTfvdDKfLiVuU2av6hbsMztirRze7LvYBkRHV3tGwyCptsrP","client_ip":"{}","client_port":9708,"node_ip":"{}","node_port":9707,"services":["VALIDATOR"]}},"dest":"4PS3EDQ3dW1tci1Bp6543CfuuebjFrg36kLAUcskGfaA"}},"metadata":{{"from":"TWwCRQRZ2ZHMJFn9TzLp7W"}},"type":"0"}},"txnMetadata":{{"seqNo":4,"txnId":"aa5e817d7cc626170eca175822029339a444eb0ee8f0bd20d3b0b76e566fb008"}},"ver":"1"}}'.format(
            pool_ip, pool_ip)
    ])

def save_pool_genesis_txn_file(path):
    data = pool_genesis_txn_data()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path), "w+") as f:
        f.writelines(data)

# Open and create wallet if not exists
async def open_wallet(wallet_config, wallet_credentials):
    try:
        await wallet.create_wallet(wallet_config, wallet_credentials)
    except IndyError as ex:
        if ex.error_code == ErrorCode.WalletAlreadyExistsError:
            pass
    return await wallet.open_wallet(wallet_config, wallet_credentials)

async def ensure_previous_request_applied(pool_handle, checker_request, checker):
    for _ in range(3):
        response = json.loads(await ledger.submit_request(pool_handle, checker_request))
        try:
            if checker(response):
                return json.dumps(response)
        except TypeError:
            pass
        time.sleep(5)

def run_coroutine(coroutine, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()
    loop.run_until_complete(coroutine())

async def open_pool():
    pool_ = {
        'name': 'pool'
    }
    logger.info("Open Pool Ledger: {}".format(pool_['name']))
    pool_['genesis_txn_path'] = get_pool_genesis_txn_path(pool_['name'])
    pool_['config'] = json.dumps({"genesis_txn": str(pool_['genesis_txn_path'])})

    # Set protocol version 2 to work with Indy Node 1.4
    await pool.set_protocol_version(PROTOCOL_VERSION)

    try:
        await pool.create_pool_ledger_config(pool_['name'], pool_['config'])
    except IndyError as ex:
        if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
            pass
    pool_['handle'] = await pool.open_pool_ledger(pool_['name'], None)
    return pool_['handle']

async def create_steward_wallet():
    identity['wallet'] = await create_wallet(steward)

async def create_wallet(identity):
    logger.info("\"{}\" -> Create wallet".format(identity['name']))
    try:
        await wallet.create_wallet(wallet_config("create", identity['wallet_config']),
                                   wallet_credentials("create", identity['wallet_credentials']))
    except IndyError as ex:
        if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
            pass
    identity['wallet'] = await wallet.open_wallet(wallet_config("open", identity['wallet_config']),
                                                  wallet_credentials("open", identity['wallet_credentials']))

    return identity['wallet']

async def create_and_store_steward_credentials():
    steward['did'], steward['key'] = await did.create_and_store_my_did(steward['wallet'], steward['did_info'])
    return (steward['did'], steward['key'])

async def get_verinym_for_government(steward, government):
    await getting_verinym(steward, government)

async def getting_verinym(from_, to):
    await create_wallet(to)

    (to['did'], to['key']) = await did.create_and_store_my_did(to['wallet'], "{}")

    from_['info'] = {
        'did': to['did'],
        'verkey': to['key'],
        'role': to['role'] or None
    }

    await send_nym(from_['pool'], from_['wallet'], from_['did'], from_['info']['did'],
                   from_['info']['verkey'], from_['info']['role'])


async def send_nym(pool_handle, wallet_handle, _did, new_did, new_key, role):
    nym_request = await ledger.build_nym_request(_did, new_did, new_key, None, role)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, nym_request)

async def get_verinym_for_government(steward, government):
    await getting_verinym(steward, tollcompany)

async def issuer_create_schema():
    (government['toll_certificate_schema_id'], government['toll_certificate_schema']) = \
        await anoncreds.issuer_create_schema(government['did'], toll_certificate['name'], toll_certificate['version'],
                                             json.dumps(toll_certificate['attributes']))
    return (government['toll_certificate_schema_id'], government['toll_certificate_schema'])

async def issuer_send_schema():
    await send_schema(government['pool'], government['wallet'], government['did'], government['toll_certificate_schema'])

async def send_schema(pool_handle, wallet_handle, _did, schema):
    schema_request = await ledger.build_schema_request(_did, schema)
    schema_response = await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, schema_request)
    print("OK", 'Schema response: {}'.format(str(schema_response)))

async def issuer_create_schema():
    (government['transcript_schema_id'], government['transcript_schema']) = \
        await anoncreds.issuer_create_schema(government['did'], transcript['name'], transcript['version'],
                                             json.dumps(transcript['attributes']))
    return (government['transcript_schema_id'], government['transcript_schema'])

async def issuer_send_schema():
    await send_schema(government['pool'], government['wallet'], government['did'], government['transcript_schema'])

async def send_schema(pool_handle, wallet_handle, _did, schema):
    schema_request = await ledger.build_schema_request(_did, schema)
    schema_response = await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, schema_request)
    print("OK", 'Schema response: {}'.format(str(schema_response)))

async def toll_company_get_schema():
    (tollcompany['transcript_schema_id'], tollcompany['transcript_schema']) = \
        await get_schema(tollcompany['pool'], tollcompany['did'], transcript_schema_id)
    return (tollcompany['transcript_schema_id'], tollcompany['transcript_schema'])
       
async def issuer_create_and_store_credential_def_transcript():
    (tollcompany['transcript_cred_def_id'], tollcompany['transcript_cred_def']) = \
        await anoncreds.issuer_create_and_store_credential_def(tollcompany['wallet'], tollcompany['did'],
                                                               tollcompany['transcript_schema'], transcript_cred_def['tag'],
                                                               transcript_cred_def['type'],
                                                               json.dumps(transcript_cred_def['config']))
    return (tollcompany['transcript_cred_def_id'], tollcompany['transcript_cred_def'])

async def send_cred_def(pool_handle, wallet_handle, _did, cred_def_json):
    cred_def_request = await ledger.build_cred_def_request(_did, cred_def_json)
    result = await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, cred_def_request)

async def toll_company_get_schema():
    (tollcompany['toll_certificate_schema_id'], tollcompany['toll_certificate_schema']) = \
        await get_schema(tollcompany['pool'], tollcompany['did'], toll_certificate_schema_id)
    return (tollcompany['toll_certificate_schema_id'], tollcompany['toll_certificate_schema'])

async def issuer_create_and_store_credential_def():
        (tollcompany['toll_certificate_cred_def_id'], tollcompany['toll_certificate_cred_def']) = \
        await anoncreds.issuer_create_and_store_credential_def(tollcompany['wallet'], tollcompany['did'],
                                                               tollcompany['toll_certificate_schema'],
                                                               toll_certificate_cred_def['tag'],
                                                               toll_certificate_cred_def['type'],
                                                               json.dumps(toll_certificate_cred_def['config']))
        return (tollcompany['toll_certificate_cred_def_id'], tollcompany['toll_certificate_cred_def'])
       
async def send_cred_def_to_ledger():
    await send_cred_def(tollcompany['pool'], tollcompany['wallet'], tollcompany['did'], tollcompany['toll_certificate_cred_def'])

async def send_cred_def(pool_handle, wallet_handle, _did, cred_def_json):
    cred_def_request = await ledger.build_cred_def_request(_did, cred_def_json)
    result = await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, cred_def_request)

async def write_to_blob_storage():
    tails_writer = await blob_storage.open_writer('default', tollcompany['tails_writer_config'])
    return tails_writer

async def issuer_create_and_store_rev_reg():
        (tollcompany['revoc_reg_id'], tollcompany['revoc_reg_def'], tollcompany['revoc_reg_entry']) = \
        await anoncreds.issuer_create_and_store_revoc_reg(tollcompany['wallet'], tollcompany['did'], 'CL_ACCUM', 'TAG1',
                                                          tollcompany['toll_certificate_cred_def_id'],
                                                          json.dumps({'max_cred_num': 5,
                                                                      'issuance_type': 'ISSUANCE_ON_DEMAND'}),
                                                          tails_writer)
        return (tollcompany['revoc_reg_id'], tollcompany['revoc_reg_def'], tollcompany['revoc_reg_entry'])

async def build_rev_reg__def_req():
    tollcompany['revoc_reg_def_request'] = await ledger.build_revoc_reg_def_request(tollcompany['did'], tollcompany['revoc_reg_def'])
    return tollcompany['revoc_reg_def_request']
    
async def sign_and_submit_req():
    await ledger.sign_and_submit_request(tollcompany['pool'], tollcompany['wallet'], tollcompany['did'], tollcompany['revoc_reg_def_request'])

async def build_rev_reg__def_req():
    tollcompany['revoc_reg_entry_request'] = \
        await ledger.build_revoc_reg_entry_request(tollcompany['did'], tollcompany['revoc_reg_id'], 'CL_ACCUM',
                                                   tollcompany['revoc_reg_entry'])
    return tollcompany['revoc_reg_entry_request']

async def sign_and_submit_entry_request():
    await ledger.sign_and_submit_request(tollcompany['pool'], tollcompany['wallet'], tollcompany['did'], tollcompany['revoc_reg_entry_request'])

async def create_rsu_keys():
     (rsu['did'], rsu['key']) = await did.create_and_store_my_did(rsu['wallet'], "{}")
     return (rsu['did'], rsu['key'])
    
async def issuer_create_credential_offer():
    tollcompany['transcript_cred_offer'] = \
        await anoncreds.issuer_create_credential_offer(tollcompany['wallet'], tollcompany['transcript_cred_def_id'])
    return tollcompany['trascript_cred_offer']

async def prover_create_master_secret():
    rsu['master_secret_id'] = await anoncreds.prover_create_master_secret(rsu['wallet'], None)
    return rsu['master_secret_id']

async def prover_get_cred_def():
    (rsu['tollcompany_transcript_cred_def_id'], rsu['tollcompany_transcript_cred_def']) = \
        await get_cred_def(rsu['pool'], rsu['did'], rsu['transcript_cred_def_id'])
    return (rsu['tollcompany_transcript_cred_def_id'], rsu['tollcompany_transcript_cred_def'])

async def get_cred_def(pool_handle, _did, cred_def_id):
    get_cred_def_request = await ledger.build_get_cred_def_request(_did, cred_def_id)
    get_cred_def_response = \
        await ensure_previous_request_applied(pool_handle, get_cred_def_request,
                                              lambda response: response['result']['data'] is not None)
    return await ledger.parse_get_cred_def_response(get_cred_def_response)

async def prover_create_cred_req():
    (rsu['transcript_cred_request'], rsu['transcript_cred_request_metadata']) = \
        await anoncreds.prover_create_credential_req(rsu['wallet'], rsu['did'],
                                                     rsu['transcript_cred_offer'], rsu['tollcompany_transcript_cred_def'],
                                                     rsu['master_secret_id'])

    return (rsu['transcript_cred_request'], rsu['transcript_cred_request_metadata'])

async def issuer_create_cred():
    tollcompany['transcript_cred'], _, _ = \
        await anoncreds.issuer_create_credential(tollcompany['wallet'], tollcompany['transcript_cred_offer'],
                                                 tollcompany['transcript_cred_request'],
                                                 tollcompany['rsu_transcript_cred_values'], None, None)
    return tollcompany['transcript_cred']

async def prover_get_cred_def():
    _, rsu['transcript_cred_def'] = await get_cred_def(rsu['pool'], rsu['did'],
                                                         rsu['transcript_cred_def_id'])
    return rsu['transcript_cred_def']

async def prover_store_cred():
        await anoncreds.prover_store_credential(rsu['wallet'], None, rsu['transcript_cred_request_metadata'],
                                            rsu['transcript_cred'], rsu['transcript_cred_def'], None)


def send_cred_offer_to_rsu():
    RSU_IP = "127.0.0.1"
    RSU_PORT = 5558
    serverAddress = (RSU_IP, RSU_PORT)
    with socket.socket(socket.AF_INET, socker.SOCK_STREAM) as s:
        s.connect(serverAddress)
        print("BO sending hello world to rsu")
        s.send(("HelloWorld").encode('utf-8'))
