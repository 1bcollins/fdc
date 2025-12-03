import getTick
import getPolyPoolData
import pymysql
import time
import os

from dotenv import load_dotenv
load_dotenv()

WALLET_ADDRESS = os.getenv("ADDRESS")


def init_db():
	"""Initialize global database connection and cursor."""
	global conn, cc
	conn = pymysql.connect(
		db="helix",
		user="username",
		passwd="password",
		host="localhost",
		cursorclass=pymysql.cursors.DictCursor,
	)
	cc = conn.cursor()

def getPoolId(botId):
	"""Fetch poolId for the given botId."""
	sql = f"SELECT poolId FROM PositionBots WHERE id={botId}"
	cc.execute(sql)
	result = cc.fetchone()
	return result["poolId"] if result else None

def getLpPool(poolId):
	"""Fetch liquidity pool details for the given poolId."""
	sql = f"SELECT * FROM LpPools WHERE id={poolId}"
	cc.execute(sql)
	return cc.fetchone()

def getEntranceConditional(botId):
	"""Fetch entrance conditional settings for the given botId."""
	sql = f"SELECT * FROM EntranceConditionals WHERE botId={botId}"
	cc.execute(sql)
	return cc.fetchone()

def translateEntranceConds(botId):
	"""Translate entrance conditions into Uniswap parameters."""
	init_db()  # Ensure DB is initialized

	poolId = getPoolId(botId)
	if not poolId:
		print("Error: No poolId found for botId", botId)
		return

	lpPool = getLpPool(poolId)
	if not lpPool:
		print("Error: No LP pool data found for poolId", poolId)
		return
	print("lpPool: ", lpPool)
	print()
	
	entranceConditionals = getEntranceConditional(botId)
	print("entranceConditionals: ", entranceConditionals)
	print()
	if not entranceConditionals:
		print("Error: No entrance conditionals found for botId", botId)
		return

	# Fetch pool blockchain data
	pool_address = lpPool["poolAddress"]
	stableCoinPosition = lpPool["stableCoinPosition"]
	poolStatus = getPolyPoolData.get_uniswap_v3_pool_data(pool_address, stableCoinPosition)
	print("poolStatus: ", poolStatus)
	print()
	# Extract required data from pool
	centerPrice=entranceConditionals['centerPrice']
	currPricePerWatchCoin = poolStatus["pricePerWatchCoin"] if centerPrice==0.00 else centerPrice
	tick_spacing = poolStatus["tick_spacing"]
	token0 = poolStatus["token0"]
	token1 = poolStatus["token1"]
	pool_fee = lpPool["feeTier"]
	
	
	# Extract conditional parameters
	spread = entranceConditionals["spread"]
	percentHigh = float(entranceConditionals["percentHigh"])
	print(percentHigh)
	percentLow = float(entranceConditionals["percentLow"])
	maxStableCoinAmount = entranceConditionals["maxStableCoinAmount"]
	maxWatchCoinAmount = entranceConditionals["maxWatchCoinAmount"]

	# Calculate upper and lower price bounds
	upperWatchCoinPrice = currPricePerWatchCoin + (spread * percentHigh)
	lowerWatchCoinPrice = currPricePerWatchCoin - (spread * percentLow)
	print("upperWatchCoinPrice: ", upperWatchCoinPrice)
	print("lowerWatchCoinPrice: ", lowerWatchCoinPrice)

	#Fix 'CoinPrice with coins decimals to 'wei'
	dec0=poolStatus['token0_decimals']
	dec1=poolStatus['token1_decimals']
	stableCoinDecimals=poolStatus['token0_decimals'] if (stableCoinPosition==0) else poolStatus['token1_decimals']
	watchCoinDecimals=poolStatus['token0_decimals'] if (stableCoinPosition==1) else poolStatus['token1_decimals']
	upperWatchCoinPrice=int(upperWatchCoinPrice*10**stableCoinDecimals)
	lowerWatchCoinPrice=int(lowerWatchCoinPrice*10**stableCoinDecimals)
	print("upperWatchCoinPrice (wei): ", upperWatchCoinPrice)
	print("lowerWatchCoinPrice (wei): ", lowerWatchCoinPrice)
	currPricePerTick=(1.0001**poolStatus['current_tick'])/(10**(poolStatus['token1_decimals']-poolStatus['token0_decimals']))
	print("currPricePerTick: ", currPricePerTick)
	print()
	print("dec0: ", dec0)
	print("dec1: ", dec1)
	
	#Note IF stableCoinPos==1 THEN tickPrice=WatchCoin/StableCoin ELSE tickPrice=StableCoin/WatchCoin
	tick_upper=getTick.price_to_tick(tick_spacing, upperWatchCoinPrice, dec0, dec1) if (stableCoinPosition==1) else getTick.price_to_tick(tick_spacing, 1/upperWatchCoinPrice, dec0, dec1)
	#lowerWatchCoinPrice=currPricePerWatchCoin-spread*percentLow
	tick_lower=getTick.price_to_tick(tick_spacing, lowerWatchCoinPrice, dec0, dec1) if (stableCoinPosition==1) else getTick.price_to_tick(tick_spacing, 1/lowerWatchCoinPrice, dec0, dec1)

	# Determine asset allocation
	if stableCoinPosition == 0:
		amount0_desired = int(maxStableCoinAmount*10**stableCoinDecimals)
		amount1_desired = int(maxWatchCoinAmount*10**watchCoinDecimals)
	else:
		amount0_desired = int(maxWatchCoinAmount*10**watchCoinDecimals)
		amount1_desired = int(maxStableCoinAmount*10**stableCoinDecimals)

	# Output parameters
	return {
		"token0": token0,
		"token1": token1,
		"fee": pool_fee,
		"tickLower": tick_lower,
		"tickUpper": tick_upper,
		"amount0Desired": amount0_desired,
		"amount1Desired": amount1_desired,
		"amount0Min": 0,  # Minimum amount0 (slippage tolerance)
		"amount1Min": 0,  # Minimum amount1 (slippage tolerance)
		"recipient": WALLET_ADDRESS,
		"deadline": int(time.time()) + 30,	#600,  # Deadline (10 minutes)
	}

if __name__ == "__main__":
	botId = int(input("Enter bot id: "))
	result = translateEntranceConds(botId)
	if result:
		print(result)

