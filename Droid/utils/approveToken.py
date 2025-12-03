from web3 import Web3
import json
import os
import getMainNetGas
from dotenv import load_dotenv
from web3.exceptions import ContractLogicError

load_dotenv()

# Load environment variables
INFURA_URL = os.getenv("PROVIDER")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("ADDRESS")

web3 = Web3(Web3.HTTPProvider(INFURA_URL))


def check_allowance(token_address, spender):
	
	token_abi = json.loads(open("ERC20.json").read())  
	token_contract = web3.eth.contract(address=token_address, abi=token_abi)

	allowance = token_contract.functions.allowance(WALLET_ADDRESS, spender).call()
	balance = token_contract.functions.balanceOf(WALLET_ADDRESS).call()

	print(f"Allowance: {allowance}, Balance: {balance}")

	return allowance, balance


def estimateApproveGas(token_address, spender, amount):
	"""Approve ERC-20 token transfer for Uniswap contract."""
	token_abi = json.loads(open("ERC20.json").read())  # Load ERC-20 ABI
	token_contract = web3.eth.contract(address=token_address, abi=token_abi)
	
	print("approve_token data: ", token_address, spender, amount)
	estimated_gas = token_contract.functions.approve(spender, amount).estimate_gas({
		"from": WALLET_ADDRESS
	})
	return estimated_gas

# Approve tokens for spending
#Entry Point
#NOTE max amount = 115792089237316195423570985008687907853269984665640564039457584007913129639935
def approve_token(token_address, spender, amount):
	apprError=True
	res="error"
	allowance, balance=check_allowance(token_address, spender)
	if balance<amount:
		print()
		print("INSUFFICIENT FUNDS FOR APPROVE TOKEN!")
		print("CHANGING APPROVE AMOUNT TO BALANCE!")
		print()
		amount=int(balance*.95)
		#return res
	if allowance==0:
		apprError=_approveToken(token_address, spender, amount)
	if allowance>=amount:
		print("NOTE: spending is preApproved")
		print()
		res="approved"
		return res
	if allowance<amount:
		apprError=_approveToken(token_address, spender, 0)	#set allowance to zero
		apprError=_approveToken(token_address, spender, amount)	#set allowance to 'amount'
		res="error" if apprError else "approved"
		
	return res
	
	
def _approveToken(token_address, spender, amount):
	error=True
	#helper fuction. see entry at "approve_token" func'
	"""Approve ERC-20 token transfer for Uniswap contract."""
	token_abi = json.loads(open("ERC20.json").read())  # Load ERC-20 ABI
	token_contract = web3.eth.contract(address=token_address, abi=token_abi)
	
	print("approve_token data: ", token_address, spender, amount)
	
	estimated_gas =estimateApproveGas(token_address, spender, amount)
	
	
	gasPriceGwei=getMainNetGas.getGasPrice() 
	gasPrice=int(gasPriceGwei * 1e9)
	print(f"gasPrice for Approve: {gasPriceGwei}")
	print()
	# Build transaction
	txn = token_contract.functions.approve(spender, amount).build_transaction({
		"from": WALLET_ADDRESS,
		"gas": int(estimated_gas*1.2) + 0,
		"gasPrice": gasPrice,
		"nonce": web3.eth.get_transaction_count(WALLET_ADDRESS),
	})

	# Sign and send transaction
	signed_txn = web3.eth.account.sign_transaction(txn, PRIVATE_KEY)
	tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
	#web3.eth.wait_for_transaction_receipt(tx_hash)
	try:
		print("waiting for tx reciept")
		receipt = web3.eth.wait_for_transaction_receipt(
			tx_hash, timeout=300, poll_latency=2.0
		)
		print(f"Transaction confirmed: {receipt}")
		print()
		error=False
	except Exception as e:
		print(f"Error while waiting for transaction receipt: {e}")
		error=True
	
	print(f"Approved {token_address} for spending. Txn Hash: {tx_hash.hex()}")
	return error
	
if __name__ == "__main__":
	token_address=input("Token address: ")	#0xdAC17F958D2ee523a2206206994597C13D831ec7"
	#token_address=token_address.lower()
	spender="0xC36442b4a4522E871399CD717aBDD847Ab11FE88"
	amount= int(input("Amount to approve in wei: "))	#402840710
	
	allowance, balance=check_allowance(token_address, spender)
	print("Allowance: ", allowance)
	print("Balance: ", balance)
	getEst=input("Get Gas est. ? (y/n)")
	if getEst=="y":
		gasEstimate=estimateApproveGas(token_address, spender, amount)
		print(gasEstimate)
	
	appr=input("Call approve (y/n): ")
	if appr=="y":
		approve_token(token_address, spender, amount)
