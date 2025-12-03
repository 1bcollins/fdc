from web3 import Web3
import json
import os
from dotenv import load_dotenv
#from web3.middleware import geth_poa_middleware
from web3.middleware import ExtraDataToPOAMiddleware
import time
import getMainNetGas
import approveToken

load_dotenv()

# Load environment variables
RPC_URL = os.getenv("PROVIDER")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("ADDRESS")

# Configurations
#RPC_URL = "https://polygon-mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"  # Replace with your RPC URL
#PRIVATE_KEY = "YOUR_PRIVATE_KEY"  # Replace with your private key (DO NOT hardcode in production)
#WALLET_ADDRESS = "YOUR_WALLET_ADDRESS"
UNISWAP_ROUTER_V3 = "0xE592427A0AEce92De3Edee1F18E0157C05861564"  # Uniswap V3 Router on Ethereum/Polygon

# Web3 Connection
web3 = Web3(Web3.HTTPProvider(RPC_URL))
# Add the middleware for PoA chains
#web3.middleware_onion.inject(geth_poa_middleware, layer=0)
web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

assert web3.is_connected(), "Failed to connect to Web3"

# ERC-20 ABI (Minimal for approvals and transfers)
ERC20_ABI = json.loads('[{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},{"constant":false,"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[],"type":"function"}]')

# Uniswap V3 Router ABI (Partial for swapping)
UNISWAP_V3_ROUTER_ABI = json.loads('[{"inputs":[{"components":[{"internalType":"address","name":"tokenIn","type":"address"},{"internalType":"address","name":"tokenOut","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMinimum","type":"uint256"},{"internalType":"uint160","name":"sqrtPriceLimitX96","type":"uint160"}],"internalType":"struct ISwapRouter.ExactInputSingleParams","name":"params","type":"tuple"}],"name":"exactInputSingle","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"}],"stateMutability":"payable","type":"function"}]')


# Function to get token decimals
def get_token_decimals(token_address):
    token_contract = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
    return token_contract.functions.decimals().call()

'''
# Function to approve token spend
def approve_token_spend(token_address, amount, spender):
    token_contract = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
    
    estimated_gas = token_contract.functions.approve(spender, amount).estimate_gas({"from": WALLET_ADDRESS})
    
    gasPriceGwei=getMainNetGas.getGasPrice() 
    gasPrice=int(gasPriceGwei * 1e9)
    print(f"gasPrice for Swap: {gasPriceGwei}")
    
    tx = token_contract.functions.approve(spender, amount).build_transaction({
        "from": WALLET_ADDRESS,
        "nonce": web3.eth.get_transaction_count(WALLET_ADDRESS),
        "gas": int(estimated_gas*1.2),	
        "gasPrice": gasPrice,
    })
    signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    return web3.eth.send_raw_transaction(signed_tx.raw_transaction)
'''

# Function to swap tokens on Uniswap V3
def swap_tokens(token_in, token_out, amount_in, min_amount_out, fee=3000):
    print("swap_tokens function called")
    swapError="failed"
    router_contract = web3.eth.contract(address=Web3.to_checksum_address(UNISWAP_ROUTER_V3), abi=UNISWAP_V3_ROUTER_ABI)
    
    # Set transaction parameters
    tx_params = {
        "tokenIn": Web3.to_checksum_address(token_in),
        "tokenOut": Web3.to_checksum_address(token_out),
        "fee": fee,  # 3000 = 0.3% fee tier
        "recipient": WALLET_ADDRESS,
        "deadline": web3.eth.get_block("latest")["timestamp"] + 150,  # 1 min expiry
        "amountIn": amount_in,
        "amountOutMinimum": min_amount_out,
        "sqrtPriceLimitX96": 0  # No price limit
    }
    print("tx_params: ", tx_params)
    
    #allowance = token_contract.functions.allowance(WALLET_ADDRESS, UNISWAP_ROUTER_V3).call()
    #print(f"Allowance: {allowance}")
    
    #estimate gas
    #gasEstimate=300000
    '''
    gasEstimate = router_contract.functions.exactInputSingle(tx_params).estimate_gas({
        "from": WALLET_ADDRESS
    })
    '''
    
    try:
        gasEstimate = router_contract.functions.exactInputSingle(tx_params).estimate_gas({"from": WALLET_ADDRESS})
        print("gasEstimate: ", gasEstimate)
    except Exception as e:
        print(f"Gas estimation failed: {e}")
        print("Wait for 'time out'")
        time.sleep(12)
        print("2nd attempt")
        gasEstimate = router_contract.functions.exactInputSingle(tx_params).estimate_gas({"from": WALLET_ADDRESS})
        print("gasEstimate: ", gasEstimate)        
        #raise
    #print("gasEstimate: ", gasEstimate)
    
    
    # Build transaction
    gas=int(gasEstimate*1.2)
    nonce=web3.eth.get_transaction_count(WALLET_ADDRESS)
    
    '''
    gasPrice=web3.eth.gas_price
    # Add a Priority Fee (Tip)
    priority_fee = Web3.to_wei(10, "gwei")  # Adjust based on urgency
    gasPrice=gasPrice+ priority_fee
    gas_price_gwei = Web3.from_wei(gasPrice, "gwei")
    '''
    '''
    gasPriceRange=getPolyGas.getGasRange()
    gasPriceGwei=gasPriceRange[2]
    gasPrice=int(gasPriceGwei * 1e9)
    print(f"gasPrice for Add Liquidity: {gasPrice}")
    print()
    gas_price_gwei = Web3.from_wei(gasPrice, "gwei")
    '''
    
    gasPriceGwei=getMainNetGas.getGasPrice() 
    gasPrice=int(gasPriceGwei * 1e9)
    print(f"gasPrice for Swap: {gasPriceGwei}")
    
    print(f"Gas Price: {gasPriceGwei} Gwei")  # Output: 50 Gwei
    tx = router_contract.functions.exactInputSingle(tx_params).build_transaction({
        "from": WALLET_ADDRESS,
        "nonce": nonce,
        "gas": gas,
        "gasPrice": gasPrice,
    })
    print("from: ", WALLET_ADDRESS)
    print("gas: ", gas)
    print("nonce: ", nonce)
    print("gasPrice: ", gasPrice)

    # Sign and send transaction
    signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    try:
        print("waiting for tx reciept.....")
        receipt = web3.eth.wait_for_transaction_receipt(
    	      tx_hash, timeout=300, poll_latency=2.0
        )
        print(f"Transaction confirmed: {receipt}")
        swapError="success"
    except Exception as e:
		    print(f"Error while waiting for transaction receipt: {e}")
		    swapError="fail"
    
    return tx_hash.hex(), swapError

def swapTokens(swapParams):
    print("swapParams: ", swapParams)
    token_decimals_in = get_token_decimals(swapParams['TOKEN_IN'])
    #MOUNT_IN = Web3.to_wei(10, "ether")  # 10 DAI (adjust decimals based on token)
    AMOUNT_IN = int(swapParams['amountIn'] * (10 ** token_decimals_in))  # Adjust amount based on token decimals
    token_decimals_out= get_token_decimals(swapParams['TOKEN_OUT'])
    #MIN_AMOUNT_OUT = Web3.to_wei(0.002, "ether")  # Expected minimum WETH amount
    MIN_AMOUNT_OUT= int(swapParams['amountOutMin'] * (10 ** token_decimals_out)) 

    # Approve Uniswap to spend DAI
    print("swapParams['TOKEN_IN']: ", swapParams['TOKEN_IN'])
    #approveTx=approve_token_spend(swapParams['TOKEN_IN'], AMOUNT_IN, UNISWAP_ROUTER_V3)
    apprRes=approveToken.approve_token(swapParams['TOKEN_IN'], UNISWAP_ROUTER_V3, AMOUNT_IN)
    print("Approval request sent!")
    print("Approve Result: ", apprRes)
    #add delay for block sync
    print("waiting 30 sec for block update!")
    time.sleep(15)
    

    # Execute swap
    if (apprRes=="approved"): swap_tx_hash, swapError = swap_tokens(swapParams['TOKEN_IN'], swapParams['TOKEN_OUT'], AMOUNT_IN, MIN_AMOUNT_OUT, swapParams['fee'])
    print(f"Swap submitted! Transaction hash: {swap_tx_hash}")
    return swap_tx_hash, swapError

# Example Usage
if __name__ == "__main__":
    #TOKEN_IN = "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063"  # Example: DAI on Polygon
    #TOKEN_OUT = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"  # Example: WETH on Polygon
    
    '''
    TOKEN_IN = input("Input addr of 'in' token: ")
    TOKEN_OUT = input("Input addr of 'out' token: ")
    amountIn=float(input(f"Input amount of {TOKEN_IN}: "))
    amountOutMin=float(input(f"Input min amount of {TOKEN_OUT} out: "))
    fee=int(input("input fee tier: "))
    
    
    packageToJson= {
		    "TOKEN_IN": TOKEN_IN,
		    "TOKEN_OUT": TOKEN_OUT,
		    "amountIn": amountIn,
		    "amountOutMin": amountOutMin,
		    "fee": fee
    }
    '''
    
    packageToJson={'TOKEN_IN': '0xc2132d05d31c914a87c6611c10748aeb04b58e8f', 'TOKEN_OUT': '0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270', 'amountIn': 214.36, 'amountOutMin': 679.95, 'fee': 500}
    txHash=swapTokens(packageToJson)
    print(txHash)
    '''
    token_decimals_in = get_token_decimals(TOKEN_IN)
    #MOUNT_IN = Web3.to_wei(10, "ether")  # 10 DAI (adjust decimals based on token)
    AMOUNT_IN = amountIn * (10 ** token_decimals_in)  # Adjust amount based on token decimals
    token_decimals_out= get_token_decimals(TOKEN_OUT)
    #MIN_AMOUNT_OUT = Web3.to_wei(0.002, "ether")  # Expected minimum WETH amount
    MIN_AMOUNT_OUT= amountOutMin * (10 ** token_decimals_out) 

    # Approve Uniswap to spend DAI
    approve_token_spend(TOKEN_IN, AMOUNT_IN, UNISWAP_ROUTER_V3)
    print("Approval successful!")

    # Execute swap
    swap_tx_hash = swap_tokens(TOKEN_IN, TOKEN_OUT, AMOUNT_IN, MIN_AMOUNT_OUT)
    print(f"Swap submitted! Transaction hash: {swap_tx_hash}")
    '''
    
    

