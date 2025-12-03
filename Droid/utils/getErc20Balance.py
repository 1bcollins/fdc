from web3 import Web3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
INFURA_URL = os.getenv("PROVIDER")  # Replace with your Infura/Alchemy/Node URL

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

# ERC-20 Token ABI (Minimal)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]

def fixDecimals(token_address, amountWei):
    """Returns the balance of an ERC-20 token for a given owner."""
    token_contract = web3.eth.contract(address=web3.to_checksum_address(token_address), abi=ERC20_ABI)
    
    # Get raw balance
    #raw_balance = token_contract.functions.balanceOf(web3.to_checksum_address(owner_address)).call()
    
    # Get token decimals to format balance
    decimals = token_contract.functions.decimals().call()
    
    # Convert balance to human-readable format
    amount = amountWei / (10 ** decimals)
    
    return amount


def get_erc20_balance(token_address, owner_address):
    """Returns the balance of an ERC-20 token for a given owner."""
    token_contract = web3.eth.contract(address=web3.to_checksum_address(token_address), abi=ERC20_ABI)
    
    # Get raw balance
    raw_balance = token_contract.functions.balanceOf(web3.to_checksum_address(owner_address)).call()
    
    # Get token decimals to format balance
    decimals = token_contract.functions.decimals().call()
    
    # Convert balance to human-readable format
    balance = raw_balance / (10 ** decimals)
    
    return balance

def get_erc20_balance_wei(token_address, owner_address):
    """Returns the balance of an ERC-20 token for a given owner."""
    token_contract = web3.eth.contract(address=web3.to_checksum_address(token_address), abi=ERC20_ABI)
    
    # Get raw balance
    raw_balance = token_contract.functions.balanceOf(web3.to_checksum_address(owner_address)).call()
    
    # Get token decimals to format balance
    decimals = token_contract.functions.decimals().call()
    
    # Convert balance to human-readable format
    balance = raw_balance #/ (10 ** decimals)
    
    return balance

def getEthBalance(wallet_address):
	# Get balance in wei
	balance_wei = web3.eth.get_balance(wallet_address)
	# Convert to ETH
	balance_eth = web3.from_wei(balance_wei, 'ether')
	return balance_eth


# Example Usage
if __name__ == "__main__":
    TOKEN_ADDRESS = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"  # DAI on Polygon
    OWNER_ADDRESS = "0x7BF2bd6B212Ad91A5B4686fC1e504CC708461C0e"
    
    balance = get_erc20_balance(TOKEN_ADDRESS, OWNER_ADDRESS)
    print(f"Balance: {balance}")

