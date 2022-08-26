import time

from indy import anoncreds, did, ledger, pool, wallet, blob_storage

import json
import logging

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

# check if we need to dyna-load a custom wallet storage plug-in
if args.storage_type:
    if not (args.library and args.entrypoint):
        parser.print_help()
        sys.exit(0)
    stg_lib = CDLL(args.library)
    result = stg_lib[args.entrypoint]()
    if result != 0:
        print("Error unable to load wallet storage", result)
        parser.print_help()
        sys.exit(0)

    # for postgres storage, also call the storage init (non-standard)
    if args.storage_type == "postgres_storage":
        try:
            print("Calling init_storagetype() for postgres:", args.config, args.creds)
            init_storagetype = stg_lib["init_storagetype"]
            c_config = c_char_p(args.config.encode('utf-8'))
            c_credentials = c_char_p(args.creds.encode('utf-8'))
            result = init_storagetype(c_config, c_credentials)
            print(" ... returns ", result)
        except RuntimeError as e:
            print("Error initializing storage, ignoring ...", e)

    print("Success, loaded wallet storage", args.storage_type)


async def run():
    logger.info("Getting started -> started")

    pool_ = {
        'name': 'pool'
    }
    logger.info("Open Pool Ledger: {}".format(pool_['name']))
    pool_['genesis_txn_path'] = get_pool_genesis_txn_path(pool_['name'])
    pool_['config'] = json.dumps({"genesis_txn": str(pool_['genesis_txn_path'])})

    # Set protocol version 2 to work with Indy Node 1.4
    await pool.set_protocol_version(PROTOCOL_VERSION)

    try:
        await pool.delete_pool_ledger_config(config_name=pool_['name'])
        await pool.create_pool_ledger_config(pool_['name'], pool_['config'])
    except IndyError as ex:
        if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
            await pool.delete_pool_ledger_config(config_name=pool_['name'])
            await pool.create_pool_ledger_config(config_name=pool_['name'], config=pool_['config'])
            pass
    pool_['handle'] = await pool.open_pool_ledger(pool_['name'], None)

    # logger.info("==============================")
    # logger.info("=== Getting Trust Anchor credentials for Faber, Acme, Thrift and Government  ==")
    # logger.info("------------------------------")

    logger.info("==============================")
    logger.info("=== Getting Trust Anchor credentials for Toll Company  ==")
    logger.info("------------------------------")

    steward = {
        'name': "Sovrin Steward",
        'wallet_config': json.dumps({'id': 'sovrin_steward_wallet'}),
        'wallet_credentials': json.dumps({'key': 'steward_wallet_key'}),
        'pool': pool_['handle'],
        'seed': '000000000000000000000000Steward1'
    }

    await create_wallet(steward)

    logger.info("\"Sovrin Steward\" -> Create and store in Wallet DID from seed")
    steward['did_info'] = json.dumps({'seed': steward['seed']})
    steward['did'], steward['key'] = await did.create_and_store_my_did(steward['wallet'], steward['did_info'])

    logger.info("==============================")
    logger.info("== Getting Trust Anchor credentials - Government getting Verinym  ==")
    logger.info("------------------------------")

    government = {
        'name': 'Government',
        'wallet_config': json.dumps({'id': 'government_wallet'}),
        'wallet_credentials': json.dumps({'key': 'government_wallet_key'}),
        'pool': pool_['handle'],
        'role': 'TRUST_ANCHOR'
    }

    await getting_verinym(steward, government)

    logger.info("==============================")
    logger.info("== Getting Trust Anchor credentials - Toll Company getting Verinym  ==")
    logger.info("------------------------------")

    tollcompany = {
        'name': 'Tollcompany',
        'wallet_config': json.dumps({'id': 'tollcompany_wallet'}),
        'wallet_credentials': json.dumps({'key': 'tollcompany_wallet_key'}),
        'pool': pool_['handle'],
        'role': 'TRUST_ANCHOR'
    }

    await getting_verinym(steward, tollcompany)

    # logger.info("==============================")
    # logger.info("== Getting Trust Anchor credentials - Acme getting Verinym  ==")
    # logger.info("------------------------------")

    # acme = {
    #     'name': 'Acme',
    #     'wallet_config': json.dumps({'id': 'acme_wallet'}),
    #     'wallet_credentials': json.dumps({'key': 'acme_wallet_key'}),
    #     'pool': pool_['handle'],
    #     'role': 'TRUST_ANCHOR'
    # }

    # await getting_verinym(steward, acme)

    # logger.info("==============================")
    # logger.info("== Getting Trust Anchor credentials - Thrift getting Verinym  ==")
    # logger.info("------------------------------")

    # thrift = {
    #     'name': 'Thrift',
    #     'wallet_config': json.dumps({'id': 'thrift_wallet'}),
    #     'wallet_credentials': json.dumps({'key': 'thrift_wallet_key'}),
    #     'pool': pool_['handle'],
    #     'role': 'TRUST_ANCHOR'
    # }

    # await getting_verinym(steward, thrift)

    logger.info("==============================")
    logger.info("=== Credential Schemas Setup ==")
    logger.info("------------------------------")

    logger.info("\"Government\" -> Create \"Toll-Certificate\" Schema")
    toll_certificate = {
        'name': 'Toll-Certificate',
        'version': '0.2',
        'attributes': ['name', 'id', 'status']
    }
    (government['toll_certificate_schema_id'], government['toll_certificate_schema']) = \
        await anoncreds.issuer_create_schema(government['did'], toll_certificate['name'], toll_certificate['version'],
                                             json.dumps(toll_certificate['attributes']))
    toll_certificate_schema_id = government['toll_certificate_schema_id']

    logger.info("\"Government\" -> Send \"Toll-Certificate\" Schema to Ledger")
    await send_schema(government['pool'], government['wallet'], government['did'], government['toll_certificate_schema'])

    logger.info("\"Government\" -> Create \"Transcript\" Schema")
    transcript = {
        'name': 'Transcript',
        'version': '1.2',
        'attributes': ['name', 'id', 'status']
    }
    (government['transcript_schema_id'], government['transcript_schema']) = \
        await anoncreds.issuer_create_schema(government['did'], transcript['name'], transcript['version'],
                                             json.dumps(transcript['attributes']))
    transcript_schema_id = government['transcript_schema_id']

    logger.info("\"Government\" -> Send \"Transcript\" Schema to Ledger")
    await send_schema(government['pool'], government['wallet'], government['did'], government['transcript_schema'])

    time.sleep(1)  # sleep 1 second before getting schema

    logger.info("==============================")
    logger.info("=== Toll Company Credential Definition Setup ==")
    logger.info("------------------------------")

    logger.info("\"Toll Company\" -> Get \"Transcript\" Schema from Ledger")
    (tollcompany['transcript_schema_id'], tollcompany['transcript_schema']) = \
        await get_schema(tollcompany['pool'], tollcompany['did'], transcript_schema_id)

    logger.info("\"Toll Company\" -> Create and store in Wallet \"Toll Company Transcript\" Credential Definition")
    transcript_cred_def = {
        'tag': 'TAG1',
        'type': 'CL',
        'config': {"support_revocation": False}
    }
    (tollcompany['transcript_cred_def_id'], tollcompany['transcript_cred_def']) = \
        await anoncreds.issuer_create_and_store_credential_def(tollcompany['wallet'], tollcompany['did'],
                                                               tollcompany['transcript_schema'], transcript_cred_def['tag'],
                                                               transcript_cred_def['type'],
                                                               json.dumps(transcript_cred_def['config']))

    logger.info("\"Toll Company\" -> Send  \"Toll Company Transcript\" Credential Definition to Ledger")
    await send_cred_def(tollcompany['pool'], tollcompany['wallet'], tollcompany['did'], tollcompany['transcript_cred_def'])

    logger.info("==============================")
    logger.info("=== Toll Company Credential Definition Setup ==")
    logger.info("------------------------------")

    logger.info("\"Toll Company\" -> Get from Ledger \"Toll-Certificate\" Schema")
    (tollcompany['toll_certificate_schema_id'], tollcompany['toll_certificate_schema']) = \
        await get_schema(tollcompany['pool'], tollcompany['did'], toll_certificate_schema_id)

    logger.info("\"Toll Company\" -> Create and store in Wallet \"Toll Company Toll-Certificate\" Credential Definition")
    toll_certificate_cred_def = {
        'tag': 'TAG1',
        'type': 'CL',
        'config': {"support_revocation": True}
    }
    (tollcompany['toll_certificate_cred_def_id'], tollcompany['toll_certificate_cred_def']) = \
        await anoncreds.issuer_create_and_store_credential_def(tollcompany['wallet'], tollcompany['did'],
                                                               tollcompany['toll_certificate_schema'],
                                                               toll_certificate_cred_def['tag'],
                                                               toll_certificate_cred_def['type'],
                                                               json.dumps(toll_certificate_cred_def['config']))

    logger.info("\"Toll Company\" -> Send \"Toll Company Toll-Certificate\" Credential Definition to Ledger")
    await send_cred_def(tollcompany['pool'], tollcompany['wallet'], tollcompany['did'], tollcompany['toll_certificate_cred_def'])

    logger.info("\"Toll Company\" -> Creates Revocation Registry")
    tollcompany['tails_writer_config'] = json.dumps({'base_dir': "/tmp/indy_tollcompany_tails", 'uri_pattern': ''})
    tails_writer = await blob_storage.open_writer('default', tollcompany['tails_writer_config'])
    (tollcompany['revoc_reg_id'], tollcompany['revoc_reg_def'], tollcompany['revoc_reg_entry']) = \
        await anoncreds.issuer_create_and_store_revoc_reg(tollcompany['wallet'], tollcompany['did'], 'CL_ACCUM', 'TAG1',
                                                          tollcompany['toll_certificate_cred_def_id'],
                                                          json.dumps({'max_cred_num': 5,
                                                                      'issuance_type': 'ISSUANCE_ON_DEMAND'}),
                                                          tails_writer)

    logger.info("\"Toll Company\" -> Post Revocation Registry Definition to Ledger")
    tollcompany['revoc_reg_def_request'] = await ledger.build_revoc_reg_def_request(tollcompany['did'], tollcompany['revoc_reg_def'])
    await ledger.sign_and_submit_request(tollcompany['pool'], tollcompany['wallet'], tollcompany['did'], tollcompany['revoc_reg_def_request'])

    logger.info("\"Toll Company\" -> Post Revocation Registry Entry to Ledger")
    tollcompany['revoc_reg_entry_request'] = \
        await ledger.build_revoc_reg_entry_request(tollcompany['did'], tollcompany['revoc_reg_id'], 'CL_ACCUM',
                                                   tollcompany['revoc_reg_entry'])
    await ledger.sign_and_submit_request(tollcompany['pool'], tollcompany['wallet'], tollcompany['did'], tollcompany['revoc_reg_entry_request'])

    logger.info("==============================")
    logger.info("=== Getting Transcript with Toll Company ==")
    logger.info("==============================")
    logger.info("== RSU setup ==")
    logger.info("------------------------------")

    rsu = {
        'name': 'Rsu',
        'wallet_config': json.dumps({'id': 'rsu_wallet'}),
        'wallet_credentials': json.dumps({'key': 'rsu_wallet_key'}),
        'pool': pool_['handle'],
    }
    await create_wallet(rsu)
    (rsu['did'], rsu['key']) = await did.create_and_store_my_did(rsu['wallet'], "{}")

    logger.info("==============================")
    logger.info("== Getting Transcript with Toll Company - Getting Transcript Credential ==")
    logger.info("------------------------------")

    logger.info("\"Toll Company\" -> Create \"Transcript\" Credential Offer for RSU")
    tollcompany['transcript_cred_offer'] = \
        await anoncreds.issuer_create_credential_offer(tollcompany['wallet'], tollcompany['transcript_cred_def_id'])

    logger.info("\"Toll Company\" -> Send \"Transcript\" Credential Offer to RSU")
    rsu['transcript_cred_offer'] = tollcompany['transcript_cred_offer']
    transcript_cred_offer_object = json.loads(rsu['transcript_cred_offer'])

    rsu['transcript_schema_id'] = transcript_cred_offer_object['schema_id']
    rsu['transcript_cred_def_id'] = transcript_cred_offer_object['cred_def_id']

    logger.info("\"RSU\" -> Create and store \"RSU\" Master Secret in Wallet")
    rsu['master_secret_id'] = await anoncreds.prover_create_master_secret(rsu['wallet'], None)

    logger.info("\"RSU\" -> Get \"Toll Company Transcript\" Credential Definition from Ledger")
    (rsu['tollcompany_transcript_cred_def_id'], rsu['tollcompany_transcript_cred_def']) = \
        await get_cred_def(rsu['pool'], rsu['did'], rsu['transcript_cred_def_id'])

    logger.info("\"RSU\" -> Create \"Transcript\" Credential Request for Toll Company")
    (rsu['transcript_cred_request'], rsu['transcript_cred_request_metadata']) = \
        await anoncreds.prover_create_credential_req(rsu['wallet'], rsu['did'],
                                                     rsu['transcript_cred_offer'], rsu['tollcompany_transcript_cred_def'],
                                                     rsu['master_secret_id'])

    logger.info("\"RSU\" -> Send \"Transcript\" Credential Request to Toll Company")
    tollcompany['transcript_cred_request'] = rsu['transcript_cred_request']

    logger.info("\"Toll Company\" -> Create \"Transcript\" Credential for RSU")
    tollcompany['rsu_transcript_cred_values'] = json.dumps({
        "name": {"raw": "rsu", "encoded": "1139481716457488690172217916278103335"},
        "id": {"raw": "123", "encoded": "123"},
        "status": {"raw": "enabled", "encoded": "2213454313412354"}
    })


    tollcompany['transcript_cred'], _, _ = \
        await anoncreds.issuer_create_credential(tollcompany['wallet'], tollcompany['transcript_cred_offer'],
                                                 tollcompany['transcript_cred_request'],
                                                 tollcompany['rsu_transcript_cred_values'], None, None)

    logger.info("\"Toll Company\" -> Send \"Transcript\" Credential to RSU")
    rsu['transcript_cred'] = tollcompany['transcript_cred']
    
    logger.info("\"RSU\" -> Store \"Transcript\" Credential from Toll Company")
    _, rsu['transcript_cred_def'] = await get_cred_def(rsu['pool'], rsu['did'],
                                                         rsu['transcript_cred_def_id'])

    await anoncreds.prover_store_credential(rsu['wallet'], None, rsu['transcript_cred_request_metadata'],
                                            rsu['transcript_cred'], rsu['transcript_cred_def'], None)

    print("THIS IS THE CREDENTIAL")
    print(rsu['transcript_cred_def'])

    # logger.info("==============================")
    # logger.info("== Apply for the rsu (toll colelctor) with Toll Company - Transcript proving ==")
    # logger.info("------------------------------")

    # logger.info("\"Toll Company\" -> Create \"Toll-Application\" Proof Request")
    # nonce = await anoncreds.generate_nonce()
    # tollcompany['toll_application_proof_request'] = json.dumps({
    #     'nonce': nonce,
    #     'name': 'Toll-Application',
    #     'version': '0.1',
    #     'requested_attributes': {
    #         'attr1_referent': {
    #             'name': 'name'
    #         },
    #         'attr3_referent': {
    #             'name': 'id',
    #             'restrictions': [{'cred_def_id': tollcompany['transcript_cred_def_id']}]
    #         },
    #         'attr4_referent': {
    #             'name': 'status',
    #             'restrictions': [{'cred_def_id': tollcompany['transcript_cred_def_id']}]
    #         },
    #         'attr6_referent': {
    #             'name': 'phone_number'
    #         }
    #     },
    #     'requested_predicates': {
    #         'predicate1_referent': {
    #             'name': 'average',
    #             'p_type': '>=',
    #             'p_value': 4,
    #             'restrictions': [{'cred_def_id': tollcompany['transcript_cred_def_id']}]
    #         }
    #     }
    # })

    # logger.info("\"Toll Company\" -> Send \"Toll-Application\" Proof Request to RSU")
    # rsu['toll_application_proof_request'] = tollcompany['job_application_proof_request']

    # logger.info("\"RSU\" -> Get credentials for \"Toll-Application\" Proof Request")

    # search_for_toll_application_proof_request = \
    #     await anoncreds.prover_search_credentials_for_proof_req(rsu['wallet'],
    #                                                             rsu['toll_application_proof_request'], None)

    # cred_for_attr1 = await get_credential_for_referent(search_for_toll_application_proof_request, 'attr1_referent')
    # cred_for_attr2 = await get_credential_for_referent(search_for_toll_application_proof_request, 'attr2_referent')
    # cred_for_attr3 = await get_credential_for_referent(search_for_toll_application_proof_request, 'attr3_referent')
    # cred_for_attr4 = await get_credential_for_referent(search_for_toll_application_proof_request, 'attr4_referent')
    # cred_for_attr5 = await get_credential_for_referent(search_for_toll_application_proof_request, 'attr5_referent')
    # cred_for_predicate1 = \
    #     await get_credential_for_referent(search_for_toll_application_proof_request, 'predicate1_referent')

    # await anoncreds.prover_close_credentials_search_for_proof_req(search_for_toll_application_proof_request)

    # rsu['creds_for_toll_application_proof'] = {cred_for_attr1['referent']: cred_for_attr1,
    #                                             cred_for_attr2['referent']: cred_for_attr2,
    #                                             cred_for_attr3['referent']: cred_for_attr3,
    #                                             cred_for_attr4['referent']: cred_for_attr4,
    #                                             cred_for_attr5['referent']: cred_for_attr5,
    #                                             cred_for_predicate1['referent']: cred_for_predicate1}

    # rsu['schemas_for_toll_application'], rsu['cred_defs_for_toll_application'], \
    # rsu['revoc_states_for_toll_application'] = \
    #     await prover_get_entities_from_ledger(rsu['pool'], rsu['did'],
    #                                           rsu['creds_for_toll_application_proof'], rsu['name'])

    # logger.info("\"RSU\" -> Create \"Toll-Application\" Proof")
    # alice['toll_application_requested_creds'] = json.dumps({
    #     'self_attested_attributes': {
    #         'attr1_referent': 'Alice',
    #         'attr2_referent': 'Garcia',
    #         'attr6_referent': '123-45-6789'
    #     },
    #     'requested_attributes': {
    #         'attr3_referent': {'cred_id': cred_for_attr3['referent'], 'revealed': True},
    #         'attr4_referent': {'cred_id': cred_for_attr4['referent'], 'revealed': True},
    #         'attr5_referent': {'cred_id': cred_for_attr5['referent'], 'revealed': True},
    #     },
    #     'requested_predicates': {'predicate1_referent': {'cred_id': cred_for_predicate1['referent']}}
    # })

    # rsu['toll_application_proof'] = \
    #     await anoncreds.prover_create_proof(rsu['wallet'], rsu['toll_application_proof_request'],
    #                                         rsu['toll_application_requested_creds'], rsu['master_secret_id'],
    #                                         rsu['schemas_for_toll_application'],
    #                                         rsu['cred_defs_for_toll_application'],
    #                                         rsu['revoc_states_for_toll_application'])

    # logger.info("\"RSU\" -> Send \"Toll-Application\" Proof to Toll Company")
    # tollcompany['toll_application_proof'] = rsu['toll_application_proof']

    # toll_application_proof_object = json.loads(tollcompany['toll_application_proof'])

    # tollcompany['schemas_for_toll_application'], tollcompany['cred_defs_for_toll_application'], \
    # tollcompany['revoc_ref_defs_for_toll_application'], tollcompany['revoc_regs_for_toll_application'] = \
    #     await verifier_get_entities_from_ledger(tollcompany['pool'], tollcompany['did'],
    #                                             toll_application_proof_object['identifiers'], tollcompany['name'])

    # logger.info("\"Toll Company\" -> Verify \"Toll-Application\" Proof from RSU")
    # assert 'Bachelor of Science, Marketing' == \
    #        job_application_proof_object['requested_proof']['revealed_attrs']['attr3_referent']['raw']
    # assert 'graduated' == \
    #        job_application_proof_object['requested_proof']['revealed_attrs']['attr4_referent']['raw']
    # assert '123-45-6789' == \
    #        job_application_proof_object['requested_proof']['revealed_attrs']['attr5_referent']['raw']

    # assert 'Alice' == job_application_proof_object['requested_proof']['self_attested_attrs']['attr1_referent']
    # assert 'Garcia' == job_application_proof_object['requested_proof']['self_attested_attrs']['attr2_referent']
    # assert '123-45-6789' == job_application_proof_object['requested_proof']['self_attested_attrs']['attr6_referent']

    # assert await anoncreds.verifier_verify_proof(acme['job_application_proof_request'], acme['job_application_proof'],
    #                                              acme['schemas_for_job_application'],
    #                                              acme['cred_defs_for_job_application'],
    #                                              acme['revoc_ref_defs_for_job_application'],
    #                                              acme['revoc_regs_for_job_application'])

    # logger.info("==============================")
    # logger.info("== Apply for the job with Acme - Getting Job-Certificate Credential ==")
    # logger.info("------------------------------")

    # logger.info("\"Acme\" -> Create \"Job-Certificate\" Credential Offer for Alice")
    # acme['job_certificate_cred_offer'] = \
    #     await anoncreds.issuer_create_credential_offer(acme['wallet'], acme['job_certificate_cred_def_id'])

    # logger.info("\"Acme\" -> Send \"Job-Certificate\" Credential Offer to Alice")
    # alice['job_certificate_cred_offer'] = acme['job_certificate_cred_offer']

    # job_certificate_cred_offer_object = json.loads(alice['job_certificate_cred_offer'])

    # logger.info("\"Alice\" -> Get \"Acme Job-Certificate\" Credential Definition from Ledger")
    # (alice['acme_job_certificate_cred_def_id'], alice['acme_job_certificate_cred_def']) = \
    #     await get_cred_def(alice['pool'], alice['did'], job_certificate_cred_offer_object['cred_def_id'])

    # logger.info("\"Alice\" -> Create and store in Wallet \"Job-Certificate\" Credential Request for Acme")
    # (alice['job_certificate_cred_request'], alice['job_certificate_cred_request_metadata']) = \
    #     await anoncreds.prover_create_credential_req(alice['wallet'], alice['did'],
    #                                                  alice['job_certificate_cred_offer'],
    #                                                  alice['acme_job_certificate_cred_def'], alice['master_secret_id'])

    # logger.info("\"Alice\" -> Send \"Job-Certificate\" Credential Request to Acme")
    # alice['job_certificate_cred_values'] = json.dumps({
    #     "name": {"raw": "Alice", "encoded": "245712572474217942457235975012103335"},
    #     "employee_status": {"raw": "Permanent", "encoded": "2143135425425143112321314321"},
    #     "salary": {"raw": "2400", "encoded": "2400"},
    #     "experience": {"raw": "10", "encoded": "10"}
    # })
    # acme['job_certificate_cred_request'] = alice['job_certificate_cred_request']
    # acme['job_certificate_cred_values'] = alice['job_certificate_cred_values']

    # logger.info("\"Acme\" -> Create \"Job-Certificate\" Credential for Alice")
    # acme['blob_storage_reader_cfg_handle'] = await blob_storage.open_reader('default', acme['tails_writer_config'])
    # acme['job_certificate_cred'], acme['job_certificate_cred_rev_id'], acme['alice_cert_rev_reg_delta'] = \
    #     await anoncreds.issuer_create_credential(acme['wallet'], acme['job_certificate_cred_offer'],
    #                                              acme['job_certificate_cred_request'],
    #                                              acme['job_certificate_cred_values'],
    #                                              acme['revoc_reg_id'],
    #                                              acme['blob_storage_reader_cfg_handle'])

    # logger.info("\"Acme\" -> Post Revocation Registry Delta to Ledger")
    # acme['revoc_reg_entry_req'] = \
    #     await ledger.build_revoc_reg_entry_request(acme['did'], acme['revoc_reg_id'], 'CL_ACCUM',
    #                                                acme['alice_cert_rev_reg_delta'])
    # await ledger.sign_and_submit_request(acme['pool'], acme['wallet'], acme['did'], acme['revoc_reg_entry_req'])

    # logger.info("\"Acme\" -> Send \"Job-Certificate\" Credential to Alice")
    # alice['job_certificate_cred'] = acme['job_certificate_cred']
    # job_certificate_cred_object = json.loads(alice['job_certificate_cred'])

    # logger.info("\"Alice\" -> Gets RevocationRegistryDefinition for \"Job-Certificate\" Credential from Acme")
    # alice['acme_revoc_reg_des_req'] = \
    #     await ledger.build_get_revoc_reg_def_request(alice['did'],
    #                                                  job_certificate_cred_object['rev_reg_id'])
    # alice['acme_revoc_reg_des_resp'] = \
    #     await ensure_previous_request_applied(alice['pool'], alice['acme_revoc_reg_des_req'],
    #                                           lambda response: response['result']['data'] is not None)
    # (alice['acme_revoc_reg_def_id'], alice['acme_revoc_reg_def_json']) = \
    #     await ledger.parse_get_revoc_reg_def_response(alice['acme_revoc_reg_des_resp'])

    # logger.info("\"Alice\" -> Store \"Job-Certificate\" Credential")
    # await anoncreds.prover_store_credential(alice['wallet'], None, alice['job_certificate_cred_request_metadata'],
    #                                         alice['job_certificate_cred'],
    #                                         alice['acme_job_certificate_cred_def'], alice['acme_revoc_reg_def_json'])

    # logger.info("==============================")
    # logger.info("=== Apply for the loan with Thrift ==")
    # logger.info("==============================")


    # async def apply_loan_basic():
    #     # This method will be called twice: once with a valid Job-Certificate and
    #     # the second time after the Job-Certificate has been revoked.
    #     logger.info("==============================")
    #     logger.info("== Apply for the loan with Thrift - Job-Certificate proving  ==")
    #     logger.info("------------------------------")

    #     logger.info("\"Thrift\" -> Create \"Loan-Application-Basic\" Proof Request")
    #     nonce = await anoncreds.generate_nonce()
    #     thrift['apply_loan_proof_request'] = json.dumps({
    #         'nonce': nonce,
    #         'name': 'Loan-Application-Basic',
    #         'version': '0.1',
    #         'requested_attributes': {
    #             'attr1_referent': {
    #                 'name': 'employee_status',
    #                 'restrictions': [{'cred_def_id': acme['job_certificate_cred_def_id']}]
    #             }
    #         },
    #         'requested_predicates': {
    #             'predicate1_referent': {
    #                 'name': 'salary',
    #                 'p_type': '>=',
    #                 'p_value': 2000,
    #                 'restrictions': [{'cred_def_id': acme['job_certificate_cred_def_id']}]
    #             },
    #             'predicate2_referent': {
    #                 'name': 'experience',
    #                 'p_type': '>=',
    #                 'p_value': 1,
    #                 'restrictions': [{'cred_def_id': acme['job_certificate_cred_def_id']}]
    #             }
    #         },
    #         'non_revoked': {'to': int(time.time())}
    #     })

    #     logger.info("\"Thrift\" -> Send \"Loan-Application-Basic\" Proof Request to Alice")
    #     alice['apply_loan_proof_request'] = thrift['apply_loan_proof_request']

    #     logger.info("\"Alice\" -> Get credentials for \"Loan-Application-Basic\" Proof Request")

    #     search_for_apply_loan_proof_request = \
    #         await anoncreds.prover_search_credentials_for_proof_req(alice['wallet'],
    #                                                                 alice['apply_loan_proof_request'], None)

    #     cred_for_attr1 = await get_credential_for_referent(search_for_apply_loan_proof_request, 'attr1_referent')
    #     cred_for_predicate1 = await get_credential_for_referent(search_for_apply_loan_proof_request,
    #                                                             'predicate1_referent')
    #     cred_for_predicate2 = await get_credential_for_referent(search_for_apply_loan_proof_request,
    #                                                             'predicate2_referent')

    #     await anoncreds.prover_close_credentials_search_for_proof_req(search_for_apply_loan_proof_request)

    #     alice['creds_for_apply_loan_proof'] = {cred_for_attr1['referent']: cred_for_attr1,
    #                                            cred_for_predicate1['referent']: cred_for_predicate1,
    #                                            cred_for_predicate2['referent']: cred_for_predicate2}

    #     requested_timestamp = int(json.loads(thrift['apply_loan_proof_request'])['non_revoked']['to'])
    #     alice['schemas_for_loan_app'], alice['cred_defs_for_loan_app'], alice['revoc_states_for_loan_app'] = \
    #         await prover_get_entities_from_ledger(alice['pool'], alice['did'],
    #                                               alice['creds_for_apply_loan_proof'],
    #                                               alice['name'], None, requested_timestamp)

    #     logger.info("\"Alice\" -> Create \"Loan-Application-Basic\" Proof")
    #     revoc_states_for_loan_app = json.loads(alice['revoc_states_for_loan_app'])
    #     timestamp_for_attr1 = get_timestamp_for_attribute(cred_for_attr1, revoc_states_for_loan_app)
    #     timestamp_for_predicate1 = get_timestamp_for_attribute(cred_for_predicate1, revoc_states_for_loan_app)
    #     timestamp_for_predicate2 = get_timestamp_for_attribute(cred_for_predicate2, revoc_states_for_loan_app)
    #     alice['apply_loan_requested_creds'] = json.dumps({
    #         'self_attested_attributes': {},
    #         'requested_attributes': {
    #             'attr1_referent': {'cred_id': cred_for_attr1['referent'], 'revealed': True,
    #                                'timestamp': timestamp_for_attr1}
    #         },
    #         'requested_predicates': {
    #             'predicate1_referent': {'cred_id': cred_for_predicate1['referent'],
    #                                     'timestamp': timestamp_for_predicate1},
    #             'predicate2_referent': {'cred_id': cred_for_predicate2['referent'],
    #                                     'timestamp': timestamp_for_predicate2}
    #         }
    #     })
    #     alice['apply_loan_proof'] = \
    #         await anoncreds.prover_create_proof(alice['wallet'], alice['apply_loan_proof_request'],
    #                                             alice['apply_loan_requested_creds'], alice['master_secret_id'],
    #                                             alice['schemas_for_loan_app'], alice['cred_defs_for_loan_app'],
    #                                             alice['revoc_states_for_loan_app'])

    #     logger.info("\"Alice\" -> Send \"Loan-Application-Basic\" Proof to Thrift")
    #     thrift['apply_loan_proof'] = alice['apply_loan_proof']
    #     apply_loan_proof_object = json.loads(thrift['apply_loan_proof'])

    #     logger.info("\"Thrift\" -> Get Schemas, Credential Definitions and Revocation Registries from Ledger"
    #                 " required for Proof verifying")

    #     thrift['schemas_for_loan_app'], thrift['cred_defs_for_loan_app'], thrift['revoc_defs_for_loan_app'], \
    #     thrift['revoc_regs_for_loan_app'] = \
    #         await verifier_get_entities_from_ledger(thrift['pool'], thrift['did'],
    #                                                 apply_loan_proof_object['identifiers'],
    #                                                 thrift['name'], requested_timestamp)

    #     logger.info("\"Thrift\" -> Verify \"Loan-Application-Basic\" Proof from Alice")
    #     assert 'Permanent' == \
    #            apply_loan_proof_object['requested_proof']['revealed_attrs']['attr1_referent']['raw']


    # await apply_loan_basic()

    # assert await anoncreds.verifier_verify_proof(thrift['apply_loan_proof_request'],
    #                                              thrift['apply_loan_proof'],
    #                                              thrift['schemas_for_loan_app'],
    #                                              thrift['cred_defs_for_loan_app'],
    #                                              thrift['revoc_defs_for_loan_app'],
    #                                              thrift['revoc_regs_for_loan_app'])

    # logger.info("==============================")
    # logger.info("== Apply for the loan with Thrift - Transcript and Job-Certificate proving  ==")
    # logger.info("------------------------------")

    # logger.info("\"Thrift\" -> Create \"Loan-Application-KYC\" Proof Request")
    # nonce = await anoncreds.generate_nonce()
    # thrift['apply_loan_kyc_proof_request'] = json.dumps({
    #     'nonce': nonce,
    #     'name': 'Loan-Application-KYC',
    #     'version': '0.1',
    #     'requested_attributes': {
    #         'attr1_referent': {'name': 'name'}
    #       
    #     },
    #     'requested_predicates': {}
    # })

    # logger.info("\"Thrift\" -> Send \"Loan-Application-KYC\" Proof Request to Alice")
    # alice['apply_loan_kyc_proof_request'] = thrift['apply_loan_kyc_proof_request']

    # logger.info("\"Alice\" -> Get credentials for \"Loan-Application-KYC\" Proof Request")

    # search_for_apply_loan_kyc_proof_request = \
    #     await anoncreds.prover_search_credentials_for_proof_req(alice['wallet'],
    #                                                             alice['apply_loan_kyc_proof_request'], None)

    # cred_for_attr1 = await get_credential_for_referent(search_for_apply_loan_kyc_proof_request, 'attr1_referent')
    # cred_for_attr2 = await get_credential_for_referent(search_for_apply_loan_kyc_proof_request, 'attr2_referent')
    # cred_for_attr3 = await get_credential_for_referent(search_for_apply_loan_kyc_proof_request, 'attr3_referent')

    # await anoncreds.prover_close_credentials_search_for_proof_req(search_for_apply_loan_kyc_proof_request)

    # alice['creds_for_apply_loan_kyc_proof'] = {cred_for_attr1['referent']: cred_for_attr1,
    #                                            cred_for_attr2['referent']: cred_for_attr2,
    #                                            cred_for_attr3['referent']: cred_for_attr3}

    # alice['schemas_for_loan_kyc_app'], alice['cred_defs_for_loan_kyc_app'], alice['revoc_states_for_loan_kyc_app'] = \
    #     await prover_get_entities_from_ledger(alice['pool'], alice['did'],
    #                                           alice['creds_for_apply_loan_kyc_proof'], alice['name'], )

    # logger.info("\"Alice\" -> Create \"Loan-Application-KYC\" Proof")
    # revoc_states_for_loan_app = json.loads(alice['revoc_states_for_loan_kyc_app'])
    # timestamp_for_attr1 = get_timestamp_for_attribute(cred_for_attr1, revoc_states_for_loan_app)
    # timestamp_for_attr2 = get_timestamp_for_attribute(cred_for_attr2, revoc_states_for_loan_app)
    # timestamp_for_attr3 = get_timestamp_for_attribute(cred_for_attr3, revoc_states_for_loan_app)
    # alice['apply_loan_kyc_requested_creds'] = json.dumps({
    #     'self_attested_attributes': {},
    #     'requested_attributes': {
    #         'attr1_referent': {'cred_id': cred_for_attr1['referent'], 'revealed': True,
    #                            'timestamp': timestamp_for_attr1},
    #         'attr2_referent': {'cred_id': cred_for_attr2['referent'], 'revealed': True,
    #                            'timestamp': timestamp_for_attr2},
    #         'attr3_referent': {'cred_id': cred_for_attr3['referent'], 'revealed': True,
    #                            'timestamp': timestamp_for_attr3}
    #     },
    #     'requested_predicates': {}
    # })

    # alice['apply_loan_kyc_proof'] = \
    #     await anoncreds.prover_create_proof(alice['wallet'], alice['apply_loan_kyc_proof_request'],
    #                                         alice['apply_loan_kyc_requested_creds'], alice['master_secret_id'],
    #                                         alice['schemas_for_loan_kyc_app'], alice['cred_defs_for_loan_kyc_app'],
    #                                         alice['revoc_states_for_loan_kyc_app'])

    # logger.info("\"Alice\" -> Send \"Loan-Application-KYC\" Proof to Thrift")
    # thrift['apply_loan_kyc_proof'] = alice['apply_loan_kyc_proof']
    # apply_loan_kyc_proof_object = json.loads(thrift['apply_loan_kyc_proof'])

    # logger.info("\"Thrift\" -> Get Schemas, Credential Definitions and Revocation Registries from Ledger"
    #             " required for Proof verifying")

    # thrift['schemas_for_loan_kyc_app'], thrift['cred_defs_for_loan_kyc_app'], thrift['revoc_defs_for_loan_kyc_app'], \
    # thrift['revoc_regs_for_loan_kyc_app'] = \
    #     await verifier_get_entities_from_ledger(thrift['pool'], thrift['did'],
    #                                             apply_loan_kyc_proof_object['identifiers'], thrift['name'])

    # logger.info("\"Thrift\" -> Verify \"Loan-Application-KYC\" Proof from Alice")
    # assert 'Alice' == \
    #        apply_loan_kyc_proof_object['requested_proof']['revealed_attrs']['attr1_referent']['raw']
    # assert 'Garcia' == \
    #        apply_loan_kyc_proof_object['requested_proof']['revealed_attrs']['attr2_referent']['raw']
    # assert '123-45-6789' == \
    #        apply_loan_kyc_proof_object['requested_proof']['revealed_attrs']['attr3_referent']['raw']

    # assert await anoncreds.verifier_verify_proof(thrift['apply_loan_kyc_proof_request'],
    #                                              thrift['apply_loan_kyc_proof'],
    #                                              thrift['schemas_for_loan_kyc_app'],
    #                                              thrift['cred_defs_for_loan_kyc_app'],
    #                                              thrift['revoc_defs_for_loan_kyc_app'],
    #                                              thrift['revoc_regs_for_loan_kyc_app'])

    # logger.info("==============================")

    # logger.info("==============================")
    # logger.info("== Credential revocation - Acme revokes Alice's Job-Certificate  ==")
    # logger.info("------------------------------")

    # logger.info("\"Acme\" - Revoke  credential")
    # acme['alice_cert_rev_reg_delta'] = \
    #     await anoncreds.issuer_revoke_credential(acme['wallet'],
    #                                              acme['blob_storage_reader_cfg_handle'],
    #                                              acme['revoc_reg_id'],
    #                                              acme['job_certificate_cred_rev_id'])

    # logger.info("\"Acme\" - Post RevocationRegistryDelta to Ledger")
    # acme['revoc_reg_entry_req'] = \
    #     await ledger.build_revoc_reg_entry_request(acme['did'], acme['revoc_reg_id'], 'CL_ACCUM',
    #                                                acme['alice_cert_rev_reg_delta'])
    # await ledger.sign_and_submit_request(acme['pool'], acme['wallet'], acme['did'], acme['revoc_reg_entry_req'])

    # logger.info("==============================")

    # logger.info("==============================")
    # logger.info("== Apply for the loan with Thrift again - Job-Certificate proving  ==")
    # logger.info("------------------------------")

    # await apply_loan_basic()

    # assert not await anoncreds.verifier_verify_proof(thrift['apply_loan_proof_request'],
    #                                                  thrift['apply_loan_proof'],
    #                                                  thrift['schemas_for_loan_app'],
    #                                                  thrift['cred_defs_for_loan_app'],
    #                                                  thrift['revoc_defs_for_loan_app'],
    #                                                  thrift['revoc_regs_for_loan_app'])

    logger.info("==============================")

    logger.info(" \"Sovrin Steward\" -> Close and Delete wallet")
    await wallet.close_wallet(steward['wallet'])
    await wallet.delete_wallet(steward['wallet_config'], steward['wallet_credentials'])

    logger.info("\"Government\" -> Close and Delete wallet")
    await wallet.close_wallet(government['wallet'])
    await wallet.delete_wallet(wallet_config("delete", government['wallet_config']),
                               wallet_credentials("delete", government['wallet_credentials']))

    logger.info("\"Toll Company\" -> Close and Delete wallet")
    await wallet.close_wallet(tollcompany['wallet'])
    await wallet.delete_wallet(wallet_config("delete", tollcompany['wallet_config']),
                               wallet_credentials("delete", tollcompany['wallet_credentials']))

    # logger.info("\"Acme\" -> Close and Delete wallet")
    # await wallet.close_wallet(acme['wallet'])
    # await wallet.delete_wallet(wallet_config("delete", acme['wallet_config']),
    #                            wallet_credentials("delete", acme['wallet_credentials']))

    # logger.info("\"Thrift\" -> Close and Delete wallet")
    # await wallet.close_wallet(thrift['wallet'])
    # await wallet.delete_wallet(wallet_config("delete", thrift['wallet_config']),
    #                            wallet_credentials("delete", thrift['wallet_credentials']))

    logger.info("\"RSU\" -> Close and Delete wallet")
    await wallet.close_wallet(rsu['wallet'])
    await wallet.delete_wallet(wallet_config("delete", rsu['wallet_config']),
                               wallet_credentials("delete", rsu['wallet_credentials']))

    logger.info("Close and Delete pool")
    await pool.close_pool_ledger(pool_['handle'])
    await pool.delete_pool_ledger_config(pool_['name'])

    logger.info("Getting started -> done")


def wallet_config(operation, wallet_config_str):
    if not args.storage_type:
        return wallet_config_str
    wallet_config_json = json.loads(wallet_config_str)
    wallet_config_json['storage_type'] = args.storage_type
    if args.config:
        wallet_config_json['storage_config'] = json.loads(args.config)
    # print(operation, json.dumps(wallet_config_json))
    return json.dumps(wallet_config_json)


def wallet_credentials(operation, wallet_credentials_str):
    if not args.storage_type:
        return wallet_credentials_str
    wallet_credentials_json = json.loads(wallet_credentials_str)
    if args.creds:
        wallet_credentials_json['storage_credentials'] = json.loads(args.creds)
    # print(operation, json.dumps(wallet_credentials_json))
    return json.dumps(wallet_credentials_json)


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


async def send_schema(pool_handle, wallet_handle, _did, schema):
    schema_request = await ledger.build_schema_request(_did, schema)
    schema_response = await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, schema_request)
    print("OK", 'Schema response: {}'.format(str(schema_response)))


async def send_cred_def(pool_handle, wallet_handle, _did, cred_def_json):
    cred_def_request = await ledger.build_cred_def_request(_did, cred_def_json)
    result = await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, cred_def_request)

async def get_schema(pool_handle, _did, schema_id):
    get_schema_request = await ledger.build_get_schema_request(_did, schema_id)
    get_schema_response = await ensure_previous_request_applied(
        pool_handle, get_schema_request, lambda response: response['result']['data'] is not None)
    return await ledger.parse_get_schema_response(get_schema_response)


async def get_cred_def(pool_handle, _did, cred_def_id):
    get_cred_def_request = await ledger.build_get_cred_def_request(_did, cred_def_id)
    get_cred_def_response = \
        await ensure_previous_request_applied(pool_handle, get_cred_def_request,
                                              lambda response: response['result']['data'] is not None)
    return await ledger.parse_get_cred_def_response(get_cred_def_response)


async def get_credential_for_referent(search_handle, referent):
    credentials = json.loads(
        await anoncreds.prover_fetch_credentials_for_proof_req(search_handle, referent, 10))
    return credentials[0]['cred_info']


def get_timestamp_for_attribute(cred_for_attribute, revoc_states):
    if cred_for_attribute['rev_reg_id'] in revoc_states:
        return int(next(iter(revoc_states[cred_for_attribute['rev_reg_id']])))
    else:
        return None


async def prover_get_entities_from_ledger(pool_handle, _did, identifiers, actor, timestamp_from=None,
                                          timestamp_to=None):
    schemas = {}
    cred_defs = {}
    rev_states = {}
    for item in identifiers.values():
        logger.info("\"{}\" -> Get Schema from Ledger".format(actor))
        (received_schema_id, received_schema) = await get_schema(pool_handle, _did, item['schema_id'])
        schemas[received_schema_id] = json.loads(received_schema)

        logger.info("\"{}\" -> Get Claim Definition from Ledger".format(actor))
        (received_cred_def_id, received_cred_def) = await get_cred_def(pool_handle, _did, item['cred_def_id'])
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


async def verifier_get_entities_from_ledger(pool_handle, _did, identifiers, actor, timestamp=None):
    schemas = {}
    cred_defs = {}
    rev_reg_defs = {}
    rev_regs = {}
    for item in identifiers:
        logger.info("\"{}\" -> Get Schema from Ledger".format(actor))
        (received_schema_id, received_schema) = await get_schema(pool_handle, _did, item['schema_id'])
        schemas[received_schema_id] = json.loads(received_schema)

        logger.info("\"{}\" -> Get Claim Definition from Ledger".format(actor))
        (received_cred_def_id, received_cred_def) = await get_cred_def(pool_handle, _did, item['cred_def_id'])
        cred_defs[received_cred_def_id] = json.loads(received_cred_def)

        if 'rev_reg_id' in item and item['rev_reg_id'] is not None:
            # Get Revocation Definitions and Revocation Registries
            logger.info("\"{}\" -> Get Revocation Definition from Ledger".format(actor))
            get_revoc_reg_def_request = await ledger.build_get_revoc_reg_def_request(_did, item['rev_reg_id'])

            get_revoc_reg_def_response = \
                await ensure_previous_request_applied(pool_handle, get_revoc_reg_def_request,
                                                      lambda response: response['result']['data'] is not None)
            (rev_reg_id, revoc_reg_def_json) = await ledger.parse_get_revoc_reg_def_response(get_revoc_reg_def_response)

            logger.info("\"{}\" -> Get Revocation Registry from Ledger".format(actor))
            if not timestamp: timestamp = item['timestamp']
            get_revoc_reg_request = \
                await ledger.build_get_revoc_reg_request(_did, item['rev_reg_id'], timestamp)
            get_revoc_reg_response = \
                await ensure_previous_request_applied(pool_handle, get_revoc_reg_request,
                                                      lambda response: response['result']['data'] is not None)
            (rev_reg_id, rev_reg_json, timestamp2) = await ledger.parse_get_revoc_reg_response(get_revoc_reg_response)

            rev_regs[rev_reg_id] = {timestamp2: json.loads(rev_reg_json)}
            rev_reg_defs[rev_reg_id] = json.loads(revoc_reg_def_json)

    return json.dumps(schemas), json.dumps(cred_defs), json.dumps(rev_reg_defs), json.dumps(rev_regs)


if __name__ == '__main__':
    run_coroutine(run)
    time.sleep(1)  # FIXME waiting for libindy thread complete
