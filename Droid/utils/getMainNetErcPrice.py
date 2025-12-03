from web3 import Web3
import requests
import logging

# Connect to Ethereum Mainnet node
infura_url = "https://mainnet.infura.io/v3/aea940137990482ba4e57b44db9fe5f6"
web3 = Web3(Web3.HTTPProvider(infura_url))

# Set up logging configuration
logging.basicConfig(level=logging.INFO)

def getEthBalance(wallet_address):
    #web3.eth.get_balance('0xd3CdA913deB6f67967B99D67aCDFa1712C293601')
    provider_url= "https://mainnet.infura.io/v3/aea940137990482ba4e57b44db9fe5f6"
    web3 = Web3(Web3.HTTPProvider(provider_url))
    wei=web3.eth.get_balance(wallet_address)
    return (wei/(10**18))

def get_erc20_balance(wallet_address, token_address):
    """Get the balance of an ERC-20 token for a wallet address."""
    # Ensure the connection is successful
    if not web3.is_connected():
        raise Exception("Failed to connect to the Ethereum network")

    # Define the ERC20 contract ABI
    erc20_abi = [
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
        }
    ]
    
    # Convert token_address to checksum format
    token_address = Web3.to_checksum_address(token_address)
    
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
    """Fetch token price from CoinGecko API for Ethereum."""
    url = f"https://api.coingecko.com/api/v3/simple/token_price/ethereum?contract_addresses={contract_address}&vs_currencies=usd"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from CoinGecko: {e}")
        return 0

    # Convert the contract address to lowercase for comparison
    res = response.json()
    contract_address_lower = contract_address.lower()
    if contract_address_lower in res and "usd" in res[contract_address_lower]:
        return res[contract_address_lower]["usd"]
    else:
        print(f"{contract_address} not available from CoinGecko.")
        return 0

def get_token_price(token_address: str) -> float:
    """Get the price of a token directly from CoinGecko, return 0 if unavailable."""
    try:
        return fetch_cg_token_price(token_address)
    except ValueError:
        # Log the issue and return 0 as a fallback
        print(f"Failed to retrieve price for {token_address}, returning 0.")
        return 0

# Example usage:
if __name__ == "__main__":
    wallet_address = "0xec92fdC275B81165317a58Ad50D5D134828c2f67"  # Replace with the wallet address you want to check
    token_address = "0x6B175474E89094C44Da98b954EedeAC495271d0F"    # Replace with the ERC20 token address

    try:
        balance = get_erc20_balance(wallet_address, token_address)
        price = get_token_price(token_address)
        print(f"The balance of the token is: {balance}")
        print(f"The price of the token is: ${price}")
    except Exception as e:
        print(f"An error occurred: {e}")

