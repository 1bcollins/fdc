from web3 import Web3
import math
import getLpPoolFees
#import getMainNetErcPrice
import getMainNetPriceFromPool
from dotenv import load_dotenv
import os
load_dotenv()
# Load environment variables
INFURA_URL = os.getenv("PROVIDER")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("ADDRESS")


# Constants
#INFURA_URL = "https://polygon-mainnet.infura.io/v3/f61eb7936eb442039755958c9d3b675b"	#"https://mainnet.infura.io/v3/aea940137990482ba4e57b44db9fe5f6"
UNISWAP_V3_FACTORY_ADDRESS = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
#UNISWAP_V3_POSITIONS_ABI = [ ... ]  # As in your script
UNISWAP_V3_POSITIONS_ABI = [
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "positions",
        "outputs": [
            {"internalType": "uint96", "name": "nonce", "type": "uint96"},
            {"internalType": "address", "name": "operator", "type": "address"},
            {"internalType": "address", "name": "token0", "type": "address"},
            {"internalType": "address", "name": "token1", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
            {"internalType": "int24", "name": "tickLower", "type": "int24"},
            {"internalType": "int24", "name": "tickUpper", "type": "int24"},
            {"internalType": "uint128", "name": "liquidity", "type": "uint128"},
            {"internalType": "uint256", "name": "feeGrowthInside0LastX128", "type": "uint256"},
            {"internalType": "uint256", "name": "feeGrowthInside1LastX128", "type": "uint256"},
            {"internalType": "uint128", "name": "tokensOwed0", "type": "uint128"},
            {"internalType": "uint128", "name": "tokensOwed1", "type": "uint128"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "ownerOf",
        "outputs": [{"internalType": "address", "name": "owner", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

#POOL_ABI = [ ... ]  # As in your script
POOL_ABI = [
    {
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
        "inputs": [],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "name": "ticks",
        "outputs": [
            {"internalType": "uint128", "name": "liquidityGross", "type": "uint128"},
            {"internalType": "int128", "name": "liquidityNet", "type": "int128"},
            {"internalType": "uint256", "name": "feeGrowthOutside0X128", "type": "uint256"},
            {"internalType": "uint256", "name": "feeGrowthOutside1X128", "type": "uint256"},
            {"internalType": "int56", "name": "tickCumulativeOutside", "type": "int56"},
            {"internalType": "uint160", "name": "secondsPerLiquidityOutsideX128", "type": "uint160"},
            {"internalType": "uint32", "name": "secondsOutside", "type": "uint32"},
            {"internalType": "bool", "name": "initialized", "type": "bool"}
        ],
        "inputs": [
            {"internalType": "int24", "name": "tick", "type": "int24"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "name": "feeGrowthGlobal0X128",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "inputs": [],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "name": "feeGrowthGlobal1X128",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "inputs": [],
        "stateMutability": "view",
        "type": "function"
    }
]



#ERC20_ABI = [ ... ]  # Minimal ABI to get decimals
ERC20_ABI = [
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ]

# Core functions

def connect_to_ethereum():
    web3 = Web3(Web3.HTTPProvider(INFURA_URL))
    if not web3.is_connected():
        raise Exception("Unable to connect to Ethereum network.")
    return web3

def get_position_data(web3, contract_address, token_id):
    """
    Retrieve position data for a specific NFT token ID from the Uniswap V3 Positions contract.
    """
    contract = web3.eth.contract(address=contract_address, abi=UNISWAP_V3_POSITIONS_ABI)
    data = contract.functions.positions(token_id).call()
    
    # Map the tuple result to a dictionary
    return {
        "nonce": data[0],
        "operator": data[1],
        "token0": data[2],
        "token1": data[3],
        "fee": data[4],
        "tickLower": data[5],
        "tickUpper": data[6],
        "liquidity": data[7],
        "feeGrowthInside0LastX128": data[8],
        "feeGrowthInside1LastX128": data[9],
        "tokensOwed0": data[10],
        "tokensOwed1": data[11]
    }


def get_owner(contract_address, token_id):
    """
    Retrieve position data for a specific NFT token ID from the Uniswap V3 Positions contract.
    """
    web3 = connect_to_ethereum()
    contract = web3.eth.contract(address=contract_address, abi=UNISWAP_V3_POSITIONS_ABI)
    data = contract.functions.ownerOf(token_id).call()
    return data


def get_pool_address(web3, token0, token1, fee):
    factory_contract = web3.eth.contract(address=UNISWAP_V3_FACTORY_ADDRESS, abi=[{
        "inputs": [{"internalType": "address", "name": "tokenA", "type": "address"},
                   {"internalType": "address", "name": "tokenB", "type": "address"},
                   {"internalType": "uint24", "name": "fee", "type": "uint24"}],
        "name": "getPool", "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view", "type": "function"
    }])
    return factory_contract.functions.getPool(token0, token1, fee).call()

def get_token_decimals(web3, token_address):
    token_contract = web3.eth.contract(address=token_address, abi=ERC20_ABI)
    return token_contract.functions.decimals().call()

def get_token_amounts(liquidity, sqrt_price_x96, tick_low, tick_high, decimal0, decimal1):
    Q96 = 2 ** 96
    sqrt_ratio_a = math.sqrt(1.0001 ** tick_low)
    sqrt_ratio_b = math.sqrt(1.0001 ** tick_high)
    current_tick = math.floor(math.log((sqrt_price_x96 / Q96) ** 2) / math.log(1.0001))
    sqrt_price = sqrt_price_x96 / Q96

    amount0 = amount1 = 0
    if current_tick < tick_low:
        amount0 = liquidity * ((sqrt_ratio_b - sqrt_ratio_a) / (sqrt_ratio_a * sqrt_ratio_b))
    elif current_tick >= tick_high:
        amount1 = liquidity * (sqrt_ratio_b - sqrt_ratio_a)
    else:
        amount0 = liquidity * ((sqrt_ratio_b - sqrt_price) / (sqrt_price * sqrt_ratio_b))
        amount1 = liquidity * (sqrt_price - sqrt_ratio_a)
    
    return round(amount0 / (10 ** decimal0), decimal0), round(amount1 / (10 ** decimal1), decimal1)

def get_slot0_data(web3, pool_address):
    pool_contract = web3.eth.contract(address=pool_address, abi=POOL_ABI)
    return pool_contract.functions.slot0().call()

def get_fee_growth_data(web3, pool_contract, tick_lower, tick_upper):
    """
    Retrieves fee growth data for a pool at the tick range boundaries.
    """
    # Retrieve data for tick lower and tick upper boundaries
    lower_data = pool_contract.functions.ticks(tick_lower).call()
    upper_data = pool_contract.functions.ticks(tick_upper).call()
    
    # Extract the fee growth data from the lower and upper tick data
    fee_growth0_low = lower_data[2]  # feeGrowthOutside0X128 for lower tick
    fee_growth1_low = lower_data[3]  # feeGrowthOutside1X128 for lower tick
    fee_growth0_hi = upper_data[2]   # feeGrowthOutside0X128 for upper tick
    fee_growth1_hi = upper_data[3]   # feeGrowthOutside1X128 for upper tick

    # Return all required fee growth values as a tuple
    return fee_growth0_low, fee_growth1_low, fee_growth0_hi, fee_growth1_hi



def get_fees(position_data, sqrt_price_x96, fee_growth_data, decimals0, decimals1):
    fee_growth_global0 = fee_growth_data[0]
    fee_growth_global1 = fee_growth_data[1]
    fee_growth0_low, fee_growth1_low = fee_growth_data[2], fee_growth_data[3]
    fee_growth0_hi, fee_growth1_hi = fee_growth_data[4], fee_growth_data[5]
    return getLpPoolFees.get_fees(fee_growth_global0, fee_growth_global1, fee_growth0_low, fee_growth0_hi, 
                                  position_data["feeGrowthInside0LastX128"], fee_growth1_low, fee_growth1_hi, 
                                  position_data["feeGrowthInside1LastX128"], position_data["liquidity"], 
                                  decimals0, decimals1, position_data["tickLower"], position_data["tickUpper"], 
                                  sqrt_price_x96)

def getPoolAddress(UNISWAP_V3_POSITIONS_NFT_CONTRACT_ADDRESS, TOKEN_ID):
    web3 = connect_to_ethereum()
    position_data = get_position_data(web3, UNISWAP_V3_POSITIONS_NFT_CONTRACT_ADDRESS, TOKEN_ID)
    # Get the pool address and contract for token0/token1 pair
    pool_address = get_pool_address(web3, position_data["token0"], position_data["token1"], position_data["fee"])
    return pool_address

# Main entry function
def get_liquidity_and_fees(UNISWAP_V3_POSITIONS_NFT_CONTRACT_ADDRESS, TOKEN_ID):
    web3 = connect_to_ethereum()
    
    # Retrieve position data
    position_data = get_position_data(web3, UNISWAP_V3_POSITIONS_NFT_CONTRACT_ADDRESS, TOKEN_ID)
    
    # Get the pool address and contract for token0/token1 pair
    pool_address = get_pool_address(web3, position_data["token0"], position_data["token1"], position_data["fee"])
    pool_contract = web3.eth.contract(address=pool_address, abi=POOL_ABI)
    
    # Retrieve current sqrtPriceX96 from slot0
    slot0_data = get_slot0_data(web3, pool_address)
    sqrt_price_x96 = slot0_data[0]
    
    # Retrieve token decimals for token0 and token1
    token0_decimals = get_token_decimals(web3, position_data["token0"])
    token1_decimals = get_token_decimals(web3, position_data["token1"])
    #token0_priceUSD = getMainNetErcPrice.get_token_price(position_data["token0"])
    #token1_priceUSD = getMainNetErcPrice.get_token_price(position_data["token1"])
    #print("!!!!!!!!!!")
    #print(f"Calling 'getMainNetPriceFromPool.get_token_price' with {position_data['token0'].lower()}")
    #print("!!!!!!!!!!!!!!")
    token0_priceUSD = getMainNetPriceFromPool.get_token_price(position_data["token0"].lower())
    #print("!!!!!!!!!!")
    #print(f"Calling 'getMainNetPriceFromPool.get_token_price' with {position_data['token1'].lower()}")
    #print("!!!!!!!!!!!!!!")
    token1_priceUSD = getMainNetPriceFromPool.get_token_price(position_data["token1"].lower())
    
    # Calculate liquidity amounts
    liquidity_amounts = get_token_amounts(position_data["liquidity"], sqrt_price_x96, position_data["tickLower"], position_data["tickUpper"], token0_decimals, token1_decimals)
    
    # Retrieve fee growth data at tick boundaries
    fee_growth0_low, fee_growth1_low, fee_growth0_hi, fee_growth1_hi = get_fee_growth_data(web3, pool_contract, position_data["tickLower"], position_data["tickUpper"])
    
    # Calculate uncollected fees using the `get_fees` function from `getLpPoolFees`
    uncollected_fees = getLpPoolFees.get_fees(
        fee_growth_global0=pool_contract.functions.feeGrowthGlobal0X128().call(),
        fee_growth_global1=pool_contract.functions.feeGrowthGlobal1X128().call(),
        fee_growth0_low=fee_growth0_low,
        fee_growth0_hi=fee_growth0_hi,
        fee_growth_inside0=position_data["feeGrowthInside0LastX128"],
        fee_growth1_low=fee_growth1_low,
        fee_growth1_hi=fee_growth1_hi,
        fee_growth_inside1=position_data["feeGrowthInside1LastX128"],
        liquidity=position_data["liquidity"],
        decimals0=token0_decimals,
        decimals1=token1_decimals,
        tick_lower=position_data["tickLower"],
        tick_upper=position_data["tickUpper"],
        tick_current=slot0_data[1]
    )
    #print(f"uncollected_fees: {uncollected_fees}")
    # Construct and return the result dictionary with proper key access
    return {
        "liquidity_amount_token0": liquidity_amounts[0],
        "liquidity_amount_token1": liquidity_amounts[1],
        "uncollected_fees_token0": float(uncollected_fees["uncollected_fees_token0"]),
        "uncollected_fees_token1": float(uncollected_fees["uncollected_fees_token1"]),
        "token0_priceUSD": token0_priceUSD,
        "token1_priceUSD": token1_priceUSD
    }

def getLpPoolValueUSD(UNISWAP_V3_POSITIONS_NFT_CONTRACT_ADDRESS, TOKEN_ID):
    results = get_liquidity_and_fees(UNISWAP_V3_POSITIONS_NFT_CONTRACT_ADDRESS, TOKEN_ID)
    totValUSD=(results["uncollected_fees_token0"]+results["liquidity_amount_token0"])*results["token0_priceUSD"]
    totValUSD=totValUSD+(results["uncollected_fees_token1"]+results["liquidity_amount_token1"])*results["token1_priceUSD"]    
    return totValUSD


if __name__ == "__main__":
	nftId=int(input("Input nft id: "))
	result = get_liquidity_and_fees("0xC36442b4a4522E871399CD717aBDD847Ab11FE88", nftId)
	print(result)


'''
# Example call
result = get_liquidity_and_fees("0xC36442b4a4522E871399CD717aBDD847Ab11FE88", 851643)
print(result)
print(result["uncollected_fees_token0"])
'''
#print(getLpPoolValueUSD("0xC36442b4a4522E871399CD717aBDD847Ab11FE88", 851643))
#print(get_owner("0xC36442b4a4522E871399CD717aBDD847Ab11FE88", 851643))


