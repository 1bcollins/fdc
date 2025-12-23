import getMainNetPositions
import getPoolTokens
import time
import pymysql
import getPoolData
import insertLpPosValuation
import getErc20Balance
import getPoolSymbols
import newNftInserts
import getV3Events
import getMainNetGas
from datetime import date, timedelta
import sys
import getGasBase
import feeRates
import getMainNetErcPrice
import json
from decimal import Decimal
import getBlockCompare

def convert_decimals(obj):
    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, Decimal):
        return float(obj)  # or str(obj) if you want precision preserved as text
    else:
        return obj


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
	# Set session-level isolation mode before creating the main cursor
	conn.cursor().execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
	
	cc = conn.cursor()

def close_db():
	global conn, cc
	try:
		cc.close()
	except Exception:
		print()
		print("Error closing data base")
		pass
	try:
		if conn and conn.open:
			conn.close()
	except Exception:
		pass
		print()
		print("Error closing data base")
		pass

#init_db()  # Ensure DB is initialized

def getPoolId(lpPositionId):
	sql=f"SELECT LpPools.id FROM LpPools JOIN LpPositions ON LpPools.poolAddress = LpPositions.poolAddress WHERE LpPositions.id = {lpPositionId}"
	cc.execute(sql)
	poolId=cc.fetchone()
	print()
	print("Pool id: ", poolId)
	ID=poolId['id']
	return ID

def getPoolAddress(poolId):
	"""Fetch liquidity pool details for the given poolId."""
	sql = f"SELECT poolAddress FROM LpPools WHERE id={poolId}"
	cc.execute(sql)
	return cc.fetchone()

def getAssetId(nftNumber):
	sql = f"SELECT id FROM Assets WHERE nftNumber={nftNumber}"
	cc.execute(sql)
	assetId=cc.fetchone()
	aId=assetId['id']
	return aId

def getLpPosition(nftNumber):
	sql = f"SELECT id FROM LpPositions WHERE nftNumber={nftNumber}"
	cc.execute(sql)
	lpId=cc.fetchone()
	lId=lpId['id'] if lpId!=None else 0
	return lId

	
def getOriginalPosUSDValue(nftNumber):
	try:
		assetId=getAssetId(nftNumber)
		sql = f"select * from LpValuations where assetId={assetId} order by id limit 1"
		cc.execute(sql)
		record=cc.fetchone()
		valueUSD=record['liquidity_amount_token0']*record['token0_priceUSD'] + record['liquidity_amount_token1']*record['token1_priceUSD']
		feesUSD=record['uncollected_fees_token0']*record['token0_priceUSD'] + record['uncollected_fees_token1']*record['token1_priceUSD']
	except:
		valueUSD=0
		feesUSD=0
	return valueUSD, feesUSD
	
def getCurrentPosUSDValue(nftNumber):
	try:
		assetId=getAssetId(nftNumber)
		sql = f"select * from LpValuations where assetId={assetId} order by id desc limit 1"
		cc.execute(sql)
		record=cc.fetchone()
		valueUSD=record['liquidity_amount_token0']*record['token0_priceUSD'] + record['liquidity_amount_token1']*record['token1_priceUSD']
		feesUSD=record['uncollected_fees_token0']*record['token0_priceUSD'] + record['uncollected_fees_token1']*record['token1_priceUSD']
	except Exception as e:
		#print(f"Get pos value error: {e}")
		#print("record: ", record)
		valueUSD=0
		feesUSD=0
	
	
	return valueUSD, feesUSD
	
	
def get24HourGasPrices():
	current_date = date.today()
	next_date = current_date + timedelta(days=1)  # adds 1 day
	sql=f"select MIN(price2) from MainNetGasPrices where timeStamp>'{current_date}' AND timeStamp<'{next_date}'"
	cc.execute(sql)
	minGas=cc.fetchone()
	sql=f"select MAX(price2) from MainNetGasPrices where timeStamp>'{current_date}' AND timeStamp<'{next_date}'"
	cc.execute(sql)
	maxGas=cc.fetchone()
	sql=f"select AVG(price2) from MainNetGasPrices where timeStamp>'{current_date}' AND timeStamp<'{next_date}'"
	cc.execute(sql)
	avgGas=cc.fetchone()
	return minGas, maxGas, avgGas

def getPosNFT(lpPositionId):
	sql = f"SELECT assetId FROM LpPositions WHERE id={lpPositionId}"
	cc.execute(sql)
	assetId=cc.fetchone()
	print(assetId['assetId'])
	a=assetId['assetId']
	sql = f"SELECT nftNumber FROM Assets WHERE id={a}"
	cc.execute(sql)
	return cc.fetchone()


def getPoolAddressesList():
	print("do something to get pool address from DB !!!!!!!!!!")
	
	#temporary
	poolAddresses=["0x9b08288c3be4f62bbf8d1c20ac9c5e6f9467d8b7", "0xeEF1A9507B3D505f0062f2be9453981255b503c8"]
	return poolAddresses

 
def getLpPoolsWatchAddr(poolAddress, watchCoinPos):
	print("finding watch coin's address")
	addrField="token0Address" if watchCoinPos==0 else "token1Address"
	sql = f"SELECT {addrField} FROM LpPools WHERE poolAddress={poolAddress}"
	cc.execute(sql)
	addr=cc.fetchone()
	print(addr[addrField])
	a=addr[addrField]
	return a

'''
def getStableCoinPos(lpPosId):
	print("finding stable coin")
	sql = f"SELECT stableCoinPosition FROM LpPositions WHERE id={lpPosId}"
	cc.execute(sql)
	pos=cc.fetchone()
	print(pos['stableCoinPosition'])
	p=pos['stableCoinPosition']
	return p
'''	
		
def get_price_from_tick(tick: int) -> float:
    return 1.0001 ** tick

def getPriceFromTick(tick, poolStatus):
	return (1.0001**tick)/(10**(poolStatus['token1_decimals']-poolStatus['token0_decimals']))


	
def getLpPool(poolId):
	"""Fetch liquidity pool details for the given poolId."""
	sql = f"SELECT * FROM LpPools WHERE id={poolId}"
	cc.execute(sql)
	return cc.fetchone()

def getPolyLpPoolList():
	"""Fetch liquidity pool details for the given poolId."""
	sql = f"SELECT * FROM LpPools WHERE blockChain='Ethereum'"
	cc.execute(sql)
	return cc.fetchall()


def getCoinRatio(current_tick, tick_lower, tick_upper):
	highSide=100*(tick_upper-current_tick)/(tick_upper-tick_lower)
	lowSide=100*(current_tick-tick_lower)/(tick_upper-tick_lower)
	highSide=int(highSide)	#round(highSide,2)
	lowSide=int(lowSide)	#round(lowSide,2)
	return f"{lowSide}:{highSide}"

def translatePosition(pos, poolStatus, stableCoinPos):
	try:
		if not isinstance(pos, dict) or not isinstance(poolStatus, dict):
			raise ValueError("Invalid input: 'pos' and 'poolStatus' must be dictionaries.")
		if not isinstance(stableCoinPos, (int, float)):
			raise ValueError("Invalid input: 'stableCoinPos' must be a number.")

		# Ensure required keys exist in 'pos'
		required_keys = ["id", "liquidity", "tickLower", "tickUpper"]
		for key in required_keys:
			if key not in pos:
				raise KeyError(f"Missing key in 'pos': {key}")

		if not isinstance(pos["tickLower"], dict) or "id" not in pos["tickLower"]:
			raise KeyError("Invalid 'tickLower' format in 'pos'.")
		if not isinstance(pos["tickUpper"], dict) or "id" not in pos["tickUpper"]:
			raise KeyError("Invalid 'tickUpper' format in 'pos'.")

		# Extract NFT number
		nftNumber = pos["id"]
		
		'''
		# Get USD value of the position
		try:
			valueUSD, feesUSD = getCurrentPosUSDValue(nftNumber)
			valueUSD = round(valueUSD, 2)
		except Exception as e:
			print(f"Error fetching USD value for NFT {nftNumber}: {e}")
			valueUSD = 0  # Default to 0 if the function fails
		'''
		# Determine if the position is active
		active = int(pos['liquidity']) > 0
		#valueUSD = valueUSD if active else 0
		
		# Extract tick IDs
		try:
			tick_lower = int(pos["tickLower"]["id"].split("#")[1])
			tick_upper = int(pos["tickUpper"]["id"].split("#")[1])
		except (IndexError, ValueError) as e:
			raise ValueError(f"Error parsing tick IDs: {e}")

		if active:
			coinRatio=getCoinRatio(poolStatus['current_tick'], tick_lower, tick_upper)
			try:
				insertLpPosValuation.insertWithNftId('Ethereum', nftNumber)
			except Exception as e:
				print(f"Error inserting LP position valuation for NFT {nftNumber}: {e}")
		else:
			#         | 51.48 : 48.52 
			coinRatio="00:00"
		
		# Get USD value of the position
		try:
			valueUSD, feesUSD = getCurrentPosUSDValue(nftNumber)
			valueUSD = round(valueUSD, 2)
		except Exception as e:
			print(f"Error fetching USD value for NFT {nftNumber}: {e}")
			valueUSD = 0  # Default to 0 if the function fails		
			feesUSD = 0
		
		valueUSD = valueUSD if active else 0
		
		'''
		# Extract tick IDs
		try:
			tick_lower = int(pos["tickLower"]["id"].split("#")[1])
			tick_upper = int(pos["tickUpper"]["id"].split("#")[1])
		except (IndexError, ValueError) as e:
			raise ValueError(f"Error parsing tick IDs: {e}")
		'''
		
		# Get price from tick values
		try:
			watchCoinPriceLow = getPriceFromTick(tick_lower, poolStatus)
			watchCoinPriceHigh = getPriceFromTick(tick_upper, poolStatus)
		except Exception as e:
			raise RuntimeError(f"Error fetching prices from ticks: {e}")

		# Compute derived values
		watchCoinPriceCenter = watchCoinPriceLow + (watchCoinPriceHigh - watchCoinPriceLow) / 2
		spread = watchCoinPriceHigh - watchCoinPriceLow

		# Handle stableCoinPos inversion
		if stableCoinPos == 0:
			if watchCoinPriceLow == 0 or watchCoinPriceHigh == 0:
				raise ZeroDivisionError("Cannot invert price: watchCoinPriceLow or watchCoinPriceHigh is zero.")
			watchCoinPriceLow = 1 / watchCoinPriceLow
			watchCoinPriceHigh = 1 / watchCoinPriceHigh

		roundInt=4 if watchCoinPriceLow<100 else 2
		return {
			"nftNumber": nftNumber,
			"active": active,
			"watchCoinPriceLow": round(watchCoinPriceLow, roundInt),
			"watchCoinPriceHigh": round(watchCoinPriceHigh, roundInt),
			"watchCoinPriceCenter": round(watchCoinPriceCenter, roundInt),
			"spread": round(spread, roundInt),
			"valueUSD": valueUSD,
			"coinRatio": coinRatio,
			"feesUSD": feesUSD
		}

	except Exception as e:
		print(f"Error in translatePosition: {e}")
		return None  # Return None to indicate failure




def generatePoolName(poolAddress):
	#print("generating pool name")
	symbols=getPoolSymbols.get_pool_data(poolAddress)
	t0Symbol=symbols['token0']['symbol']	#get pool t0 symbol
	t1Symbol=symbols['token1']['symbol']	#get pool t1 symbol
	name=f"{t0Symbol} / {t1Symbol}"
	return name



def getFixedPositions(pool_id, OWNER_ADDRESS):
	lp_pool = getLpPool(pool_id)
	if not lp_pool:
		print("Invalid pool ID.")
		return
	pool_address = lp_pool["poolAddress"]
	stable_coin_pos = lp_pool["stableCoinPosition"]
	#check 'block compare'
	print()
	difference, infura_block, sg_block=getBlockCompare.compare_blocks()
	print()
	# Fetch pool status and positions
	pool_status = getPoolData.get_uniswap_v3_pool_data(pool_address, stable_coin_pos)
	positions = getMainNetPositions.query_subgraph(pool_address, OWNER_ADDRESS)
	fixed_positions = [translatePosition(pos, pool_status, stable_coin_pos) for pos in positions["data"]["positions"]]
	return fixed_positions  

def reorder_positions(fixed_positions):
	#return sorted(fixed_positions, key=lambda x: (x["active"], x["watchCoinPriceCenter"], x["spread"]))
	return sorted(fixed_positions, key=lambda x: (x["active"], x["watchCoinPriceLow"], x["spread"]))



def analyze_active_positions(fixedPositions):
	total_weighted_center = 0
	total_weighted_ratio_low = 0
	total_weighted_ratio_high = 0
	total_value = 0
	

	for pos in fixedPositions:
		if pos.get("active"):
			value = pos.get("valueUSD", 0)
			total_value += value
			total_weighted_center += pos["watchCoinPriceCenter"] * float(value)
			try:
				low_str, high_str = pos["coinRatio"].split(":")
				low_str="00" if int(low_str)<0 else low_str
				low_str="100" if int(low_str)>100 else low_str
				high_str="00" if int(high_str)<0 else high_str
				high_str="100" if int(high_str)>100 else high_str
				total_weighted_ratio_low += int(low_str) * float(value)
				total_weighted_ratio_high += int(high_str) * float(value)
			except ValueError:
				print(f"Invalid coinRatio format in position {pos['nftNumber']}: {pos['coinRatio']}")
				continue

	if total_value == 0:
		return {
			"average_center_point": None,
			"average_ratio": None,
			"total_liquidity": 0.00
		}

	avg_center = total_weighted_center / float(total_value)
	avg_ratio_low = total_weighted_ratio_low / float(total_value)
	avg_ratio_high = total_weighted_ratio_high / float(total_value)
	avg_ratio = f"{round(avg_ratio_low)}:{round(avg_ratio_high)}"

	return {
		"average_center_point": round(avg_center, 2),
		"average_ratio": avg_ratio,
		"total_liquidity": round(float(total_value),2)
	}

				

def waitForSubGraph():
	# Initial block check
	difference, infura_block, sg_block = getBlockCompare.compare_blocks()
	print("Initial check: difference, infura_block, sg_block:", difference, infura_block, sg_block)

	first_infura_block = infura_block

	# Loop until Subgraph catches up
	max_attempts = 20        # optional safety limit
	attempt = 0
	
	time.sleep(3)

	while True:
		attempt += 1
		# Check stop conditions
		if difference == 0 or sg_block >= first_infura_block:
			print(f"Subgraph synced at attempt {attempt}")
			break

		# Optional: prevent infinite loop
		if attempt >= max_attempts:
			print("Max attempts reached, exiting loop")
			break

		# Wait a short interval before retrying
		time.sleep(6)

		# Fetch latest block numbers again
		difference, infura_block, sg_block = getBlockCompare.compare_blocks()
		print(f"Attempt {attempt}: difference={difference}, infura_block={infura_block}, sg_block={sg_block}")


def main(OWNER, poolSelect):	#, displayType):	
	#close_db()	
	'''
	#check 'block compare'
	print()
	difference, infura_block, sg_block=getBlockCompare.compare_blocks()
	print("difference, infura_block, sg_block: ", difference, infura_block, sg_block)
	
	time.sleep(3)
	'''
	waitForSubGraph()
	
	init_db()

	result_data = {
		"wallet": OWNER,
		"lpPool": None,
		"poolStatus": None,
		"gasRange": None,
		"gasBaseWei": None,
		"gasBaseGwei": None,
		"positions": [],
		"rawPositions": [],
		"activePositions": 0,
		"watchCoinPrice": None,
		"ethBalance": None,
		"ethValueUSD": None,
		"token0Balance": None,
		"token0BalanceUSD": None,
		"token1Balance": None,
		"token1BalanceUSD": None,
		"totalBalanceUSD": None,
		"positionAverages": {},
		"errors": []
	}
	
	activePositions = 0
	lpPool = getLpPool(poolSelect)
	result_data["lpPool"] = lpPool
	
	poolAddress = lpPool["poolAddress"]
	stableCoinPosition = lpPool["stableCoinPosition"]
	fixedPositions = []

	try:
		poolStatus = getPoolData.get_uniswap_v3_pool_data(poolAddress, stableCoinPosition)
		result_data["poolStatus"] = poolStatus
		currWatchCoinPrice = poolStatus['pricePerWatchCoin']
		result_data["watchCoinPrice"] = currWatchCoinPrice
		
		gasRange = getMainNetGas.getGasRange()
		result_data["gasRange"] = gasRange
		
		result_data["todaysGasStats"] = get24HourGasPrices()
		
		gasBaseWei, gasBaseGwei = getGasBase.getGasBase()
		result_data["gasBaseWei"] = gasBaseWei
		result_data["gasBaseGwei"] = gasBaseGwei
		
		# Possibly return this separately if needed
		# displayGasEstimatesUSD(gasRange, currWatchCoinPrice)
		
		positions = getMainNetPositions.query_subgraph(poolAddress, OWNER)
		result_data["rawPositions"]=positions
		for pos in positions:
			fixedPos = translatePosition(pos, poolStatus, stableCoinPosition)
			fixedPositions.append(fixedPos)
			if fixedPos["active"]:
				activePositions += 1

	except Exception as e:
		result_data["errors"].append(str(e))
		result_data["errors"].append(f"Error Check positions: {positions if 'positions' in locals() else 'N/A'}")
		result_data["errors"].append(f"Error Check pos: {pos if 'pos' in locals() else 'N/A'}")

	fixedPositions = reorder_positions(fixedPositions)
	result_data["positions"] = fixedPositions
	result_data["activePositions"] = activePositions

	ethBalance = getMainNetErcPrice.getEthBalance(OWNER)
	ETHprice = getMainNetErcPrice.get_token_price("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
	ethValUSD = round(ethBalance * ETHprice, 2)
	
	result_data["ethBalance"] = round(ethBalance, 3)
	result_data["ethValueUSD"] = ethValUSD

	t0Balance = getErc20Balance.get_erc20_balance(lpPool["token0Address"], OWNER)
	t1Balance = getErc20Balance.get_erc20_balance(lpPool["token1Address"], OWNER)

	if stableCoinPosition == 0:
		balanceUSD = t0Balance + currWatchCoinPrice * t1Balance
		result_data["token0Balance"] = t0Balance
		result_data["token0BalanceUSD"] = round(t0Balance, 2)
		result_data["token1Balance"] = t1Balance
		result_data["token1BalanceUSD"] = round(t1Balance * currWatchCoinPrice, 2)
	else:
		balanceUSD = t1Balance + currWatchCoinPrice * t0Balance
		result_data["token0Balance"] = t0Balance
		result_data["token0BalanceUSD"] = round(t0Balance * currWatchCoinPrice, 2)
		result_data["token1Balance"] = t1Balance
		result_data["token1BalanceUSD"] = round(t1Balance, 2)

	result_data["totalBalanceUSD"] = round(balanceUSD, 2)

	posAverages = analyze_active_positions(fixedPositions)
	result_data["positionAverages"] = {
		"averageCenterPoint": posAverages['average_center_point'],
		"averageRatio": posAverages['average_ratio'],
		"totalLiquidityUSD": posAverages['total_liquidity']
	}

	return result_data


if __name__ == "__main__":

	init_db()
	OWNER = "0x7BF2bd6B212Ad91A5B4686fC1e504CC708461C0e"	#LP Pool account on Python (aka: PyTradeBot)


	walletSelection = int(sys.argv[1])
	#print("Wallet select: ", walletSelection)

	additional_params = sys.argv[2:] if len(sys.argv) > 2 else []

	if walletSelection==1: 
		OWNER = "0x7BF2bd6B212Ad91A5B4686fC1e504CC708461C0e"
		#print("'1C0e Selected")
	elif walletSelection==2: 
		OWNER = "0xec92fdC275B81165317a58Ad50D5D134828c2f67"
		#print("'2f67 Selected")
	else:
		#print("Selectio NOT identified. Using '1C0e")
		OWNER = "0x7BF2bd6B212Ad91A5B4686fC1e504CC708461C0e"
	#print()



	#display pools avail'
	#print("Pools:")
	lpPoolList=getPolyLpPoolList()
	for pool in lpPoolList:
		poolName=generatePoolName(pool['poolAddress'])
		#print(pool['id'], ": ", poolName, "feeTier: ", pool['feeTier'])
		
	#print()

	poolSelect=int(additional_params[0])	#int(sys.argv[2])

	close_db()

	result_data=main(OWNER, poolSelect)

	#print(json.dumps(jsonResult['lpPool'], indent=2))	#<- this works !!!!!!!!!!!!!!
	#print(json.dumps(jsonResult['positions'], indent=2))	#<- this does NOT work !!!!!!!!!!!!!!
	jsonResult = convert_decimals(result_data)  # <- important!

	#print(json.dumps(jsonResult['positions'], indent=2))  # now this will work
	print(json.dumps(jsonResult, indent=2))


	
	
