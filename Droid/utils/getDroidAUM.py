import pymysql
import json
from decimal import Decimal
import getErc20Balance
import getFixedPositions
import getMainNetPositions


def get_droid_aum(droid_id: int, wallet_address: str) -> str:
	"""
	Calculate total AUM (Assets Under Management) for a given droid.
	Returns JSON object with asset balances and total USD value.
	"""

	# --- Initialize database ---
	conn = pymysql.connect(host="localhost", user="username", password="password", database="helix")
	cursor = conn.cursor(pymysql.cursors.DictCursor)

	report = {
		"droidId": droid_id,
		"wallet": wallet_address,
		"token0_wallet": 0,
		"token1_wallet": 0,
		"eth_wallet": 0,
		"token0_positions": 0,
		"token1_positions": 0,
		"total_token0": 0,
		"total_token1": 0,
		"total_eth": 0,
		"watch_token_price_usd": 0,
		"aum_usd": 0
	}

	# --- Step 1: Get pool data from Droids & LpPools ---
	cursor.execute("""
		SELECT d.poolId, p.token0Address, p.token1Address, p.stableCoinPosition, p.poolAddress 
		FROM Droids d 
		JOIN LpPools p ON d.poolId = p.id 
		WHERE d.id = %s
	""", (droid_id,))
	row = cursor.fetchone()
	if not row:
		return json.dumps({"error": "Droid ID not found"})

	pool_id = row["poolId"]
	token0 = row["token0Address"]
	token1 = row["token1Address"]
	stable_pos = row["stableCoinPosition"]

	# --- Step 2: Get wallet balances (Replace with real calls) ---
	report["eth_wallet"] = getErc20Balance.getEthBalance(wallet_address)
	report["token0_wallet"] = getErc20Balance.get_erc20_balance(token0, wallet_address)
	report["token1_wallet"] = getErc20Balance.get_erc20_balance(token1, wallet_address)
	
	
	LpPositionsStat = getFixedPositions.main(wallet_address, pool_id)
	for pos in LpPositionsStat['positions']:
		print(pos)
		print()
	
	'''
	# --- Step 3: Get NFT positions for this droid ---
	nft_numbers = get_nft_array(droid_id, cursor)  # your pre-built helper

	# --- Step 4: Sum token balances from all positions ---
	for nft in nft_numbers:
		pos_balances = get_nft_balances(nft)  # your pre-built helper
		report["token0_positions"] += pos_balances["token0"]
		report["token1_positions"] += pos_balances["token1"]

	# --- Step 5: Total balances ---
	report["total_token0"] = report["token0_wallet"] + report["token0_positions"]
	report["total_token1"] = report["token1_wallet"] + report["token1_positions"]
	report["total_eth"] = report["eth_wallet"]

	# --- Step 6: USD Valuation ---
	watch_price_usd = get_watch_token_price_usd(pool_id)  # your helper
	report["watch_token_price_usd"] = watch_price_usd

	if stable_pos == 0:
		# token1 is watch coin
		report["aum_usd"] = float(report["total_token0"]) + float(report["total_token1"]) * watch_price_usd
	else:
		# token0 is watch coin
		report["aum_usd"] = float(report["total_token1"]) + float(report["total_token0"]) * watch_price_usd

	# --- Finalize ---
	cursor.close()
	conn.close()
	return json.dumps(report, indent=4)
	'''


# ---------- EXECUTE ---------- #
if __name__ == "__main__":
	droid_id, wallet_address = 3, "0x7BF2bd6B212Ad91A5B4686fC1e504CC708461C0e"
	get_droid_aum(droid_id, wallet_address)
