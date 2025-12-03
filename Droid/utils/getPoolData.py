from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()

# Load environment variables
INFURA_URL = os.getenv("PROVIDER")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("ADDRESS")

# ABI for the Uniswap V3 pool contract
pool_abi = [
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "fee",
        "outputs": [{"internalType": "uint24", "name": "", "type": "uint24"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "liquidity",
        "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "tickSpacing",
        "outputs": [{"internalType": "int24", "name": "", "type": "int24"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "int24", "name": "tick", "type": "int24"},
            {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
            {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
            {"internalType": "bool", "name": "unlocked", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

erc20_abi = '''[
    {"constant": true, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "payable": false, "stateMutability": "view", "type": "function"}
]'''

# Replace with your own Infura project URL or any other Ethereum provider
infura_url = INFURA_URL	#"https://polygon-mainnet.infura.io/v3/f61eb7936eb442039755958c9d3b675b"
web3 = Web3(Web3.HTTPProvider(infura_url))

def get_uniswap_v3_pool_data_old(pool_address, stableCoinPosition):
    # Ensure the address is checksummed
    pool_address = Web3.to_checksum_address(pool_address)
    
    # Create a contract instance for the Uniswap V3 pool
    pool_contract = web3.eth.contract(address=pool_address, abi=pool_abi)

    # Fetch pool data
    token0 = pool_contract.functions.token0().call()
    token1 = pool_contract.functions.token1().call()
    fee = pool_contract.functions.fee().call()
    liquidity = pool_contract.functions.liquidity().call()
    tick_spacing = pool_contract.functions.tickSpacing().call()
    slot0 = pool_contract.functions.slot0().call()

    sqrt_price_x96 = slot0[0]
    current_tick = slot0[1]
    token0_decimals = web3.eth.contract(address=token0, abi=erc20_abi).functions.decimals().call()
    token1_decimals = web3.eth.contract(address=token1, abi=erc20_abi).functions.decimals().call()
    price_token0_in_token1 = ((sqrt_price_x96 / (2 ** 96)) ** 2) * (10 ** (token0_decimals - token1_decimals))
    pricePerWatchCoin= price_token0_in_token1 if stableCoinPosition==0 else 1/price_token0_in_token1
    # Output the fetched data
    print(f"Uniswap V3 Pool at address: {pool_address}")
    print(f"Token 0 Address: {token0}")
    print(f"Token 1 Address: {token1}")
    print(f"Fee (in hundredths of a bip): {fee / 10000}%")
    print(f"Liquidity: {liquidity}")
    print(f"Tick Spacing: {tick_spacing}")
    print(f"Sqrt Price (X96): {sqrt_price_x96}")
    print(f"Current Tick: {current_tick}")
    print(f"price_token0_in_token1: {price_token0_in_token1}")
    print(f"pricePerWatchCoin: {pricePerWatchCoin}")
    
def get_uniswap_v3_pool_data(pool_address, stableCoinPosition):
    # Ensure the address is checksummed
    pool_address = Web3.to_checksum_address(pool_address)
    
    # Create a contract instance for the Uniswap V3 pool
    pool_contract = web3.eth.contract(address=pool_address, abi=pool_abi)

    # Fetch pool data
    token0 = pool_contract.functions.token0().call()
    token1 = pool_contract.functions.token1().call()
    fee = pool_contract.functions.fee().call()
    liquidity = pool_contract.functions.liquidity().call()
    tick_spacing = pool_contract.functions.tickSpacing().call()
    slot0 = pool_contract.functions.slot0().call()

    sqrt_price_x96 = slot0[0]
    current_tick = slot0[1]
    token0_decimals = web3.eth.contract(address=token0, abi=erc20_abi).functions.decimals().call()
    token1_decimals = web3.eth.contract(address=token1, abi=erc20_abi).functions.decimals().call()
    price_token0_in_token1 = ((sqrt_price_x96 / (2 ** 96)) ** 2) * (10 ** (token0_decimals - token1_decimals))
    pricePerWatchCoin = price_token0_in_token1 if stableCoinPosition == 1 else 1 / price_token0_in_token1

    # Return data as a dictionary
    return {
        "pool_address": pool_address,
        "token0": token0,
        "token1": token1,
        "fee_percent": fee / 10000,
        "liquidity": liquidity,
        "tick_spacing": tick_spacing,
        "sqrt_price_x96": sqrt_price_x96,
        "current_tick": current_tick,
        "price_token0_in_token1": price_token0_in_token1,
        "pricePerWatchCoin": pricePerWatchCoin,
        "token0_decimals": token0_decimals,
        "token1_decimals": token1_decimals
    }


if __name__ == "__main__":
    pool_address = input("Enter the Uniswap V3 pool address: ")
    stableCoinPosition=int(input("enter stable coin position: "))
    if web3.is_address(pool_address):
        result=get_uniswap_v3_pool_data(pool_address, stableCoinPosition)
        print(result)
    else:
        print("Invalid Ethereum address.")

