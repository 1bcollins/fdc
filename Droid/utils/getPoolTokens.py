from web3 import Web3


# Replace with your Ethereum node provider URL
INFURA_URL = "https://mainnet.infura.io/v3/aea940137990482ba4e57b44db9fe5f6"
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Uniswap V3 Pool ABI (simplified for the methods we need)
UNISWAP_V3_POOL_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "token0",
        "outputs": [{"name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token1",
        "outputs": [{"name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [
            {"name": "", "type": "address"}
        ],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]

# ERC20 ABI (simplified for balanceOf function)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]


def getBalance(_address, owner):
    contract=web3.eth.contract(address=_address, abi=ERC20_ABI)
    return contract.functions.balanceOf(owner).call()
    
def get_token_balances(_pool_address):
    pool_address=Web3.to_checksum_address(_pool_address)
    pool_contract = web3.eth.contract(address=pool_address, abi=UNISWAP_V3_POOL_ABI)

    # Get token0 and token1 addresses
    token0_address = pool_contract.functions.token0().call()
    token1_address = pool_contract.functions.token1().call()

    # Get balances for token0 and token1 in the pool
    token0_contract = web3.eth.contract(address=token0_address, abi=ERC20_ABI)
    token1_contract = web3.eth.contract(address=token1_address, abi=ERC20_ABI)

    token0_balance = token0_contract.functions.balanceOf(pool_address).call()
    token1_balance = token1_contract.functions.balanceOf(pool_address).call()

    # Return token addresses and balances
    return {
        "token0": {
            "address": token0_address,
            #"balance": web3.from_wei(token0_balance, 'ether')
            "balance": token0_balance
        },
        "token1": {
            "address": token1_address,
            #"balance": web3.from_wei(token1_balance, 'ether')
            "balance": token1_balance
        }
    }

if __name__ == "__main__":
    # Example pool address: USDC/WETH pool on Uniswap V3
    pool_address = "0xc2e9f25be6257c210d7adf0d4cd6e3e881ba25f8"
    poolAddr=Web3.to_checksum_address(pool_address)

    balances = get_token_balances(poolAddr)
    print("Token0 Address:", balances["token0"]["address"])
    print("Token0 Balance:", balances["token0"]["balance"])
    print("Token1 Address:", balances["token1"]["address"])
    print("Token1 Balance:", balances["token1"]["balance"])

