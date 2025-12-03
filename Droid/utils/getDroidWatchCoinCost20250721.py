import pymysql

# === Step 0: Define your database config ===
DB_CONFIG = {
	"host": "localhost",
	"user": "username",
	"password": "password",
	"database": "helix",
	"cursorclass": pymysql.cursors.DictCursor
}

def run(droidId, stableCoinPos):
	if stableCoinPos == 1:
		stableCoin = "amount1"
		watchCoin = "amount0"
	else:
		stableCoin = "amount0"
		watchCoin = "amount1"

	additionsQuery = f"""
		SELECT 
			SUM(amountUSD - {stableCoin}) / SUM({watchCoin}) AS weighted_average,
			SUM({watchCoin}) AS amount
		FROM LpAddLiquTxs
		WHERE droidId = {droidId};
	"""

	removesQuery = f"""
		SELECT 
			SUM(amountUSD - {stableCoin}) / SUM({watchCoin}) AS weighted_average,
			SUM({watchCoin}) AS amount, COUNT(id) AS txCount
		FROM LpRemoveLiquTxs
		WHERE droidId = {droidId};
	"""

	stableAddQuery = f"""
		SELECT 
			SUM({stableCoin}) AS amount
		FROM LpAddLiquTxs
		WHERE droidId = {droidId};
	"""

	stableRemsQuery = f"""
		SELECT 
			SUM({stableCoin}) AS amount
		FROM LpRemoveLiquTxs
		WHERE droidId = {droidId};
	"""



	# === Step 1: Connect to DB and execute ===
	try:
		conn = pymysql.connect(**DB_CONFIG)
		with conn.cursor() as cursor:
			cursor.execute(additionsQuery)
			additionsResults = cursor.fetchone()

			cursor.execute(removesQuery)
			removesResults = cursor.fetchone()

			cursor.execute(stableAddQuery)
			stableAddResults = cursor.fetchone()			

			cursor.execute(stableRemsQuery)
			stableRemsResults = cursor.fetchone()			

	except Exception as e:
		print("Database error:", e)
		return
	finally:
		conn.close()

	# === Step 2: Perform calculation ===
	if additionsResults["amount"] is None or removesResults["amount"] is None:
		print("No data available for droidId", droidId)
		return

	watchCoinAccum = removesResults["amount"] - additionsResults["amount"]
	
	'''
	watchCoinPurchasePrice = (
		removesResults["weighted_average"] + additionsResults["weighted_average"]
	) / 2
	'''
	#watchCoinPurchasePrice = removesResults["weighted_average"]
	
	
	watchCoinPurchasePriceDelta = (
		additionsResults["weighted_average"] - removesResults["weighted_average"]
	)

	# === Step 3: Output ===
	print(f"Droid ID: {droidId}")
	print(f"Watch Coin Accumulated: {watchCoinAccum}")
	print(f"Avg Purchase Price: {removesResults["weighted_average"]:.4f}")
	print(f"Additions Purchase Delta: {watchCoinPurchasePriceDelta:.4f}")
	print(f"Watch Coin 'baught': {removesResults['amount']}")
	print(f"Watch Coin 'sold': {additionsResults['amount']}")
	print(f"Stable Coin Added: {stableAddResults['amount']}")
	print(f"Stable Coin Removed: {stableRemsResults['amount']}")
	stableCoinDiff=stableRemsResults['amount']-stableAddResults['amount']
	print(f"Stable coin difference: {stableCoinDiff}")
	
	print(f"TX Count: {removesResults['txCount']}")

# Example run
if __name__ == "__main__":
	droidId=int(input("Enter droid ID: "))
	
	run(droidId, stableCoinPos=1)  # Set your own values here




