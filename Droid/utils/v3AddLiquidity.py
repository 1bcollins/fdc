from web3 import Web3
import json
import time
import os
from dotenv import load_dotenv
import getMainNetGas
import approveToken
from web3.exceptions import ContractLogicError
import evmTxRaw
import asyncio

load_dotenv()

# Load environment variables
INFURA_URL = os.getenv("PROVIDER")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("ADDRESS")

# Initialize Web3 connection
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Uniswap V3 NonfungiblePositionManager contract details
NFT_POSITION_MANAGER_ADDRESS = web3.to_checksum_address("0xC36442b4a4522E871399CD717aBDD847Ab11FE88")  # Polygon Mainnet
NFT_POSITION_MANAGER_ABI = json.loads(open("NonfungiblePositionManagerABI.json").read())  # Load ABI

# Instantiate contract
position_manager = web3.eth.contract(address=NFT_POSITION_MANAGER_ADDRESS, abi=NFT_POSITION_MANAGER_ABI)

'''
# Approve tokens for spending
def approve_token(token_address, spender, amount):
    """Approve ERC-20 token transfer for Uniswap contract."""
    token_abi = json.loads(open("ERC20.json").read())  # Load ERC-20 ABI
    token_contract = web3.eth.contract(address=token_address, abi=token_abi)

    estimated_gas = token_contract.functions.approve(spender, amount).estimate_gas({"from": WALLET_ADDRESS})
    
    gasPriceGwei=getMainNetGas.getGasPrice() 
    gasPrice=int(gasPriceGwei * 1e9)
    print(f"gasPrice for Approve: {gasPriceGwei}")
    
    
    txn = token_contract.functions.approve(spender, amount).build_transaction({
        "from": WALLET_ADDRESS,
        "gas": int(estimated_gas*1.2) + 0,
        "gasPrice": gasPrice,
        "nonce": web3.eth.get_transaction_count(WALLET_ADDRESS),
    })
    
    signed_txn = web3.eth.account.sign_transaction(txn, PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print("Waiting for tx receipt!!")
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300, poll_latency=2.0)
    print(f"Approved {token_address} for spending. Txn Hash: {tx_hash.hex()}")
'''

# Increase liquidity in an existing NFT position
def increase_liquidityOLD(params, gas):
    """Increase liquidity for an existing NFT position."""
    addLiquError="unknown"
    
    '''
    gasPriceRange=getMainNetGas.getGasRange()
    gasPriceGwei=gasPriceRange[2]
    gasPrice=int(gasPriceGwei * 1e9)
    print(f"gasPrice for Add Liquidity: {gasPrice}")
    print()
    '''
    gasPriceGwei=getMainNetGas.getGasPrice() 
    gasPrice=int(gasPriceGwei * 1e9)
    print(f"gasPrice for Add Liquidity: {gasPriceGwei}")
    print()
    
    
    txn = position_manager.functions.increaseLiquidity(params).build_transaction({
        "from": WALLET_ADDRESS,
        "gas": int(1.2*gas),
        "gasPrice": gasPrice,	#int(1.13*web3.eth.gas_price),
        "nonce": web3.eth.get_transaction_count(WALLET_ADDRESS),
    })
    
    signed_txn = web3.eth.account.sign_transaction(txn, PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print("Waiting for tx receipt...")
    try:
    	receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=330, poll_latency=2.0)
    except:
    	receipt={"status": 0}
    
    
    if receipt.get("status") == 0:
        raise RuntimeError(f"Transaction failed! Txn Hash: {tx_hash.hex()}")
        addLiquError="fail"
    else:
        addLiquError="success"
        print(f"Liquidity increased successfully! Txn Hash: {tx_hash.hex()}")
    return tx_hash.hex(), addLiquError


def buildHexData(params, gas, priority=1, maxGasPrice=40):
	
	try:
		# Get gas price
		gasPriceGwei = getMainNetGas.getGasPrice(priority=priority, maxGasPrice=maxGasPrice)
		gasPrice = int(gasPriceGwei * 1e9)
		print(f"gasPrice for Add Liquidity: {gasPriceGwei} GWEI\n")

		# Build and sign transaction
		txn = position_manager.functions.increaseLiquidity(params).build_transaction({
			"from": WALLET_ADDRESS,
			"gas": int(1.2 * gas),
			"gasPrice": gasPrice,
			"nonce": web3.eth.get_transaction_count(WALLET_ADDRESS),
		})
		
	except Exception as e:
		print(f"❌ Error while building Hex Data: {str(e)}")
		return "error"
		

	return txn


def increase_liquidity(params, gas):
	"""Increase liquidity for an existing NFT position."""
	addLiquError = "unknown"
	tx_hash_hex = None

	try:
		# Get gas price
		gasPriceGwei = getMainNetGas.getGasPrice()
		gasPrice = int(gasPriceGwei * 1e9)
		print(f"gasPrice for Add Liquidity: {gasPriceGwei} GWEI\n")

		# Build and sign transaction
		txn = position_manager.functions.increaseLiquidity(params).build_transaction({
			"from": WALLET_ADDRESS,
			"gas": int(1.2 * gas),
			"gasPrice": gasPrice,
			"nonce": web3.eth.get_transaction_count(WALLET_ADDRESS),
		})

		signed_txn = web3.eth.account.sign_transaction(txn, PRIVATE_KEY)
		tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
		tx_hash_hex = tx_hash.hex()

		print("⏳ Waiting for tx receipt...")
		receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=330, poll_latency=2.0)

		if receipt.get("status") == 0:
			print(f"❌ Transaction failed! Txn Hash: {tx_hash_hex}")
			addLiquError = "fail"
		else:
			print(f"✅ Liquidity increased! Txn Hash: {tx_hash_hex}")
			addLiquError = "success"

	except Exception as e:
		print(f"❌ Error while increasing liquidity: {str(e)}")
		addLiquError = "exception"
		tx_hash_hex = tx_hash_hex or "0x0"

	return tx_hash_hex, addLiquError



# Estimate gas for increasing liquidity
def gas_estimateOLD(params):
    estimated_gas = position_manager.functions.increaseLiquidity(params).estimate_gas({"from": WALLET_ADDRESS})
    print(f"Estimated gas: {estimated_gas}")
    return estimated_gas


# Estimate gas with retry mechanism
def gas_estimate(params, max_retries=3, initial_delay=2):
    print()
    print("Estimating gas for add liquidity")
    print("params: ", params)
    print()
    
    attempt = 0
    while attempt < max_retries:
        try:
            estimated_gas = position_manager.functions.increaseLiquidity(params).estimate_gas({"from": WALLET_ADDRESS})
            print(f"Estimated gas: {estimated_gas}")
            return estimated_gas
        except ContractLogicError as e:
            #except as e:
            error_message = str(e)
            print(f"Gas estimation failed on attempt {attempt + 1}: {error_message}")
            
            if "execution reverted: STF" in error_message:
                delay = initial_delay * (2 ** attempt)  # Exponential backoff
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                attempt += 1
            else:
                raise  # If it's a different error, raise it immediately
    print("Max retries reached. Gas estimation failed.")
    return None  # Return None if all retries fail



# Format parameters for increaseLiquidity
def format_params(params):
    params_tuple = (
        params["tokenId"],
        params["amount0Desired"],
        params["amount1Desired"],
        params["amount0Min"],
        params["amount1Min"],
        int(time.time()) + 300  # Deadline (10 minutes from now)
    )
    return params_tuple

'''
def format_params(params):
	return ({
		"tokenId": int(params["tokenId"]),
		"amount0Desired": int(params["amount0Desired"]),
		"amount1Desired": int(params["amount1Desired"]),
		"amount0Min": int(params["amount0Min"]),
		"amount1Min": int(params["amount1Min"]),
		"deadline": int(time.time()) + 300
	},)
'''

# Increase liquidity entry point
def add_liquidity(params):
    #approve_token(params['token0'], NFT_POSITION_MANAGER_ADDRESS, params['amount0Desired'])
    #approve_token(params['token1'], NFT_POSITION_MANAGER_ADDRESS, params['amount1Desired'])
    apprRes0=approveToken.approve_token(params['token0'], NFT_POSITION_MANAGER_ADDRESS, params['amount0Desired'])
    apprRes1=approveToken.approve_token(params['token1'], NFT_POSITION_MANAGER_ADDRESS, params['amount1Desired'])	
    params_tuple = format_params(params)
    print("params_tuple: ", params_tuple)
    print()
    gas_est = gas_estimate(params_tuple)
    if (apprRes0=="approved" and apprRes1=="approved"): tx_hash, addLiquError = increase_liquidity(params_tuple, gas_est)
    return tx_hash, addLiquError


def addLiquFordefi(params, chain, priority=1, maxGasPrice=40):
    apprRes0=approveToken.approve_token(params['token0'], NFT_POSITION_MANAGER_ADDRESS, params['amount0Desired'])
    apprRes1=approveToken.approve_token(params['token1'], NFT_POSITION_MANAGER_ADDRESS, params['amount1Desired'])	
    params_tuple = format_params(params)
    print("params_tuple: ", params_tuple)
    print()
    gas_est = gas_estimate(params_tuple)
    if (apprRes0=="approved" and apprRes1=="approved"): #tx_hash, addLiquError = increase_liquidity(params_tuple, gas_est)
        txHexData=buildHexData(params_tuple, gas_est, priority, maxGasPrice)	
        if (txHexData!="error"):
        	print("txHexData: ", txHexData)
        	print()
        	tx_hash=asyncio.run(evmTxRaw.rawTx(txHexData['data'], NFT_POSITION_MANAGER_ADDRESS, chain))
        	if tx_hash : addLiquError="success"
        else:
        	tx_hash="error"
        	addLiquError="fail"
    return tx_hash, addLiquError

'''
example params:
params = {
    "tokenId": 12345,  # Existing NFT ID
    "token0": "0x...",  # Token 0 address
    "token1": "0x...",  # Token 1 address
    "amount0Desired": Web3.to_wei(1, "ether"),
    "amount1Desired": Web3.to_wei(500, "ether"),
    "amount0Min": Web3.to_wei(0.99, "ether"),
    "amount1Min": Web3.to_wei(490, "ether"),
}
tx_hash = add_liquidity(params)
'''



