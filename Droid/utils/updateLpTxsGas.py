import pymysql
from web3 import Web3
import os
from dotenv import load_dotenv
import time
load_dotenv()

# ---------------- CONFIG ---------------- #

DB_CONFIG = {
	'host': 'localhost',
	'user': 'username',
	'password': 'password',
	'database': 'helix',
	'cursorclass': pymysql.cursors.DictCursor
}


RPC_URL = os.getenv("PROVIDER")  # e.g., Infura or Alchemy
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# ---------------- HELPERS ---------------- #
def get_tx_fee_eth(tx_hash):
	try:
		tx = web3.eth.get_transaction(tx_hash)
		receipt = web3.eth.get_transaction_receipt(tx_hash)
		gas_used = receipt["gasUsed"]
		gas_price = tx["gasPrice"]
		fee_eth = Web3.from_wei(gas_used * gas_price, "ether")
		return float(fee_eth)
	except Exception as e:
		print(f"Error fetching tx fee for {tx_hash}: {e}")
		return None

def update_table_fees(cursor, connection, table_name):
	query = f"SELECT id, tx_hash FROM {table_name} WHERE txFeeETH IS NULL OR txFeeETH = 0"
	cursor.execute(query)
	rows = cursor.fetchall()

	for row in rows:
		time.sleep(2)
		tx_hash = row["tx_hash"]
		fee_eth = get_tx_fee_eth(tx_hash)
		if fee_eth is not None:
			update_query = f"UPDATE {table_name} SET txFeeETH = %s WHERE id = %s"
			cursor.execute(update_query, (fee_eth, row["id"]))
			connection.commit()
			print(f"✅ Updated txFeeETH for {table_name} ID {row['id']} - {fee_eth:.6f} ETH")
		else:
			print(f"⚠️  Skipping update for ID {row['id']}")

# ---------------- MAIN ---------------- #
def main():
	connection = pymysql.connect(**DB_CONFIG)
	cursor = connection.cursor()

	try:
		print("🧪 Updating LpAddLiquTxs table...")
		update_table_fees(cursor, connection, "LpAddLiquTxs")
		print("🧪 Updating LpRemoveLiquTxs table...")
		update_table_fees(cursor, connection, "LpRemoveLiquTxs")
	finally:
		cursor.close()
		connection.close()
		print("✅ Done.")

if __name__ == "__main__":
	main()

