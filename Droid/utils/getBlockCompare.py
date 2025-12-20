import requests
import json
from dotenv import load_dotenv
import os

# Load .env variables
load_dotenv()

INFURA_URL = os.getenv("PROVIDER")
SUBGRAPH_URL = os.getenv("SUBGRAPH_URL")

SUBGRAPH_QUERY = {
	"query": """
	{
		_meta {
			block {
				number
			}
		}
	}
	"""
}

INFURA_REQUEST = {
	"jsonrpc": "2.0",
	"method": "eth_blockNumber",
	"params": [],
	"id": 1
}

def get_subgraph_block():
	try:
		response = requests.post(SUBGRAPH_URL, json=SUBGRAPH_QUERY)
		response.raise_for_status()
		data = response.json()
		return int(data["data"]["_meta"]["block"]["number"])
	except Exception as e:
		print("Error fetching Subgraph block:", e)
		return None

def get_infura_block():
	try:
		response = requests.post(INFURA_URL, json=INFURA_REQUEST)
		response.raise_for_status()
		data = response.json()
		return int(data["result"], 16)
	except Exception as e:
		print("Error fetching Infura block:", e)
		return None

def compare_blocks():
	sg_block = get_subgraph_block()
	infura_block = get_infura_block()

	if sg_block is None or infura_block is None:
		print("Could not fetch all block numbers.")
		return

	difference = infura_block - sg_block

	print("\n=== BLOCK COMPARISON ===")
	print(f"Subgraph block     : {sg_block}")
	print(f"Ethereum (Provider): {infura_block}")
	print(f"Difference (lag)   : {difference} blocks\n")

	'''
	if abs(difference) <= 5:
		print("✔ Subgraph is up-to-date (within 5 blocks).")
	else:
		print("⚠ Subgraph is lagging behind significantly.")
	'''
	
	return difference, infura_block, sg_block

if __name__ == "__main__":
	diff=compare_blocks()
	print(diff)
