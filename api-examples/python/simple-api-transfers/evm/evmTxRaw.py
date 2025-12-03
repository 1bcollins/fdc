import os
import json
import asyncio
import datetime
from utils.broadcast import broadcast_tx
from utils.sign_payload import sign
from dotenv import load_dotenv

load_dotenv()


async def evm_tx_raw(vault_id: str, chain: str, to: str, hex_data: str, value: str = "0"):
    request_json = {
        "vault_id": vault_id,
        "signer_type": "api_signer",
        "type": "evm_transaction",
        "details": {
            "type": "evm_raw_transaction",
            "chain": chain,  # e.g. "ethereum_mainnet" or "polygon_mainnet"
            "to": to,
            "value": value,
            "data": {
                "type": "hex",
                "hex_data": hex_data
            }
        }
    }
    return request_json





async def evm_tx_native(evm_chain: str, vault_id: str, destination: str, custom_note: str, value: str):
    request_json = {
        "signer_type": "api_signer",
        "vault_id": vault_id,
        "note": custom_note,
        "type": "evm_transaction",
        "details": {
            "type": "evm_transfer",
            "gas": {
                "type": "priority",
                "priority_level": "medium"
            },
            "to": destination,
            "asset_identifier": {
                "type": "evm",
                "details": {
                    "type": "native",
                    "chain": f"evm_{evm_chain}_mainnet"
                }
            },
            "value": {
                "type": "value",
                "value": value
            }
        }
    }
    
    return request_json

## Fordefi configuration
USER_API_TOKEN = os.getenv("FORDEFI_API_TOKEN")
print("USER_API_TOKEN: ", USER_API_TOKEN)
EVM_VAULT_ID = os.getenv("EVM_VAULT_ID")
print("EVM_VAULT_ID: ", EVM_VAULT_ID)
evm_chain = "polygon"
path = "/api/v1/transactions" # CHANGE
destination = "0x8E60A6b5A1D139e9baEFBB33bF135a7f3dE4aDc9" # CHANGE to your EVM address
custom_note = "jello!" # Optional note
value = str(5_000_000_000_000_000_000) # 0.00001 BNB (1 BNB = 0.000000000000000001 wei)

async def evmTxNative():
    try:
        ## Building transaction
        request_json = await evm_tx_native(evm_chain=evm_chain, vault_id=EVM_VAULT_ID, destination=destination, custom_note=custom_note, value=value)
        request_body = json.dumps(request_json)
        timestamp = datetime.datetime.now().strftime("%s")
        payload = f"{path}|{timestamp}|{request_body}"
        ## Signing transaction with API Signer
        signature = await sign(payload=payload)
        ## Broadcasting tx
        await broadcast_tx(path, USER_API_TOKEN, signature, timestamp, request_body)
        print("✅ Transaction submitted successfully!")
    except Exception as e:
        print(f"❌ Transaction failed: {str(e)}")

async def rawTx(hexData, _to):
    try:
        request_json = await evm_tx_raw(
            vault_id=EVM_VAULT_ID,
            chain="ethereum_mainnet",  # or polygon_mainnet
            to=_to, 	#"0x565697B5DD1F7Bdc61f774807057D058E5A27cbC",
            hex_data=hexData,	#"0x0d1d7ae50000000000000000000000000000000000000000000000000000000000000006",
            value="0"
        )
        request_body = json.dumps(request_json)
        timestamp = datetime.datetime.now().strftime("%s")
        payload = f"{path}|{timestamp}|{request_body}"
        signature = await sign(payload=payload)
        await broadcast_tx(path, USER_API_TOKEN, signature, timestamp, request_body)
        print("✅ Raw transaction submitted successfully!")
    except Exception as e:
        print(f"❌ Transaction failed: {str(e)}")



if __name__ == "__main__":
    #asyncio.run(main())
    asyncio.run(evmTxNative())
    #hexData="0x0d1d7ae50000000000000000000000000000000000000000000000000000000000000006"
    #to="0x565697B5DD1F7Bdc61f774807057D058E5A27cbC"
    #asyncio.run(rawTx(hexData, to))
    
    
