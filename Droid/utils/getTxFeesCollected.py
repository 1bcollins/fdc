from web3 import Web3
import os
from dotenv import load_dotenv
#import getErc20Balance
load_dotenv()

INFURA_URL = os.getenv("PROVIDER")
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Event signatures
sig_decrease = "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c"
sig_transfer = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

POOL_ADDRESS="0x00"
TOKEN0_ADDRESS="0x00"

# Uniswap V3 pool minimal ABI (only the token0() function)
UNISWAP_V3_POOL_ABI = [
	{
		"inputs": [],
		"name": "token0",
		"outputs": [{"internalType": "address", "name": "", "type": "address"}],
		"stateMutability": "view",
		"type": "function"
	}
]

def get_token0_address(pool_address):
	"""
	Gets the token0 address of a Uniswap V3 pool.

	Args:
		pool_address (str): The Ethereum address of the Uniswap V3 pool.
		provider_url (str): An Ethereum RPC provider URL (e.g. Infura endpoint).

	Returns:
		str: The token0 address or None if something fails.
	"""
	try:
		pool = w3.eth.contract(address=Web3.to_checksum_address(pool_address), abi=UNISWAP_V3_POOL_ABI)
		token0 = pool.functions.token0().call()
		return token0
	except Exception as e:
		print(f"❌ Error: {e}")
		return None



def setPoolAddress(addr):
	global POOL_ADDRESS
	global TOKEN0_ADDRESS
	
	#print(f"calling setPoolAddress with {addr}")
	#print()
	POOL_ADDRESS=addr
	TOKEN0_ADDRESS=get_token0_address(POOL_ADDRESS)


def getV3Fees(tx_hash: str):
	removed0 = removed1 = 0
	collected0 = collected1 = 0
	transfer_events = []
	receipt = w3.eth.get_transaction_receipt(tx_hash)
	
	
	'''
	print(tx_hash)
	print()	
	print(receipt)
	print()
	'''
	
	for log in receipt['logs']:
		#print(log)
		#print()
		
		topic0 = log['topics'][0].hex()
		
		#print(topic0)
		#print()
		
		if(topic0[0:2]!="0x"): topic0="0x" + topic0
		#print(topic0)
		#print()

		if topic0 == sig_decrease:
			#print("Decrease found")
			#print()
			setPoolAddress(log['address'])
			
			hex_data = log['data'].hex()
			if(hex_data[0:2]!="0x"): hex_data="0x" + hex_data
			amount0 = int(hex_data[66:130], 16)
			amount1 = int(hex_data[130:194], 16)
			removed0 += amount0
			removed1 += amount1
			#print(removed0)
			#print(removed1)
			#print()

		elif topic0 == sig_transfer:
			#print("transfer found")
			#print()
			token_address = log['address']
			#print(token_address)
			#print()
			hex_data = log['data'].hex()
			if(hex_data[0:2]!="0x"): hex_data="0x" + hex_data
			#print(hex_data)
			#print()
			amount = int(hex_data, 16)
			transfer_events.append((token_address, amount))
			#print(amount)

	if len(transfer_events) >= 2:
		#print(transfer_events)
		#print()
		collected0 = transfer_events[0][1]
		collected1 = transfer_events[1][1]
		t0=transfer_events[0][0]
		t1=transfer_events[1][0]
	else:
		if transfer_events[0][0]==TOKEN0_ADDRESS:
			collected0 = transfer_events[0][1] 
		else:
			collected1 = transfer_events[0][1] 
	#	collected1 = transfer_events[0][1]		
	#	t0=transfer_events[0][0]
	#	t1=transfer_events[0][0]

	#print(transfer_events)
	#print()
	#print(transfer_events[0][0])
	#print()
	
	fee0 = collected0 - removed0
	fee1 = collected1 - removed1
	if(fee0<0): 
		fee0=0
		collected0=removed0
	if(fee1<0): 
		fee1=0
		collected1=removed1
	
	#print(t0, t1)
	#print()
	#getErc20Balance.fixDecimals(token_address, amountWei)
	
	'''
	return {
		"fee0": fee0,
		"fee1": fee1,
		"collected0": collected0,
		"collected1": collected1,
		"removed0": removed0,
		"removed1": removed1
	}
	'''
	#print(removed0, removed1)
	#print()
	
	'''
	fee0=getErc20Balance.fixDecimals(t0, fee0) if fee0>0 else 0
	fee1=getErc20Balance.fixDecimals(t1, fee1) if fee1>0 else 0
	collected0=getErc20Balance.fixDecimals(t0, collected0) if collected0>0 else 0
	collected1=getErc20Balance.fixDecimals(t1, collected1) if collected1>0 else 0
	removed0=getErc20Balance.fixDecimals(t0, removed0) if removed0>0 else 0
	removed1=getErc20Balance.fixDecimals(t1, removed1) if removed1>0 else 0
	'''
	'''
	return {
		"fee0": getErc20Balance.fixDecimals(t0, fee0),		#fee0,
		"fee1": getErc20Balance.fixDecimals(t1, fee1),		#fee1,
		"collected0": getErc20Balance.fixDecimals(t0, collected0),		#collected0,
		"collected1": getErc20Balance.fixDecimals(t1, collected1),		#collected1,
		"removed0": getErc20Balance.fixDecimals(t0, removed0),		#removed0,
		"removed1": getErc20Balance.fixDecimals(t1, removed1)		#removed1
	}	
	
	'''
	#print(POOL_ADDRESS)
	#print()
	#print(TOKEN0_ADDRESS)
	#print()
	
	return {
		"fee0": fee0,
		"fee1": fee1,
		"collected0": collected0,
		"collected1": collected1,
		"removed0": removed0,
		"removed1": removed1
	}
	
	
	
if __name__ == "__main__":
	txHash=input("TX HASH? : ")
	res=getV3Fees(txHash)
	print(res)
	
	
	
