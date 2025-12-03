import os
import json
from web3 import Web3
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
import getMainNetGas
import asyncio
import evmTxRaw

load_dotenv()

# Load environment variables
INFURA_URL = os.getenv("PROVIDER")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("ADDRESS")

# Connect to Ethereum network
web3 = Web3(Web3.HTTPProvider(INFURA_URL))
assert web3.is_connected(), "Could not connect to Ethereum network"

# Load ABI from a separate file
with open("NonfungiblePositionManagerABI.json", "r") as abi_file:
    NONFUNGIBLE_POSITION_MANAGER_ABI = json.load(abi_file)

# Uniswap Nonfungible Position Manager contract address
NONFUNGIBLE_POSITION_MANAGER_ADDRESS = "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"

# Initialize contract
contract = web3.eth.contract(
    address=Web3.to_checksum_address(NONFUNGIBLE_POSITION_MANAGER_ADDRESS),
    abi=NONFUNGIBLE_POSITION_MANAGER_ABI
)

def collect_fees(_token_id):
    """
    Collect fees from the position specified by the token_id.
    """
    print()
    print("Collect Fees called")
    print()
    token_id=int(_token_id)
    # Define maximum values for collecting fees
    amount0_max = 2**128 - 1  # Equivalent to uint128(-1) in Solidity
    amount1_max = 2**128 - 1

    # Prepare transaction
    collect_params = {
        "tokenId": token_id,
        "recipient": WALLET_ADDRESS,
        "amount0Max": amount0_max,
        "amount1Max": amount1_max,
    }

    nonce = web3.eth.get_transaction_count(WALLET_ADDRESS)
    
    
    #get gase estimate
    #get curr gas price
    estimated_gas = contract.functions.collect(collect_params).estimate_gas({
        "from": WALLET_ADDRESS
    })
    print(f"Estimated gas: {estimated_gas}")
    
    '''
    gasPriceRange=getMainNetGas.getGasRange()
    gasPriceGwei=gasPriceRange[3]
    gasPrice=int(gasPriceGwei * 1e9)
    print(f"gasPrice for Collect: {gasPrice}")
    print()   
    '''
    
    try:
        gasPriceGwei=getMainNetGas.getGasPrice() 
        gasPrice=int(gasPriceGwei * 1e9)
        print(f"gasPrice for Collect: {gasPriceGwei}")
    except:
        print()
        print("Error getting currenct gas price!!")
        print()
        time.sleep(12)	#time out here
        gasPriceGwei=getMainNetGas.getGasPrice() 
        gasPrice=int(gasPriceGwei * 1e9)
        print(f"gasPrice for Collect: {gasPriceGwei}")
            
    #gas_price = web3.eth.gas_price
    print(f"Current gas price: {web3.from_wei(gasPrice, 'gwei')} Gwei")    
    
    tx = contract.functions.collect(collect_params).build_transaction({
        "from": WALLET_ADDRESS,
        "nonce": nonce,
        "gas": int(estimated_gas*1.2),	# + 5000,
        "gasPrice": gasPrice	#web3.to_wei("30", "gwei")
    })

    # Sign and send the transaction
    signed_tx = web3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

    print(f"Collect transaction sent: {web3.to_hex(tx_hash)}")
    # Wait for the transaction receipt
    #receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    try:
        receipt = web3.eth.wait_for_transaction_receipt(
            tx_hash, timeout=300, poll_latency=2.0
        )
        print(f"Transaction confirmed: {receipt}")
    except Exception as e:
        print(f"Error while waiting for transaction receipt: {e}")
    
    print(f"Transaction receipt: {receipt}")
    return receipt

def remove_liquidity(_token_id, percentage=1, liquidity=0, priority=3):
    '''
    PRIORITY LEVELS:
    1=HIGHEST
    2=HIGH
    3=MED (DEFAULT)
    4=LOW
    5=LOWEST
    '''
    """
    Remove liquidity from a Uniswap V3 position with additional percentage control.

    Args:
        token_id (int): The token ID of the position.
        percentage (float): A value between 0 and 1 representing the fraction of liquidity to remove.
        liquidity (int): An optional liquidity value. If 0, the value is fetched from the contract.
    """
    token_id=int(_token_id)
    # Validate input percentage
    if not (0 <= percentage <= 1):
        raise ValueError("Percentage must be between 0 and 1")

    # Fetch position details if needed
    position = contract.functions.positions(token_id).call()
    position_liquidity = position[7]  # liquidity is the 8th value returned (uint128)
    time.sleep(30)

    # Calculate liquidity to remove
    if liquidity == 0 and percentage > 0:
        liquidity_to_remove = int(position_liquidity * percentage)
    elif liquidity > 0 and percentage == 0:
        liquidity_to_remove = liquidity
    elif liquidity > 0 and percentage > 0:
        liquidity_to_remove = int(liquidity * percentage)
    else:
        raise ValueError("Either 'liquidity' or 'percentage' must be greater than 0")

    # Ensure liquidity to remove is not greater than available liquidity
    if liquidity_to_remove > position_liquidity:
        raise ValueError("Liquidity to remove exceeds available position liquidity")

    # Define minimum amounts for slippage protection
    amount0_min = 0
    amount1_min = 0

    # Define transaction deadline
    deadline = int((datetime.now() + timedelta(minutes=10)).timestamp())

    # Build transaction for decreaseLiquidity
    params = {
        "tokenId": token_id,
        "liquidity": liquidity_to_remove,
        "amount0Min": amount0_min,
        "amount1Min": amount1_min,
        "deadline": deadline
    }

    nonce = web3.eth.get_transaction_count(WALLET_ADDRESS)

    '''
    gasPriceRange=getMainNetGas.getGasRange()
    gasPriceGwei=gasPriceRange[priority]
    gasPrice=int(gasPriceGwei * 1e9)
    print(f"gasPrice for Remove Liquidity: {gasPrice}")
    print()  
    ''' 
    
    try:
        gasPriceGwei=getMainNetGas.getGasPrice(priority=priority) 
        gasPrice=int(gasPriceGwei * 1e9)
        print(f"gasPrice for Remove Liquidity: {gasPriceGwei}")
    except Exception as e:
        print(f"gas price fetch error: {e}")
        time.sleep(5)
        gasPriceGwei=getMainNetGas.getGasPrice(priority=priority) 
        gasPrice=int(gasPriceGwei * 1e9)
        print(f"gasPrice for Remove Liquidity: {gasPriceGwei}")   
    
    estimated_gas = contract.functions.decreaseLiquidity(params).estimate_gas({
        "from": WALLET_ADDRESS
    })
    print(f"Estimated gas: {estimated_gas}")
    
    #gas_price = web3.eth.gas_price
    print(f"Current gas price: {web3.from_wei(gasPrice, 'gwei')} Gwei")
    
    
    transaction = contract.functions.decreaseLiquidity(params).build_transaction({
        "from": WALLET_ADDRESS,
        "nonce": nonce,
        "gas": int(estimated_gas*1.2),
        "gasPrice": gasPrice	#web3.to_wei("20", "gwei")
    })
    print("transaction: ", transaction)
    

    
    # Sign and send the transaction
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"Transaction sent: {web3.to_hex(tx_hash)}")
    time.sleep(30)
    try:
        receipt = web3.eth.wait_for_transaction_receipt(
            tx_hash, timeout=300, poll_latency=2.0
        )
        print(f"Transaction confirmed: {receipt}")
    except Exception as e:
        print(f"Error while waiting for transaction receipt: {e}")
    

    # Wait for transaction receipt
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Transaction confirmed: {receipt.transactionHash.hex()}")
    return receipt
    
'''
# Example usage
token_id = 2379360

try:
    remove_liquidity(token_id, percentage=0.5)  # Remove 50% of position's liquidity
except Exception as e:
    print(f"Error: {e}")



try:
    time.sleep(30)
    collect_fees(token_id)  # Collect fees after liquidity removal
except Exception as e:
    print(f"Error: {e}")
'''

def remLiquAndCollFordefi(token_id, chain, percentage=1.0, liquidity=0, priority=1):
    token_id = int(token_id)
    # Validate input
    if not (0 <= percentage <= 1):
        raise ValueError("Percentage must be between 0 and 1")

    # Fetch position details
    position = contract.functions.positions(token_id).call()
    position_liquidity = position[7]
    time.sleep(2)

    if liquidity == 0 and percentage > 0:
        calculated = int(position_liquidity * percentage)
        diff_ratio = abs(position_liquidity - calculated) / position_liquidity if position_liquidity != 0 else 0

        if diff_ratio <= 0.01:  # Within 1%
            liquidity_to_remove = position_liquidity
        else:
            liquidity_to_remove = calculated
    elif liquidity > 0 and percentage == 0:
        liquidity_to_remove = liquidity

    elif liquidity > 0 and percentage > 0:
        calculated = int(liquidity * percentage)
        diff_ratio = abs(position_liquidity - calculated) / position_liquidity if position_liquidity != 0 else 0

        if diff_ratio <= 0.01:  # Within 1%
            liquidity_to_remove = position_liquidity
        else:
            liquidity_to_remove = calculated

    else:
        raise ValueError("Invalid liquidity or percentage combination")
    
    # Params
    amount0_min = 0
    amount1_min = 0
    deadline = int((datetime.now() + timedelta(minutes=4)).timestamp())

    decrease_params = {
        "tokenId": token_id,
        "liquidity": liquidity_to_remove,
        "amount0Min": amount0_min,
        "amount1Min": amount1_min,
        "deadline": deadline,
    }

    collect_params = {
        "tokenId": token_id,
        "recipient": WALLET_ADDRESS,
        "amount0Max": 2**128 - 1,
        "amount1Max": 2**128 - 1,
    }

    # Encode both function calls
    #encoded_decrease = contract.encode_abi(fn_name="decreaseLiquidity", args=[decrease_params])
    #encoded_collect = contract.encode_abi(fn_name="collect", args=[collect_params])
    encoded_decrease = contract.encode_abi("decreaseLiquidity", args=[decrease_params])
    encoded_collect = contract.encode_abi("collect", args=[collect_params])

    # Combine them in multicall
    multicall_data = [encoded_decrease, encoded_collect]

    nonce = web3.eth.get_transaction_count(WALLET_ADDRESS)

    try:
        gasPriceGwei = getMainNetGas.getGasPrice(priority=priority)
        gasPrice = int(gasPriceGwei * 1e9)
    except Exception as e:
        print(f"Gas price error: {e}")
        gasPriceGwei = getMainNetGas.getGasPrice(priority=priority)
        gasPrice = int(gasPriceGwei * 1e9)

    # Estimate gas (rough guess since multicall can be tricky)
    print("multicall_data: ", multicall_data)
    print()
    
    try:
        estimated_gas = contract.functions.multicall(multicall_data).estimate_gas({"from": WALLET_ADDRESS})
    except Exception as e:
        print(f"Gas Estimate error: {e}")
        print("multicall_data: ", multicall_data)
        print("token id: ", token_id)
        print("position_liquidity: ", position_liquidity)
        print("liquidity_to_remove: ", liquidity_to_remove)
        print()
        time.sleep(5)
        estimated_gas = contract.functions.multicall(multicall_data).estimate_gas({"from": WALLET_ADDRESS})
        
    print(f"Estimated gas for multicall: {estimated_gas}")
    print(f"Gas Price submited: {gasPrice}")
    print()

    tx = contract.functions.multicall(multicall_data).build_transaction({
        "from": WALLET_ADDRESS,
        "nonce": nonce,
        "gas": int(estimated_gas * 1.2),
        "gasPrice": gasPrice
    })
    
    #!!!!!!!!!! INSERT HERE: "return tx" !!!!!!!!!!!!!!!!!!

    #signed_tx = web3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    #tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

    #print(f"Multicall tx sent: {web3.to_hex(tx_hash)}")
    #print("Waiting for reciept.....")
    print()
    try:
        #receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300, poll_latency=2.0)
        receipt = asyncio.run(evmTxRaw.rawTx(tx['data'], NONFUNGIBLE_POSITION_MANAGER_ADDRESS, chain))
        print(f"Transaction confirmed!")	#: {receipt}")
    except Exception as e:
        print(f"Error during tx confirmation: {e}")
        receipt="fail"
    return receipt


def remove_liquidity_and_collect(token_id, percentage=1.0, liquidity=0, priority=1):
    token_id = int(token_id)
    # Validate input
    if not (0 <= percentage <= 1):
        raise ValueError("Percentage must be between 0 and 1")

    # Fetch position details
    position = contract.functions.positions(token_id).call()
    position_liquidity = position[7]
    time.sleep(2)

    if liquidity == 0 and percentage > 0:
        calculated = int(position_liquidity * percentage)
        diff_ratio = abs(position_liquidity - calculated) / position_liquidity if position_liquidity != 0 else 0

        if diff_ratio <= 0.01:  # Within 1%
            liquidity_to_remove = position_liquidity
        else:
            liquidity_to_remove = calculated
    elif liquidity > 0 and percentage == 0:
        liquidity_to_remove = liquidity

    elif liquidity > 0 and percentage > 0:
        calculated = int(liquidity * percentage)
        diff_ratio = abs(position_liquidity - calculated) / position_liquidity if position_liquidity != 0 else 0

        if diff_ratio <= 0.01:  # Within 1%
            liquidity_to_remove = position_liquidity
        else:
            liquidity_to_remove = calculated

    else:
        raise ValueError("Invalid liquidity or percentage combination")
    
    # Params
    amount0_min = 0
    amount1_min = 0
    deadline = int((datetime.now() + timedelta(minutes=4)).timestamp())

    decrease_params = {
        "tokenId": token_id,
        "liquidity": liquidity_to_remove,
        "amount0Min": amount0_min,
        "amount1Min": amount1_min,
        "deadline": deadline,
    }

    collect_params = {
        "tokenId": token_id,
        "recipient": WALLET_ADDRESS,
        "amount0Max": 2**128 - 1,
        "amount1Max": 2**128 - 1,
    }

    # Encode both function calls
    #encoded_decrease = contract.encode_abi(fn_name="decreaseLiquidity", args=[decrease_params])
    #encoded_collect = contract.encode_abi(fn_name="collect", args=[collect_params])
    encoded_decrease = contract.encode_abi("decreaseLiquidity", args=[decrease_params])
    encoded_collect = contract.encode_abi("collect", args=[collect_params])

    # Combine them in multicall
    multicall_data = [encoded_decrease, encoded_collect]

    nonce = web3.eth.get_transaction_count(WALLET_ADDRESS)

    try:
        gasPriceGwei = getMainNetGas.getGasPrice(priority=priority)
        gasPrice = int(gasPriceGwei * 1e9)
    except Exception as e:
        print(f"Gas price error: {e}")
        gasPriceGwei = getMainNetGas.getGasPrice(priority=priority)
        gasPrice = int(gasPriceGwei * 1e9)

    # Estimate gas (rough guess since multicall can be tricky)
    print("multicall_data: ", multicall_data)
    print()
    
    try:
        estimated_gas = contract.functions.multicall(multicall_data).estimate_gas({"from": WALLET_ADDRESS})
    except Exception as e:
        print(f"Gas Estimate error: {e}")
        print("multicall_data: ", multicall_data)
        print("token id: ", token_id)
        print("position_liquidity: ", position_liquidity)
        print("liquidity_to_remove: ", liquidity_to_remove)
        print()
        time.sleep(5)
        estimated_gas = contract.functions.multicall(multicall_data).estimate_gas({"from": WALLET_ADDRESS})
        
    print(f"Estimated gas for multicall: {estimated_gas}")
    print(f"Gas Price submited: {gasPrice}")
    print()

    tx = contract.functions.multicall(multicall_data).build_transaction({
        "from": WALLET_ADDRESS,
        "nonce": nonce,
        "gas": int(estimated_gas * 1.2),
        "gasPrice": gasPrice
    })
    
    #!!!!!!!!!! INSERT HERE: "return tx" !!!!!!!!!!!!!!!!!!

    signed_tx = web3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

    print(f"Multicall tx sent: {web3.to_hex(tx_hash)}")
    print("Waiting for reciept.....")
    print()
    try:
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300, poll_latency=2.0)
        print(f"Transaction confirmed!")	#: {receipt}")
    except Exception as e:
        print(f"Error during tx confirmation: {e}")
        receipt="fail"
    return receipt



if __name__ == "__main__":
	token_id=input("Token number: ")	#0xdAC17F958D2ee523a2206206994597C13D831ec7"
	
	remove_liquidity_and_collect(token_id)
	'''
	remove=input("Remove Liquidity? (y/n): ")
	if remove=="y":
		try:
			remove_liquidity(token_id)	#, percentage=0.5)  # Remove 50% of position's liquidity
		except Exception as e:
			print(f"Error: {e}")
	
	collect=input("Collect Fees? (y/n): ")
	if collect=="y":
		try:
			#time.sleep(30)
			collect_fees(token_id)  # Collect fees after liquidity removal
		except Exception as e:
			print(f"Error: {e}")
  '''
    
    
    
    	
	
