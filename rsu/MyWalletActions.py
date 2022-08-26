
import json, asyncio

from indy import pool, ledger, wallet, did, crypto
from indy.error import IndyError, ErrorCode

wallet_config = json.dumps({"id": "wallet"})
wallet_credentials = json.dumps({"key": "wallet_key"})
walletHandle = ""

def print_log(type="DEBUG", value_color="", value_noncolor=""):
        """set the colors for text."""
        HEADER = '\033[92m'
        ENDC = '\033[0m'
        if type == "ERROR" :
            HEADER = '\u001B[31m'
        if type == "WARNING" :
            HEADER = '\033[93m'
        if type == "DEBUG" :
            HEADER = '\033[92m'
        print(HEADER + value_color + ENDC + str(value_noncolor))


async def encrypt_message(walletHandle, myVerkey, verkey_client, response):
    encrypted_response = await crypto.auth_crypt(walletHandle, myVerkey, verkey_client, response)
    return encrypted_response

def set_walletHandle(wh):
    walletHandle = wh
        
async def createWallet():
    try:
        print_log("DEBUG" , 'Creating wallet')
        try:
            await wallet.create_wallet(wallet_config, wallet_credentials)
            wh = await wallet.open_wallet(wallet_config, wallet_credentials)
            set_walletHandle(wh)
        except IndyError as ex:
            if ex.error_code == ErrorCode.WalletAlreadyExistsError:
                pass
    except IndyError as e:
        print('Error occurred: %s' % e)

async def createNewContextKeys(walletHandle, myDid, myVerkey):
    try:
        print_log("DEBUG" , 'Opening wallet and creating new did/verkey pair')
        myDid, myVerkey =  await did.create_and_store_my_did(walletHandle, "{}")
        print_log("DEBUG" , ("MY DID: {} MY VERKEY: {} ").format(myDid, myVerkey))

        return myDid, myVerkey
    except IndyError as e:
        print('Error occurred: %s' % e)


def main():
    pass
    # loop1 = asyncio.get_event_loop()
    # createWallet_task = loop1.create_task(myWalletInit.createWallet())
    # loop1.run_until_complete(createWallet_task)
    # loop1.close()
    
    # loop2 = asyncio.new_event_loop()
    # openWallet_task = loop2.create_task(myWalletInit.createNewContextKeys())
    # loop2.run_until_complete(openWallet_task)
    # loop2.close()

if __name__ == "__main__":
    
    main()
