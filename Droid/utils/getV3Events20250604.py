from web3 import Web3
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
INFURA_URL = os.getenv("PROVIDER")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("ADDRESS")


# Get the path of the ABI file
abi_file = os.path.join(os.path.dirname(__file__), "v3NftPosManagerAbi.json")

# Load the contract ABI from the JSON file
with open(abi_file, "r") as f:
    contract_abi = json.load(f)


# Connect to an Ethereum/Polygon node
w3=Web3(Web3.HTTPProvider(INFURA_URL))

def get_transaction_events1(tx_hash, contract_address, contract_abi):
    """
    Retrieves and decodes events associated with a transaction.

    :param tx_hash: The transaction hash.
    :param contract_address: The contract that emitted the event.
    :param contract_abi: The contract's ABI.
    :return: List of decoded events.
    """
    # Fetch transaction receipt
    receipt = w3.eth.get_transaction_receipt(tx_hash)

    # Load contract
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    decoded_events = []
    #print(contract.events)
    #print()
    # Process each log
    for log in receipt.logs:
        # Check if the log is from the target contract
        print(log.topics[0])
        print()
        if log.address.lower() == contract_address.lower():
            try:
                # Decode log using contract ABI
                event = contract.events._find_matching_event_abi(log.topics[0])
                #event = contract.events.Transfer(log.topics[0])
                decoded_data = contract.events[event['name']]().process_log(log)
                decoded_events.append(decoded_data)
            except Exception as e:
                print(f"Error decoding log: {e}")

    return decoded_events

def get_transaction_events(tx_hash, contract_address):	#, contract_abi):
    """
    Retrieves and decodes events associated with a transaction.

    :param tx_hash: The transaction hash.
    :param contract_address: The contract that emitted the event.
    :param contract_abi: The contract's ABI.
    :return: List of decoded events.
    """
    # Get transaction receipt
    receipt = w3.eth.get_transaction_receipt(tx_hash)

    # Load contract
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    decoded_events = []

    # Loop through all logs in the receipt
    for log in receipt.logs:
        if log.address.lower() == contract_address.lower():
            for event_name in contract.events.__dict__:  # Get all event names as strings
                try:
                    event_class = getattr(contract.events, event_name)  # Get the event class
                    decoded_event = event_class().process_log(log)  # Decode the log
                    decoded_events.append(decoded_event)
                except Exception as e:
                    pass  # Skip if the log doesn't match this event

    return decoded_events

def findNftId(tx_hash):
	contract_address = "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"
	events = get_transaction_events(tx_hash, contract_address)	#, contract_abi)
	tokenId=0
	for event in events:
		#print()
		#print("event: ", event)
		if(event['event']=="Transfer"):
			tokenId=event['args']['tokenId']
	return tokenId

if __name__ == "__main__":
	# Example usage
	tx_hash = "0xe0d79652a937d42dddf94359be109e094bccd2e0fff9b0b6d5ec0a7e166a4c10"
	contract_address = "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"
	#contract_abi = [...]  # Load contract ABI
	
	'''
	events = get_transaction_events(tx_hash, contract_address)	#, contract_abi)
	for event in events:
		print()
		print("event: ", event)
	'''
	t=findNftId(tx_hash)
	print(t)
