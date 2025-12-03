from web3 import Web3
import json
import time
import os
import getMainNetGas
from dotenv import load_dotenv
from web3.exceptions import ContractLogicError
import evmTxRaw
load_dotenv()
import asyncio

# Load environment variables
INFURA_URL = os.getenv("PROVIDER")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("ADDRESS")



# Initialize Web3 connection (replace with your RPC provider)
#RPC_URL = "https://polygon-mainnet.infura.io/v3/YOUR_INFURA_API_KEY"
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Your wallet details
#PRIVATE_KEY = "YOUR_PRIVATE_KEY"
#WALLET_ADDRESS = web3.to_checksum_address("YOUR_WALLET_ADDRESS")

# Uniswap V3 NonfungiblePositionManager contract details
NFT_POSITION_MANAGER_ADDRESS = web3.to_checksum_address("0xC36442b4a4522E871399CD717aBDD847Ab11FE88")  # Polygon Mainnet
NFT_POSITION_MANAGER_ABI = json.loads(open("NonfungiblePositionManagerABI.json").read())  # Load ABI

# Instantiate contract
position_manager = web3.eth.contract(address=NFT_POSITION_MANAGER_ADDRESS, abi=NFT_POSITION_MANAGER_ABI)

'''
# Tokens (Replace with actual token contract addresses)
TOKEN0 = web3.to_checksum_address("0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063")  # Example: DAI
TOKEN1 = web3.to_checksum_address("0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619")  # Example: WETH

# Fee tier (3000 = 0.3% pool)
POOL_FEE = 3000

# Price range in tick format (determine from Uniswap docs)
TICK_LOWER = -887220  # Example tick value
TICK_UPPER = 887220

# Amounts to provide as liquidity
AMOUNT0_DESIRED = Web3.to_wei(10, 'ether')  # 10 DAI
AMOUNT1_DESIRED = Web3.to_wei(0.01, 'ether')  # 0.01 WETH
'''

def check_allowance(token_address, spender):
	
	token_abi = json.loads(open("ERC20.json").read())  
	token_contract = web3.eth.contract(address=token_address, abi=token_abi)

	allowance = token_contract.functions.allowance(WALLET_ADDRESS, spender).call()
	balance = token_contract.functions.balanceOf(WALLET_ADDRESS).call()

	print(f"Allowance: {allowance}, Balance: {balance}")

	return allowance, balance


def estimateApproveGas(token_address, spender, amount):
	"""Approve ERC-20 token transfer for Uniswap contract."""
	token_abi = json.loads(open("ERC20.json").read())  # Load ERC-20 ABI
	token_contract = web3.eth.contract(address=token_address, abi=token_abi)
	
	print("approve_token data: ", token_address, spender, amount)
	try:
		estimated_gas = token_contract.functions.approve(spender, amount).estimate_gas({
			"from": WALLET_ADDRESS
		})
	except Exception as e:
		print(f"Error in estimateApproveGas function: {e}")
		estimated_gas = token_contract.functions.approve(spender, amount).estimate_gas({
			"from": WALLET_ADDRESS
		})		
		
	return estimated_gas

# Approve tokens for spending
def approve_token(token_address, spender, amount):
	apprError=True
	res="error"
	allowance, balance=check_allowance(token_address, spender)
	if balance<amount:
		print()
		print("INSUFFICIENT FUNDS FOR APPROVE TOKEN!")
		print()
		#return res
	if allowance==0:
		apprError=_approveToken(token_address, spender, amount)
	if allowance>=amount:
		res="approved"
		return res
	if allowance<amount:
		apprError=_approveToken(token_address, spender, 0)	#set allowance to zero
		apprError=_approveToken(token_address, spender, amount)	#set allowance to 'amount'
		res="error" if apprError else "approved"
		
	return res
	
	
def _approveToken(token_address, spender, amount):
	error=True
	#helper fuction. see entry at "approve_token" func'
	"""Approve ERC-20 token transfer for Uniswap contract."""
	token_abi = json.loads(open("ERC20.json").read())  # Load ERC-20 ABI
	token_contract = web3.eth.contract(address=token_address, abi=token_abi)
	
	print("approve_token data: ", token_address, spender, amount)
	
	estimated_gas =estimateApproveGas(token_address, spender, amount)
	
	
	gasPriceGwei=getMainNetGas.getGasPrice() 
	gasPrice=int(gasPriceGwei * 1e9)
	print(f"gasPrice for Approve: {gasPriceGwei}")

	# Build transaction
	txn = token_contract.functions.approve(spender, amount).build_transaction({
		"from": WALLET_ADDRESS,
		"gas": int(estimated_gas*1.2) + 0,
		"gasPrice": gasPrice,
		"nonce": web3.eth.get_transaction_count(WALLET_ADDRESS),
	})

	# Sign and send transaction
	signed_txn = web3.eth.account.sign_transaction(txn, PRIVATE_KEY)
	tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
	#web3.eth.wait_for_transaction_receipt(tx_hash)
	try:
		print("waiting for tx reciept")
		receipt = web3.eth.wait_for_transaction_receipt(
			tx_hash, timeout=330, poll_latency=2.0
		)
		print(f"Transaction confirmed: {receipt}")
		error=False
	except Exception as e:
		print(f"Error while waiting for transaction receipt: {e}")
		error=True
	
	print(f"Approved {token_address} for spending. Txn Hash: {tx_hash.hex()}")
	return error
	
# Mint a new liquidity position
def mint_position(params, gas):
    print("calling mint_position()")
    """Mint an NFT liquidity position on Uniswap V3."""
    '''
    gasPriceRange=getMainNetGas.getGasRange()
    gasPriceGwei=gasPriceRange[2]
    gasPrice=int(gasPriceGwei * 1e9)
    print(f"gasPrice for Mint: {gasPrice}")
    print()
    '''
    gasPriceGwei=getMainNetGas.getGasPrice() 
    gasPrice=int(gasPriceGwei * 1e9)
    print(f"gasPrice for Mint: {gasPriceGwei}")

    # Build transaction
    txn = position_manager.functions.mint(params).build_transaction({
        "from": WALLET_ADDRESS,
        "gas": gas + 0,
        "gasPrice": gasPrice, #web3.eth.gas_price,
        "nonce": web3.eth.get_transaction_count(WALLET_ADDRESS),
    })

    # Sign and send transaction
    signed_txn = web3.eth.account.sign_transaction(txn, PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

    try:
        print("Waiting for transaction receipt...")
        receipt = web3.eth.wait_for_transaction_receipt(
            tx_hash, timeout=330, poll_latency=2.0
        )
        print(f"Transaction receipt received: {receipt}")

        # Check transaction status
        if receipt.get("status") == 0:
            raise RuntimeError(f"Transaction failed! Txn Hash: {tx_hash.hex()}")

    except Exception as e:
        print(f"Error while waiting for transaction receipt: {e}")
        return "error"

    print(f"Liquidity position minted successfully! Txn Hash: {tx_hash.hex()}")
    return tx_hash.hex()


def gasEstimate(params):
	max_retries = 3  # Number of retries after initial attempt
	retry_delay = 10  # Seconds to wait before retrying

	for attempt in range(max_retries + 1):
		try:
			estimated_gas = position_manager.functions.mint(params).estimate_gas({
					"from": WALLET_ADDRESS
			})
			print(f"Estimated gas: {estimated_gas}")
			return int(estimated_gas*1.2)

		except ContractLogicError as e:
			print(f"Attempt {attempt + 1} failed with revert reason: {e}")
			print(f"Raw data: {e.data}")
			if attempt < max_retries:
				print(f"Waiting {retry_delay} seconds before retrying...")
				time.sleep(retry_delay)
			else:
				print()
				print("Max retries reached. Giving up.")
				print("params: ", params)
				print()
				raise  # Re-raise the exception after exhausting retries
	
	return 0

def formatParams(params):
	params_tuple = (
		params["token0"],
		params["token1"],
		params["fee"],
		params["tickLower"],
		params["tickUpper"],
		params["amount0Desired"],
		params["amount1Desired"],
		params["amount0Min"],
		params["amount1Min"],
		params["recipient"],
		params["deadline"]
	)
	return params_tuple

#mint Entry
def mint(params):
	# Approve tokens
	apprRes0=approve_token(params['token0'], NFT_POSITION_MANAGER_ADDRESS, params['amount0Desired'])
	apprRes1=approve_token(params['token1'], NFT_POSITION_MANAGER_ADDRESS, params['amount1Desired'])	
	time.sleep(10)#!!!!!!!!! ADD delay for block sync !!!!!!!!!!!!!
	params_tuple=formatParams(params)
	gasEst=gasEstimate(params_tuple)
	txHash="error"
	if (apprRes0=="approved" and apprRes1=="approved" and gasEst!=0): txHash=mint_position(params_tuple, gasEst)
	#txHash=mint_position(params_tuple, gasEst)
	return txHash

def buildHexData(params, gas):
    print("calling buildHexData()")
    
    gasPriceGwei = getMainNetGas.getGasPrice() 
    gasPrice = int(gasPriceGwei * 1e9)
    print(f"gasPrice for Mint: {gasPriceGwei}")

    # Build the transaction (but don't sign or send it)
    txn = position_manager.functions.mint(params).build_transaction({
        "from": WALLET_ADDRESS,
        "gas": gas,
        "gasPrice": gasPrice,
        "nonce": web3.eth.get_transaction_count(WALLET_ADDRESS),
    })

    # Encode to hex for Fordefi
    #hex_data = web3.eth.account.sign_transaction(txn, b'\x00'*32).raw_transaction.hex()  
    # ^ Using dummy key so we can grab encoded structure without actually signing

    # Remove "0x" if Fordefi expects pure hex
    #if hex_data.startswith("0x"):
    #    hex_data = hex_data[2:]
    
    '''
    # Send asynchronously to Fordefi
    asyncio.run(send_to_fordefi(
        chain=f"evm_{evm_chain}_mainnet",
        vault_id=EVM_VAULT_ID,
        to=NFT_POSITION_MANAGER_ADDRESS,
        hex_data=hex_data,
        value=str(txn.get("value", 0))
    ))
    '''
    return txn


def mintFordefi(params, chain):
	# Approve tokens
	apprRes0=approve_token(params['token0'], NFT_POSITION_MANAGER_ADDRESS, params['amount0Desired'])
	apprRes1=approve_token(params['token1'], NFT_POSITION_MANAGER_ADDRESS, params['amount1Desired'])	
	time.sleep(10)#!!!!!!!!! ADD delay for block sync !!!!!!!!!!!!!
	params_tuple=formatParams(params)
	gasEst=gasEstimate(params_tuple)
	txHash="error"
	if (apprRes0=="approved" and apprRes1=="approved" and gasEst!=0): hexData=buildHexData(params_tuple, gasEst)
	#print("hexData: ", hexData)
	#print("hexData['data']: ", hexData['data'])
	#print()
	txHash=asyncio.run(evmTxRaw.rawTx(hexData['data'], NFT_POSITION_MANAGER_ADDRESS, chain))
	#print("end mintFordefi() call")
	#print()
	return txHash

if __name__ == "__main__":
	token_address=input("Token address: ")	#0xdAC17F958D2ee523a2206206994597C13D831ec7"
	#token_address=token_address.lower()
	spender="0xC36442b4a4522E871399CD717aBDD847Ab11FE88"
	amount= int(input("Amount to approve in wei: "))	#402840710
	
	allowance, balance=check_allowance(token_address, spender)
	print("Allowance: ", allowance)
	print("Balance: ", balance)
	getEst=input("Get Gas est. ? (y/n)")
	if getEst=="y":
		gasEstimate=estimateApproveGas(token_address, spender, amount)
		print(gasEstimate)
	
	appr=input("Call approve (y/n): ")
	if appr=="y":
		approve_token(token_address, spender, amount)

'''
params={'token0': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', 'token1': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F', 'fee': 500, 'tickLower': -288680, 'tickUpper': -287700, 'amount0Desired': 1091140000000000131072, 'amount1Desired': 350000000, 'amount0Min': 0, 'amount1Min': 0, 'recipient': '0x7BF2bd6B212Ad91A5B4686fC1e504CC708461C0e', 'deadline': 1740066926}
'''

'''
# Check if wallet has enough token balance
token0_contract = web3.eth.contract(address=params["token0"], abi=json.loads(open("ERC20.json").read()))
token1_contract = web3.eth.contract(address=params["token1"], abi=json.loads(open("ERC20.json").read()))

balance0 = token0_contract.functions.balanceOf(WALLET_ADDRESS).call()
balance1 = token1_contract.functions.balanceOf(WALLET_ADDRESS).call()

print(f"Token0 Balance: {balance0}, Required: {params['amount0Desired']}")
print(f"Token1 Balance: {balance1}, Required: {params['amount1Desired']}")
'''
#print(params['token0'])






# Mint the NFT position
#txHash=mint_position(params_tuple, gasEst)

