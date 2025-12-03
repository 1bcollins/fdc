import os
import json
import asyncio
import datetime
import get_quoteErc20
from pathlib import Path
from sign_payload import sign
from dotenv import load_dotenv
from broadcast import broadcast_tx
from submit_quoteErc20 import submit_quote
from get_provider_list import getSwapProviders 
from get_quote import get_quote, get_best_quote

load_dotenv()

## CONFIG
FORDEFI_API_TOKEN = os.getenv("FORDEFI_API_TOKEN")
EVM_VAULT_ID = os.getenv("EVM_VAULT_ID")
PRIVATE_KEY_PEM_FILE = Path("private.pem")
path = "/api/v1/swaps"



sell_token_amount = str(1000000000000000) # in smallest unit, 1 ETH = 1000000000000000000 wei
buy_token_address = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48" # USDC on Ethereum
chain_type =  "evm"
network =  "evm_ethereum_mainnet"
slippage = "500" # in bps

async def swap(quoteId, sell_token_amount, buy_token_address, providerId, slippage, sell_token_address):
    print("calling swap")
    print()
    try:
        tx_payload = submit_quote(
            quote_id=quoteId,
            vault_id=EVM_VAULT_ID, 
            chain_type=chain_type, 
            network=network, 
            sell_token_amount=sell_token_amount, 
            buy_token_address=buy_token_address, 
            providers=providerId,
            slippage=slippage,
            sell_token_address=sell_token_address)
        
        tx_payload_json = json.dumps(tx_payload) 
        timestamp = datetime.datetime.now().strftime("%s")
        payload = f"{path}|{timestamp}|{tx_payload_json}"
        
        print("payload: ", payload)
        print()

        ## Signing transaction payload with API User's private key  
        signature = await sign(payload=payload, private_key_path=PRIVATE_KEY_PEM_FILE)

        ## Sending transaction to Fordefi for MPC signature and broadcast
        resp_tx = await broadcast_tx(path, FORDEFI_API_TOKEN, signature, timestamp, tx_payload_json)
        print("resp_tx: ", resp_tx)
        print("✅ Transaction submitted successfully!")
        print()
    except Exception as e:
        print(f"❌ Transaction failed: {str(e)}")

if __name__ == "__main__":
	providers=getSwapProviders("evm", FORDEFI_API_TOKEN)
	buy_token_address="0xdAC17F958D2ee523a2206206994597C13D831ec7" #USDT
	sell_token_address="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"	#WETH
	sell_token_amount="10000000000000000"	# 10000000000000000 =.01 eth =~$40
	slippage="100"	#0000000000000"
	print("providers: ", providers)
	print("providers[1]: ", providers[1])
	filtered = get_quoteErc20.remove_uniswap_x(providers)
	quotes=get_quoteErc20.get_quote(EVM_VAULT_ID, "evm", "ethereum_mainnet",  sell_token_amount, buy_token_address, filtered, slippage, FORDEFI_API_TOKEN, sell_token_address)
	
	quoteId="none"	#default 
	
	print("quotes: ", quotes)
	print()
	for q in quotes['providers_with_quote']:
		print(q['quote'])
		if (q['quote']): 
			#print("quote ID: ", q['quote']['quote_id'])	#<-isolated quote ID
			if(q['quote']['provider_info']['provider_id']=='one_inch_fusion'):
				print("One inch found")
				quoteId=q['quote']['quote_id']
				providerId=q['quote']['provider_info']['provider_id']
				print("quote ID: ", quoteId)
				print("providerId: ", providerId)
			
		print()
	
	if(quoteId!="none"):
		print("call swap function here!")	
		asyncio.run(swap(quoteId, sell_token_amount, buy_token_address, providerId, slippage, sell_token_address))
	else:
		print("no provider available!")
	
	
	
	
	
	
	
	
	
	
