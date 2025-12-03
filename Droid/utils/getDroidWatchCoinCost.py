import pymysql
import json

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
			SUM({watchCoin}) AS amount,
			COUNT(id) AS txCount
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
		return json.dumps({ "error": f"Database error: {str(e)}" })
	finally:
		conn.close()

	if additionsResults["amount"] is None or removesResults["amount"] is None:
		return json.dumps({ "error": f"No data available for droidId {droidId}" })

	watchCoinAccum = removesResults["amount"] - additionsResults["amount"]

	watchCoinPurchasePriceDelta = (
		additionsResults["weighted_average"] - removesResults["weighted_average"]
	)

	stableCoinDiff = stableRemsResults["amount"] - stableAddResults["amount"]

	output = {
		"droidId": droidId,
		"watchCoinAccumulated": float(watchCoinAccum),
		"avgRemovedPrice": float(round(removesResults["weighted_average"], 4)),
		"avgAddPrice": float(round(additionsResults["weighted_average"], 4)),
		"additionsPurchaseDelta": float(round(watchCoinPurchasePriceDelta, 4)),
		"watchCoinRemoved": float(removesResults["amount"]),
		"watchCoinAdded": float(additionsResults["amount"]),
		"stableCoinAdded": float(stableAddResults["amount"]),
		"stableCoinRemoved": float(stableRemsResults["amount"]),
		"stableCoinAccumulated": float(stableCoinDiff),
		"txCount": removesResults["txCount"]
	}
	#print(output)
	return output	#json.dumps(output, indent=2)


# === Example usage ===
if __name__ == "__main__":
	import sys
	droidId = int(input("Enter droid ID: "))
	if droidId==0:
		droidCount=18	#TODO: get droid count
		while (droidId<droidCount):
			droidId=droidId+1
			result = run(droidId, stableCoinPos=1)
			print(result)
	else:
		result = run(droidId, stableCoinPos=1)
		print(result)

