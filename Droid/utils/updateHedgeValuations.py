import pymysql
import json
import requests

# ---------- CONFIG ---------- #
DB_CONFIG = {
	'host': 'localhost',
	'user': 'username',
	'password': 'password',
	'database': 'helix',
	'cursorclass': pymysql.cursors.DictCursor
}


def getDroidRecord(droidId, cursor):
    cursor.execute("SELECT * FROM Droids WHERE id = %s", (droidId,))
    return cursor.fetchone()

def getAccountRecord(accountId, cursor):
    cursor.execute("SELECT * FROM Accounts WHERE id = %s", (accountId,))
    return cursor.fetchone()


def fetch_hedge_valuation_api(droid_id: int, cursor, conn) -> dict:
	"""
	Fetches hedge valuation data from the Helix API for a given droid ID.
	Returns the data as a Python dictionary.
	"""
	print("Fetching Hedge data....")
	print()
	
	droidRecord=getDroidRecord(droid_id, cursor)
	poolId=droidRecord['poolId']	#getPoolId(droid_id)
	accountRecord=getAccountRecord(droidRecord['hedgeAccount'], cursor)
	walletAddr=accountRecord['address']	#"0xA6788E6777F9CefFe2F28f9c3F2041F2398cee70"	
	url = f"http://208.104.246.47:8080/run?script=GetAccountPositions&address={walletAddr}&params=[{poolId}]"

	try:
		response = requests.get(url, timeout=10)
		response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
		data = response.json()
		return data
	except requests.exceptions.RequestException as e:
		print(f"❌ Error fetching API data for droidId {droid_id}: {e}")
		return {}



def insert_hedge_valuation(droid_id, data, cursor, connection):
	"""
	Inserts a hedge valuation record into the HedgeValuations table.

	Args:
		droid_id (int): The ID of the droid associated with this valuation.
		data (dict): A dictionary containing the API response fields.
		cursor: A MySQL cursor object.
		connection: A MySQL connection object.
	"""

	sql = """
		INSERT INTO HedgeValuations (
			droidId,
			token0_wallet, token1_wallet, eth_wallet,
			token0_positions, token1_positions,
			total_token0, total_token1, total_eth,
			watch_token_price_usd, wallet_total_USD,
			wallet, t1USD, t0USD
		) VALUES (
			%(droidId)s,
			%(token0_wallet)s, %(token1_wallet)s, %(eth_wallet)s,
			%(token0_positions)s, %(token1_positions)s,
			%(total_token0)s, %(total_token1)s, %(total_eth)s,
			%(watch_token_price_usd)s, %(wallet_total_USD)s,
			%(wallet)s, %(t1USD)s, %(t0USD)s
		)
	"""

	params = {
		'droidId': droid_id,
		'token0_wallet': data.get('token0_wallet', 0),
		'token1_wallet': data.get('token1_wallet', 0),
		'eth_wallet': data.get('eth_wallet', 0),
		'token0_positions': data.get('token0_positions', 0),
		'token1_positions': data.get('token1_positions', 0),
		'total_token0': data.get('total_token0', 0),
		'total_token1': data.get('total_token1', 0),
		'total_eth': data.get('total_eth', 0),
		'watch_token_price_usd': data.get('watch_token_price_usd', 0),
		'wallet_total_USD': data.get('wallet_total_USD', 0),
		'wallet': data.get('wallet', ''),
		't1USD': data.get('t1USD', 0),
		't0USD': data.get('t0USD', 0),
	}

	try:
		cursor.execute(sql, params)
		connection.commit()
		print("✅ HedgeValuations record inserted.")
	except Exception as e:
		print("❌ Error inserting hedge valuation:", e)
		connection.rollback()
		
def insertHedgeValuation(droidId):
	# DB connection
	#conn = pymysql.connect(host="localhost", user="username", password="password", database="helix")
	conn = pymysql.connect(**DB_CONFIG)
	cursor = conn.cursor()
	
	
	api_response=fetch_hedge_valuation_api(droidId, cursor, conn)
	# Insert
	insert_hedge_valuation(droidId, api_response, cursor, conn)

	cursor.close()
	conn.close()
	
if __name__ == "__main__":
	droidId=int(input("Input droid id: "))
	insertHedgeValuation(droidId)	
	
	


