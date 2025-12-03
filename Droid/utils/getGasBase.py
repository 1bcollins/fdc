from web3 import Web3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
INFURA_URL = os.getenv("PROVIDER")  

def getGasBase():
	web3 = Web3(Web3.HTTPProvider(INFURA_URL))

	latest_block = web3.eth.get_block("latest")
	base_fee_per_gas = latest_block["baseFeePerGas"]
	#print(f"Base Fee (wei): {base_fee_per_gas}")
	#print(f"Base Fee (gwei): {web3.from_wei(base_fee_per_gas, 'gwei')}")
	
	return base_fee_per_gas, web3.from_wei(base_fee_per_gas, 'gwei')
	
if __name__ == "__main__":
	wei, gwei=getGasBase()
	print(wei)
	print(gwei)

