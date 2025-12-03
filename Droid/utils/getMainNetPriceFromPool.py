from web3 import Web3
import requests
import pymysql

# Connect to Ethereum node
#infura_url = "https://polygon-mainnet.infura.io/v3/f61eb7936eb442039755958c9d3b675b"
infura_url = "https://mainnet.infura.io/v3/aea940137990482ba4e57b44db9fe5f6"
web3 = Web3(Web3.HTTPProvider(infura_url))

# Database connection
conn = pymysql.connect(db='helix', user='username', passwd='password', host='localhost')
cc = conn.cursor()

def getLpPool(erc20Addr):
    #select * from LpPools  where blockChain = 'Ethereum'  and (token0Address = 'erc20Addr}' or token1Address = 'erc20Addr}');
    try:
        #sql = f"select * from LpPools where token0Address='{erc20Addr}' or token1Address='{erc20Addr}'=(select id from LpPools where blockChain='Ethereum');"
        sql = f"select * from LpPools  where blockChain = 'Ethereum'  and (token0Address = '{erc20Addr}' or token1Address = '{erc20Addr}');"
        cc.execute(sql)
        result = cc.fetchall()
        return result[0] if result else None
    except Exception as e:
        print(f"Error fetching asset: {e}")
        return None


erc20_abi = '''[
    {"constant": true, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "payable": false, "stateMutability": "view", "type": "function"}
]'''
uniswap_v3_pool_abi = '''[
    {"constant": true, "inputs": [], "name": "slot0", "outputs": [{"name": "sqrtPriceX96", "type": "uint160"}], "stateMutability": "view", "type": "function"},
    {"constant": true, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"constant": true, "inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"}
]'''


def getPolyBalance(wallet_address):
    #web3.eth.get_balance('0xd3CdA913deB6f67967B99D67aCDFa1712C293601')
    provider_url= "https://polygon-mainnet.infura.io/v3/f61eb7936eb442039755958c9d3b675b"
    web3 = Web3(Web3.HTTPProvider(provider_url))
    wei=web3.eth.get_balance(wallet_address)
    return (wei/(10**18))


def get_erc20_balance(wallet_address, token_address):
    # Connect to the Ethereum network
    provider_url= "https://polygon-mainnet.infura.io/v3/f61eb7936eb442039755958c9d3b675b"
    web3 = Web3(Web3.HTTPProvider(provider_url))

    # Ensure the connection is successful
    if not web3.is_connected():
        raise Exception("Failed to connect to the Ethereum network")

    # Define the ERC20 token contract ABI (simplified)
    erc20_abi = [
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        }
    ]

    # Create a contract instance for the ERC20 token
    token_contract = web3.eth.contract(address=token_address, abi=erc20_abi)

    # Get the balance of the specified wallet address
    balance = token_contract.functions.balanceOf(wallet_address).call()

    # Get the decimals from the ERC20 contract
    decimals = token_contract.functions.decimals().call()

    # Convert the balance to a human-readable format
    human_readable_balance = balance / (10 ** decimals)

    return human_readable_balance

def fetch_cg_token_price(contract_address: str) -> float:
    """Fetch token price from CoinGecko API."""
    # Validate the contract address format if necessary
    if not contract_address.startswith("0x") or len(contract_address) != 42:
        raise ValueError("Invalid contract address format.")
    
    url = f"https://api.coingecko.com/api/v3/simple/token_price/polygon-pos?contract_addresses={contract_address}&vs_currencies=usd"
    
    try:
        response = requests.get(url, timeout=10)  # Set a timeout for the request
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from CoinGecko: {e}")
        raise

    # Print the response for debugging
    res = response.json()
    #logging.info(f"Response from CoinGecko for {contract_address}: {res}")

    # Convert the contract address to lowercase for comparison
    contract_address_lower = contract_address.lower()

    # Check if the contract address and 'usd' key exist in the response
    if contract_address_lower in res and "usd" in res[contract_address_lower]:
        return res[contract_address_lower]["usd"]
    else:
        raise ValueError(f"{contract_address} not available from CoinGecko.")


def address_to_symbol(token_address: str) -> str:
    """Convert a token address to its symbol."""
    return address_to_symbol_map.get(Web3.to_checksum_address(token_address))

def get_token_price(token_address: str) -> float:
    lpPool=getLpPool(token_address)
    #print()
    #print("lpPool: ", lpPool)
    pool_address=lpPool[2]
    token0_address=lpPool[3]
    token1_address=lpPool[4]
    token_position=lpPool[6]
    #token_position=1 if token_position==0 else token_position=1
    #print()
    #print("token_psoitio: ", token_position)
    #print()
    isRequTokenStableCoin=False if token0_address==token_address else True
    #print()
    #print("isRequTokenStableCoin: ", isRequTokenStableCoin)
    #print()
    
    pool_contract = web3.eth.contract(address=Web3.to_checksum_address(pool_address), abi=uniswap_v3_pool_abi)
    # Fetch token addresses and decimals for price calculation
    token0_address, token1_address = pool_contract.functions.token0().call(), pool_contract.functions.token1().call()
    token0_decimals = web3.eth.contract(address=token0_address, abi=erc20_abi).functions.decimals().call()
    token1_decimals = web3.eth.contract(address=token1_address, abi=erc20_abi).functions.decimals().call()

    # Attempt to call slot0 and handle different output structures
    try:
        slot0 = pool_contract.functions.slot0().call()
        
        # If slot0 is a single integer, use it directly as sqrtPriceX96
        if isinstance(slot0, int):
            sqrt_price_x96 = slot0
        elif isinstance(slot0, (list, tuple)) and len(slot0) > 0:
            sqrt_price_x96 = slot0[0]
        else:
            raise ValueError(f"Unexpected slot0 data structure: {slot0}")

    except Exception as e:
        raise ValueError(f"Failed to retrieve slot0 data: {e}")

    # Calculate price based on token position
    price_token0_in_token1 = ((sqrt_price_x96 / (2 ** 96)) ** 2) * (10 ** (token0_decimals - token1_decimals))
    #return price_token0_in_token1 if token_position == 0 else (1 / price_token0_in_token1)
    watchCoinPrice=price_token0_in_token1 if token_position == 1 else (1 / price_token0_in_token1)
    #return price_token0_in_token1 if token_position == 1 else (1 / price_token0_in_token1)
    return watchCoinPrice if isRequTokenStableCoin!=True else (1.00)	#!!!!!!!!!!!!!! change for case where stable coin is failing!!!!
    


if __name__ == "__main__":
	#r=get_token_price("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2")
	#r=get_token_price("0xdac17f958d2ee523a2206206994597c13d831ec7")
	erc20Addr=input("input token addr: ")
	r=get_token_price(erc20Addr)
	print(r)
	


