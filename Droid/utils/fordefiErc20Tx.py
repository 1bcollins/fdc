import os
import json
import asyncio
import datetime
import json
import monitorFordefiTxId
import getErc20Balance
from fordefiUtils.broadcast import broadcast_tx
from fordefiUtils.sign_payload import sign
from dotenv import load_dotenv
from fordefiUtils import fordefiGetApi
load_dotenv()

# Load Fordefi config
USER_API_TOKEN = os.getenv("FORDEFI_API_TOKEN")
#EVM_VAULT_ID = os.getenv("EVM_VAULT_ID")
evm_chain = "ethereum"
path = "/api/v1/transactions"



async def evm_tx_tokens(evm_chain: str, vault_id: str, destination: str, custom_note: str, value: str, token_contract: str):
    """Builds the JSON for an ERC20 transfer transaction request."""
    return {
        "signer_type": "api_signer",
        "type": "evm_transaction",
        "details": {
            "type": "evm_transfer",
            "gas": {
                "type": "priority",
                "priority_level": "medium"
            },
            "to": destination,
            "value": {
                "type": "value",
                "value": value
            },
            "asset_identifier": {
                "type": "evm",
                "details": {
                    "type": "erc20",
                    "token": {
                        "chain": f"evm_{evm_chain}_mainnet",
                        "hex_repr": token_contract
                    }
                }
            }
        },
        "note": custom_note,
        "vault_id": vault_id
    }


async def send_token_tx(destination: str, custom_note: str, token_contract_address: str, value: str, vault: str):
    """
    Creates, signs, and broadcasts an ERC20 transfer via Fordefi API.

    Args:
        destination (str): Recipient address
        custom_note (str): Optional note for the transaction
        token_contract_address (str): ERC20 token contract
        value (str): Token amount in smallest units (respecting token decimals)
    """
    try:
        # Build transaction
        request_json = await evm_tx_tokens(
            evm_chain=evm_chain,
            vault_id=vault,
            destination=destination,
            custom_note=custom_note,
            value=value,
            token_contract=token_contract_address
        )

        request_body = json.dumps(request_json)
        timestamp = datetime.datetime.now().strftime("%s")
        payload = f"{path}|{timestamp}|{request_body}"

        # Sign transaction
        signature = await sign(payload=payload)

        # Broadcast transaction
        resp_tx=await broadcast_tx(path, USER_API_TOKEN, signature, timestamp, request_body)
        print("✅ Transaction submitted successfully!")

    except Exception as e:
        print(f"❌ Transaction failed: {str(e)}")
        return "fail"

    respJson= resp_tx.json()
    print("respJson['id']: ", respJson['id'])
    txId=respJson['id']
    print("txId: ", txId)
    print()
    txIdData=monitorFordefiTxId.monitor_transaction(txId, 5,)	
    txHash=txIdData['hash']
    print("txHash: ", txHash)
    print()
    #TODO: ADD CHECK HERE txIdData FOR errors or failures !!!!!!!!!!!!!!!
    return txHash

def sendTokenTx(destination: str, custom_note: str, token_contract_address: str, value: str, vault: str):
	#add check here to check if token amount is available from vault
	#steps:
	#get vault evm address
	vault_info = fordefiGetApi.get_vault(vault)
	vaultEvmAddr=vault_info['address']
	#get amount available from token_contract_address
	amountAvail=getErc20Balance.get_erc20_balance_wei(token_contract_address, vaultEvmAddr)
	#compare available to "value"
	#IF "avail"<"value" THEN return "fail" ("error")
	if (int(amountAvail)<int(value)): 
		print("insufficient funds for transfer!")
		print()
		return "fail"
	
	txHash=asyncio.run(send_token_tx(destination, custom_note, token_contract_address, value, vault))
	return txHash
	
	
	
