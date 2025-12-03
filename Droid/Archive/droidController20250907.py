import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from dotenv import load_dotenv
import time
import pymysql
import time
import math
import json
import droidOperator
from typing import List
from utils import getMainNetPositions
from utils import getFixedPositions
from utils import getMainNetPriceFromPool
from utils import v3AddLiquidity
from utils import v3Mint
from utils import lpPositionLiquidate
from utils import newNftInserts
from utils import insertPositionBot
from utils import getMainNetGas
from utils import drawLadderGraphic
from utils import getErc20Balance
from utils import getRemoveLiquidities
from utils import getAddLiquidities
from utils import updateFeesCollected
from utils import updateHedgeValuations
from utils import updateLpTxsGas
from utils import fordefiErc20Tx
#from utils.build_mint_params import buildMintParams

from utils.dbFetch import (
	get_active_droids,
	getDroid,
	getPoolId,
	getLpPosId,
	getBotId,
	getPoolAddress,
	getLpPoolRecord,
	getLpPositionRecord,
	get_position_bots_for_droid,
	getDuplicateBots,
	getNftNumber,
	getUnusedBotId,
	getEvmAddress
)

from utils.fordefiUtils import fordefiGetApi

import logging
#from logging.handlers import RotatingFileHandler

# Set up a logger for session updates
session_logger = logging.getLogger("session_logger")
logging.basicConfig(filename='session_updates.log', encoding='utf-8', level=logging.INFO, force=True)
#session_logger.setLevel(logging.INFO)
#logging.basicConfig(filename='session_updates.log', encoding='utf-8', level=logging.INFO)
session_logger.info('Start Up')
'''
handler = RotatingFileHandler(
	"session_updates.log",  # File path
	maxBytes=5 * 1024 * 1024,  # 5 MB per file
	backupCount=3  # Keep 3 old files, delete older ones
)
handler.setLevel(logging.INFO)  # ✅ CRITICAL
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)

if not session_logger.hasHandlers():
	session_logger.addHandler(handler)
'''

#OWNER = "0x3651a474027496aA25F8106eF3A8D6f1486A88A6"	#TODO change to get/set from DB with ini' routines
def setOwner(accountId, cursor):
	global OWNER
	owner=getEvmAddress(accountId, cursor)
	OWNER = owner['address']	#"0x3651a474027496aA25F8106eF3A8D6f1486A88A6"

CHAIN = "ethereum_mainnet"	#TODO change to get/set from DB with ini' routines

# ---------- CONFIG ---------- #
DB_CONFIG = {
	'host': 'localhost',
	'user': 'username',
	'password': 'password',
	'database': 'helix',
	'cursorclass': pymysql.cursors.DictCursor
}

# ---------- LADDER CASE TYPES ---------- #
LADDER_CASES = {
	"ORIGINAL": "original",
	"EXT_UP": "extended_up",
	"EXT_DOWN": "extended_down",
	"REBAL_UP": "rebalance_up",
	"REBAL_DOWN": "rebalance_down"
}

previous_values = {}

DROID_SESSION={}



def upsert_droid_status(droid, nftArray, nftsLiquUSD, lpPosArray, botArray, ratioArray, cursor, connection):
	"""
	Inserts or updates the DroidsStatus table with current data.
	If a record with the given droidId exists, it will be updated.
	Otherwise, a new record will be inserted.
	"""
	
	droidId=droid['id']
	# Convert Python lists to JSON strings
	nftArray_json = json.dumps(nftArray)
	nftsLiquUSD_json = json.dumps(nftsLiquUSD)
	lpPosArray_json = json.dumps(lpPosArray)
	botArray_json = json.dumps(botArray)
	ratioArray_json = json.dumps(ratioArray)

	# First, check if a record already exists for this droidId
	cursor.execute("SELECT id FROM DroidsStatus WHERE droidId = %s", (droidId,))
	existing = cursor.fetchone()
	ladderArray = get_ladder_structure(droid, cursor)
	ladderArray_json=json.dumps(ladderArray)
	#print(droidId, ladderArray)
	#print()
	
	if existing:
		# UPDATE existing record
		sql = """
		UPDATE DroidsStatus
		SET timeStamp = CURRENT_TIMESTAMP,
			nftArray = %s,
			nftsLiquUSD = %s,
			lpPosArray = %s,
			botArray = %s,
			ratioArray = %s,
			ladderArray = %s
		WHERE droidId = %s
		"""
		cursor.execute(sql, (nftArray_json, nftsLiquUSD_json, lpPosArray_json, botArray_json, ratioArray_json, ladderArray_json, droidId))
	else:
		# INSERT new record
		sql = """
		INSERT INTO DroidsStatus (droidId, nftArray, nftsLiquUSD, lpPosArray, botArray, ratioArray, ladderArray)
		VALUES (%s, %s, %s, %s, %s, %s, %s)
		"""
		cursor.execute(sql, (droidId, nftArray_json, nftsLiquUSD_json, lpPosArray_json, botArray_json, ratioArray_json, ladderArray_json))

	connection.commit()



def updateLpTxs(droid_id):
	POOL=LpPositionsStat['lpPool']['poolAddress']	#"0x4e68ccd3e89f51c3074ca5072bbac773960dfa36"
	#WALLET = "0xec92fdc275b81165317a58ad50d5d134828c2f67"
	print("\n--- Starting Lp Txs sync cycle ---")
	try:
		getAddLiquidities.run(POOL, OWNER, droid_id)
		getRemoveLiquidities.run(POOL, OWNER, droid_id)
		updateFeesCollected.update_fees()
		updateLpTxsGas.main()

	except Exception as e:
		print(f"Error during sync cycle: {e}")


def check_breakers(droid, session) -> str | None:
	"""
	Checks breaker conditions to prevent blockchain actions.

	Returns:
	- Name of the tripped breaker (str), or
	- None if all breakers pass
	"""

	# ---------- Hardcoded Breaker Values (for now) ---------- #
	GAS_BUDGET_LIMIT = droid['gasBudgetLimit']	#0.024 # max amount of eth avail to spend on droid
	MAX_PRICE = droid['maxPrice']	#2900    # Max price (USD) of watch token allowed
	MIN_PRICE = droid['minPrice']	#2400    # Min price (USD) of watch token allowed

	# ---------- Fetch Live Values (from globals or helpers) ---------- #
	#current_gas_price_gwei = get_current_gas_price()         # e.g., in GWEI
	#gas_cost_eth = estimate_tx_cost_eth(current_gas_price_gwei)  # Convert GWEI to ETH (stub function)

	current_eth_balance=float(getErc20Balance.getEthBalance(OWNER))
	eth_spent=session['startingEthGasAmount']-current_eth_balance
	watch_price = float(LpPoolStat['token0']['tokenDayData'][0]['priceUSD'])
	
	print("eth_spent (on gas fees): ", eth_spent)
	print()

	# ---------- Breaker Checks ---------- #
	if eth_spent > GAS_BUDGET_LIMIT:
		return "gas_budget_breaker"

	elif watch_price > MAX_PRICE:
		return "max_price_breaker"

	elif watch_price < MIN_PRICE:
		return "min_price_breaker"
	
	elif droid['active']==0:
		return "deactive_breaker"

	# ---------- All breakers passed ---------- #
	return None



'''
EXAMPLE/REFERENCE:
LpPositionsStat['positions']=
[{'nftNumber': '961909', 'active': False, 'watchCoinPriceLow': 1477.4, 'watchCoinPriceHigh': 1486.29, 'watchCoinPriceCenter': 1481.84, 'spread': 8.89, 'valueUSD': 0, 'coinRatio': '00:00', 'feesUSD': Decimal('0E-16')}, {'nftNumber': '963526', 'active': False, 'watchCoinPriceLow': 1486.29, 'watchCoinPriceHigh': 1495.23, 'watchCoinPriceCenter': 1490.76, 'spread': 8.94, 'valueUSD': 0, 'coinRatio': '00:00', 'feesUSD': Decimal('0E-16')}, {'....................

LpPositionsStat:  {'wallet': '0x7BF2bd6B212Ad91A5B4686fC1e504CC708461C0e', 'lpPool': {'id': 2, 'blockChain': 'Ethereum', 'poolAddress': '0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36', 'token0Address': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2', 'token1Address': '0xdac17f958d2ee523a2206206994597c13d831ec7', 'feeTier': 3000, 'stableCoinPosition': 1}, 'poolStatus': {'pool_address': '0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36', 'token0': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'token1': '0xdAC17F958D2ee523a2206206994597C13D831ec7', 'fee_percent': 0.3, 'liquidity': 6544789216043777125, 'tick_spacing': 60, 'sqrt_price_x96': 3972444541520663254859673, 'current_tick': -198025, 'price_token0_in_token1': 2513.9493193964004, 'pricePerWatchCoin': 2513.9493193964004, 'token0_decimals': 18, 'token1_decimals': 6}, 'gasRange': [22519257, 1.41, 1.4, 1.4, 1.39, 1.38], 'gasBaseWei': 1311565280, 'gasBaseGwei': Decimal('1.31156528'), 'positions': [.................



'''

def setPositions(poolId, OWNER, max_retries=3, retry_delay=5):
	global LpPositionsStat

	retry_count = 0
	while retry_count < max_retries:
		try:
			LpPositionsStat = getFixedPositions.main(OWNER, poolId)

			# If result is valid (non-empty dict)
			if isinstance(LpPositionsStat, dict) and LpPositionsStat:
				print("✅ LpPositionsStat successfully updated.")
				return
			else:
				print("⚠️ Warning: getFixedPositions.main returned empty or invalid data.")

		except Exception as e:
			print(f"❌ Error in getFixedPositions.main: {e}")

		# Wait before retrying
		retry_count += 1
		if retry_count < max_retries:
			print(f"⏳ Retrying in {retry_delay} seconds... (Attempt {retry_count + 1}/{max_retries})")
			time.sleep(retry_delay)

	# If we exit the loop, it failed all retries
	print("❗ Failed to update LpPositionsStat after multiple attempts.")
	LpPositionsStat = {}


# Store EMA state per pool
ema_state = {}

def setPoolStat(poolAddress, N):
    global LpPoolStat

    #N = 10
    alpha = 2 / (N + 1) 
    
    try:
        # Get new pool data
        sgStat = getMainNetPositions.query_pool_status(poolAddress)
    except Exception as e:
        print(f"Failed to UPDATE POSITIONS price: {e}")
        return   

    # Extract price (we'll use token1Price, in USD per token0)
    try:
        price = float(sgStat['data']['pools'][0]['token1Price'])
    except Exception as e:
        print(f"Failed to extract price: {e}")
        return

    # Use current timestamp
    now = time.time()

    # Get previous EMA and time, if exists
    prev = ema_state.get(poolAddress)
    if prev:
        prev_ema, prev_time = prev['ema'], prev['timestamp']
        delta_t = now - prev_time if now > prev_time else 6  # fallback Δt

        # Calculate new EMA and derivative
        ema = price * alpha + prev_ema * (1 - alpha)
        derivative = (ema - prev_ema) / delta_t
    else:
        ema = price
        derivative = 0.0
        delta_t = 0

    # Save updated state
    ema_state[poolAddress] = {
        'ema': ema,
        'derivative': derivative,
        'timestamp': now
    }

    
    _sgStat=sgStat['data']['pools'][0]
    # Merge into sgStat for global use
    _sgStat['ema'] = ema
    _sgStat['ema_derivative'] = derivative
    _sgStat['ema_last_updated'] = now
    _sgStat['derivativeHigh'] = .05	#
    _sgStat['derivativeLow'] = -.05

    LpPoolStat = _sgStat
	
def detect_order(arr):
	if all(earlier < later for earlier, later in zip(arr, arr[1:])):
		return "asc"
	elif all(earlier > later for earlier, later in zip(arr, arr[1:])):
		return "desc"
	else:
		return "na"


def check_duplicate_lp_positions(droid_id, cursor):
	"""
	Returns a list of dicts containing duplicate lpPositionId entries for a given droid_id.
	Each dict includes: lpPositionId and count (number of occurrences).
	"""

	query = """
		SELECT 
			lpPositionId, COUNT(*) AS count
		FROM PositionBots
		WHERE droidId = %s AND lpPositionId IS NOT NULL
		GROUP BY lpPositionId
		HAVING count > 1;
	"""

	cursor.execute(query, (droid_id,))
	duplicates = cursor.fetchall()

	if not duplicates:
		print(f"✅ No duplicate lpPositionId values found for droidId {droid_id}.")
	else:
		print(f"⚠️  Duplicate lpPositionId values found for droidId {droid_id}:")
		for row in duplicates:
			print(f"  lpPositionId: {row['lpPositionId']} | Count: {row['count']}")

	return duplicates  # list of {'lpPositionId': <int>, 'count': <int>}


def prune_duplicates(droid, cursor, connection):
	"""
	If duplicates are found for the given droid, deactivate the droid.
	"""
	print("🔍 Pruning duplicates...\n")
	duplicates = check_duplicate_lp_positions(droid['id'], cursor)

	if duplicates:
		# Deactivate the droid
		print("⚠️  Duplicates found — fixing duplicates!")
		try:
			#cursor.execute("UPDATE Droids SET active = 0 WHERE id = %s", (droid['id'],))
			#connection.commit()
			print("✅ Droid deactivated.")
			for dup in duplicates:
				botDups=getDuplicateBots(dup['lpPositionId'], droid['id'], cursor)
				print(f"Bot Duplicates {botDups}")
				print()
				if len(botDups)==2:
					if(botDups[0]['id']==droid['centerPosBotId']): 
						print("set botDups[1] droidId value to 0")
						cursor.execute("UPDATE PositionBots SET droidId = 0 WHERE id = %s", (botDups[1]['id'],))
						connection.commit()						
					if(botDups[1]['id']==droid['centerPosBotId']): #print("set botDups[0] droidId value to 0")
						cursor.execute("UPDATE PositionBots SET droidId = 0 WHERE id = %s", (botDups[0]['id'],))
						connection.commit()								
			
		except Exception as e:
			print("❌ Error fixing duplicates:", e)
	else:
		print("✅ No action needed. Droid is clean.")

def addPositionToDB(nftNumber, nftArray, nftsLiquUSD, cursor, botArray, connection, droid):
	print(f"Attempting: Add position {nftNumber} to DB!!")
	positionAdded = 0

	# Check for an existing unfunded NFT
	unFundedNftIndex = -1
	for n, nftUSD in enumerate(nftsLiquUSD):
		if nftUSD == 0:
			unFundedNftIndex = n
			break

	if unFundedNftIndex != -1:
		unFundedBotId = botArray[unFundedNftIndex]
		print(f"Assigning {nftNumber} lpPosId to botId {unFundedBotId}!")

		lpPosRecord = getLpPositionRecord(nftNumber, cursor)
		if (lpPosRecord==None):
			newNftInserts.insertMainNetNftAsset(nftNumber, LpPositionsStat['lpPool']['id'])	#add LP record
			lpPosRecord = getLpPositionRecord(nftNumber, cursor)
		
		#query = "UPDATE PositionBots SET lpPositionId=%s WHERE id=%s"
		query = f"UPDATE PositionBots SET lpPositionId={lpPosRecord['id']} WHERE id={unFundedBotId}"
		print("!!! TEST THIS query!!!!")
		print("query: ", query)
		print()
		
		try:
			cursor.execute(query)	#, (lpPosRecord['id'], unFundedBotId))
			connection.commit()
			positionAdded = lpPosRecord['id']
		except Exception as e:
			print("❌ Error executing query:", e)
		
	else:
		print("All DB LpPositions are funded!")
		print(f"Liquidating NFT: {nftNumber}....")
		print()
		
		max_gas_calc=getMaxGasGwei(droid['fundingUSD'])
		print("max_gas_calc: ", max_gas_calc)
		print()
		gasCheck=getGasCheck(max_gas_calc)	#True/False return. 
		if (gasCheck):
			receipt=lpPositionLiquidate.remLiquAndCollFordefi(nftNumber, CHAIN)
			if(receipt=="fail"):
				print("error liquidating position!")
				print()
		else:
			print("'gas check': error liquidating position!")
			print()
	return positionAdded


def alignDBwithBC(nftArray, nftsLiquUSD, cursor, botArray, connection, droid):
	print("Checking for DB ↔ Blockchain position alignment!")
	for pos in LpPositionsStat['positions']:
		if pos['active']:
			nftFound = int(pos['nftNumber']) in nftArray
			if not nftFound:
				print(f"🔍 Active NFT {pos['nftNumber']} not in nftArray or synced with DB. Adding it...")
				addedPosition = addPositionToDB(pos['nftNumber'], nftArray, nftsLiquUSD, cursor, botArray, connection, droid)
				return addedPosition  # or continue if processing all

	print(" ✅ Alignment=OK!")
	print()
	return 0

	
def prepare_droid_arrays(droid, cursor, connection):
	print("Calling prepare_droid_arrays function.")
	nftArray, nftsLiquUSD = getNftArray(droid, cursor)
	print("nftArray: ", nftArray)
	print("nftsLiquUSD: ", nftsLiquUSD)
	print()

	lpPosArray = [getLpPositionRecord(nft, cursor)['id'] for nft in nftArray]
	print("lpPosArray: ", lpPosArray)
	
	ratioArray=[]
	for nft in nftArray:
		ratio=getRatio(nft)
		#print("ratio: ", ratio)
		ratioArray.append(ratio)
	print("ratioArray: ", ratioArray)
	botArray = [getBotId(droid['id'], posId, cursor) for posId in lpPosArray]
	print("botArray: ", botArray)
	print()
	
	prune_duplicates(droid, cursor, connection)
	
	
	upsert_droid_status(droid, nftArray, nftsLiquUSD, lpPosArray, botArray, ratioArray, cursor, connection)

	return nftArray, nftsLiquUSD, lpPosArray, botArray, ratioArray


def evaluate_droid_state(droid, nftArray, nftsLiquUSD, lpPosArray, botArray, cursor, connection):
	if len(nftsLiquUSD) > 1:
		nftsLiquOrderUSD = detect_order(nftsLiquUSD)
	else:
		nftsLiquOrderUSD = "na"

	nftsLiquTotalUSD = sum(nftsLiquUSD)
	triggerStat = None

	#remove all bots > center that have zero liquidity
	n=-1
	for liquUSD in nftsLiquUSD:
		n=n+1
		print("liquUSD: ", liquUSD)
		if(liquUSD==0.0 and n>0): 
			print(f"Removing bot '{botArray[n]}' from droid!")
			print()
			sql = f"UPDATE PositionBots SET droidId=0 WHERE id = {botArray[n]}"
			cursor.execute(sql)
			connection.commit()
	
	if nftsLiquOrderUSD == "asc":
		# Reverse ordering — promote highest liquidity NFT to center
		maxUsdIndex = nftsLiquUSD.index(max(nftsLiquUSD))
		newCenterBotId = botArray[maxUsdIndex]
		print("Updating Droid with new centerPosBotId")
		sql = f"UPDATE Droids SET centerPosBotId={newCenterBotId} WHERE id = {droid['id']}"
		cursor.execute(sql)
		connection.commit()

	elif nftsLiquOrderUSD == "desc":
		if nftsLiquUSD[0] == 0:
			triggerStat = "fallingRebalanceTrigger"

					
	else:
		# Distribution is scrambled
		print("Droid in LiquUSD distribution 'dis-array'.")
		if nftsLiquTotalUSD == 0:
			print("Zero liquidity total — deregistering all except center.")
			for i, bot in enumerate(botArray):
				if i > 0:  # Leave center (index 0)
					sql = f"UPDATE PositionBots SET droidId=0 WHERE id = {bot}"
					cursor.execute(sql)
					connection.commit()
			triggerStat = "fallingRebalanceTrigger"

	if(nftsLiquTotalUSD>droid['fundingUSD']):
		diff=nftsLiquTotalUSD-droid['fundingUSD']
		print(f"Droid is OverFunded by ${diff}!")
		print()
		
	if(nftsLiquUSD[0]==0.0):
		triggerStat="iniCenterPos"
	
	return triggerStat

def iniDroid(droid, cursor, connection):
	print("Call droid initialization routines here!")
	print()
	if(droid['centerPosBotId']==0): 
		#assgin bot to center positon
		newBotId=getUnusedBotId(cursor)
		sql = f"UPDATE PositionBots SET droidId={droid['id']}, active=1 WHERE id = {newBotId}"
		cursor.execute(sql)
		connection.commit()
		sql=f"UPDATE Droids SET centerPosBotId={newBotId} WHERE id={droid['id']}";
		cursor.execute(sql)
		connection.commit()
		
		addedPosition=alignDBwithBC([0], [0], cursor, [newBotId], connection, droid)	#align the database positions found with blockchain function
		return "fallingRebalanceTrigger"
	print("updating Lp...Txs tables...")
	print()
	updateLpTxs(droid['id'])
	
	nftArray, nftsLiquUSD, lpPosArray, botArray, ratioArray = prepare_droid_arrays(droid, cursor, connection)
	
	addedPosition=alignDBwithBC(nftArray, nftsLiquUSD, cursor, botArray, connection, droid)	#align the database positions found with blockchain function
	if addedPosition!=0: return "fallingRebalanceTrigger"
	
	triggerStat = evaluate_droid_state(droid, nftArray, nftsLiquUSD, lpPosArray, botArray, cursor, connection)
	
	print("Updating Position data ....")
	print()
	setPositions(2, OWNER)
	return triggerStat

def getDroidSession(droidId, cursor, connection):
	print("getting droid session")
	print()
	session=DROID_SESSION.get(droidId)
	if (session == None):
		print("no session found. create new session.")
		print()
		startingEthGasAmount=getErc20Balance.getEthBalance(OWNER)
		DROID_SESSION[droidId]={ "status" : "not_ini", "startingEthGasAmount" : float(startingEthGasAmount)}
		sessionId=insert_droid_controller_session(droidId, cursor, connection)
		DROID_SESSION[droidId]['sessionId']=sessionId
		return DROID_SESSION[droidId]
	
	return session

def getReadyToPrune(droid):
	ready=True
	print("Checking to Prune.")
	#session:  {'status': 'ini_in_process', 'startingEthGasAmount': 0.4412716877645183, 'sessionId': 15, 'actionResult': '{"status": "failed", "step": "mint_build"}', 'prevActionTime': 1753192568, 'triggerStatReady': 'fallingRebalanceTrigger', 'loopCycleCount': 11, 'triggerStatSet': 'fallingRebalanceTrigger', 'breakerTrip': None}
	#if (DROID_SESSION[droidId]['actionResult'] contains "status": "failed" THEN ready=False
	droidId=droid['id']
	if ("failed" in DROID_SESSION[droidId]['actionResult']): ready=False
	return ready

def timeOutRoutines(timeOutSession, timeRemaining, droid, cursor, connection):
	print(f"  🏗️  calling time out routines for Time Out Session: {timeOutSession}!")
	nftArray, nftsLiquUSD, lpPosArray, botArray, ratioArray = prepare_droid_arrays(droid, cursor, connection)
	
	#TODO: use this addedPosition variable after "alignDBwithBC" function test
	#addedPosition=alignDBwithBC(nftArray, nftsLiquUSD, cursor, botArray, connection)	#align the database positions found with blockchain function
	
	#handler.flush()
	
	if(timeOutSession % 5 ==0): 
		droidOperator.updateDroidAum(droid['id'])
		time.sleep(5)
		updateHedgeValuations.insertHedgeValuation(droid['id'])
	if(timeOutSession % 2 == 0):
		readyToPrune=getReadyToPrune(droid)
		if (readyToPrune): 
			print("calling Prune droid!")
			print()
			pruneDroid(droid, cursor, connection)
		setPositions(droid['poolId'], OWNER)	#reSet LpPositionsStat
		
	return timeOutSession


def get_ladder_structure(droid, cursor):
	"""
	Given a droid record, build the ladder structure of positions
	relative to the center position, sorted by liquidity.
	"""
	if(droid['centerPosBotId']==0): return [0]
	
	# Step 1: Get tick size (e.g., number of positions / tick spacing)
	tick_size = droid.get("tickBuckets", 0)	#get_droid_size(droid)  # This should return an integer > 1

	# Step 2: Get all PositionBot records that belong to this droid
	position_bots = get_position_bots_for_droid(droid["id"], cursor)  # List of dicts

	def get_position_data(nftNumber):
		record = next((r for r in LpPositionsStat['positions'] if r['nftNumber'] == str(nftNumber)), None)
		if record:
			return record['watchCoinPriceCenter'], record['valueUSD']
		else:
			return None, None

	# Step 3: Get position data for each PositionBot using its lpPositionId
	positions = []
	for pb in position_bots:
		lp_position_id = pb["lpPositionId"]

		# Get nftNumber from DB
		cursor.execute("SELECT nftNumber FROM LpPositions WHERE id = %s", (lp_position_id,))
		result = cursor.fetchone()
		if not result:
			continue
		nft_number = result["nftNumber"]

		# Get price center and liquidity via your existing helper
		price_center, liquidity = get_position_data(nft_number)  # Already implemented
		positions.append({
			"nftNumber": nft_number,
			"price_center": price_center,
			"liquidity": liquidity,
			"bot_id": pb["id"]
		})

	# Step 4: Get the center position details
	center_pos_bot_id = droid["centerPosBotId"]
	cursor.execute("SELECT lpPositionId FROM PositionBots WHERE id = %s", (center_pos_bot_id,))
	result = cursor.fetchone()
	if not result:
		raise ValueError("Center Position Bot ID not found.")
	lp_position_id = result["lpPositionId"]
	cursor.execute("SELECT nftNumber FROM LpPositions WHERE id = %s", (lp_position_id,))
	result = cursor.fetchone()
	if not result:
		raise ValueError("LpPosition ID for center not found.")
	center_nft = result["nftNumber"]
	center_price, center_liquidity = get_position_data(center_nft)

	# Step 5: Build ladder structure array
	# Remove the center from the list if it's included
	positions = [p for p in positions if p["nftNumber"] != center_nft]

	#print("ladder positions: ", positions)
	#print()
	# Sort all by liquidity (highest first), include center explicitly at front
	sorted_positions = sorted(positions, key=lambda x: x["liquidity"], reverse=True)

	# Final ladder: center is always 0
	ladder = [0]  # Center position is reference

	centerTickLower, centerTickUpper = getTickRange(center_nft)
	for pos in sorted_positions:
		# Compare price center to center position
		#get_raw_position_data(pos['nftNumber'])
		xTickLower, xTickUpper=getTickRange(pos['nftNumber'])
		delta = pos["price_center"] - center_price

		# Decide tick index: assume 'tick spacing' or some form of offset-to-int mapping
		#relative_tick = get_relative_tick(delta, tick_size)  # Helper function to define
		offset_multiplier=droid.get("bucketOffset", 1)	
		tickSpacing=LpPositionsStat['poolStatus']['tick_spacing']
		if(xTickLower>centerTickLower):
			relative_tick= int((xTickLower-centerTickLower)/(offset_multiplier*tickSpacing))
		else:
			relative_tick= int((xTickUpper-centerTickUpper)/(offset_multiplier*tickSpacing))
		ladder.append(relative_tick)

	return ladder

def getNftArray(droid, cursor):
	"""
	Returns a list of NFT numbers associated with a Droid.
	- The first element is always the center NFT (via centerPosBotId).
	- The rest are sorted by liquidity USD descending.
	"""
	if(droid['centerPosBotId']==0): return [0], [0]
	
	center_pos_bot_id = droid["centerPosBotId"]
	droid_id = droid["id"]

	# Step 1: Get center lpPositionId and its NFT number
	cursor.execute("SELECT lpPositionId FROM PositionBots WHERE id = %s", (center_pos_bot_id,))
	center_result = cursor.fetchone()
	if not center_result:
		print("Center bot not found.")
		return []

	center_lp_position_id = center_result["lpPositionId"]

	cursor.execute("SELECT nftNumber FROM LpPositions WHERE id = %s", (center_lp_position_id,))
	center_nft_result = cursor.fetchone()
	if not center_nft_result:
		print("Center lpPositionId not found in LpPositions.")
		return []

	center_nft_number = center_nft_result["nftNumber"]

	# Step 2: Fetch all other positionBots (excluding the center)
	cursor.execute("""
		SELECT pb.id AS botId, lp.id AS lpPositionId, lp.nftNumber
		FROM PositionBots pb
		JOIN LpPositions lp ON pb.lpPositionId = lp.id
		WHERE pb.droidId = %s AND pb.id != %s
	""", (droid_id, center_pos_bot_id))
	all_results = cursor.fetchall()

	print("all_results: ", all_results)
	print()
	
	# Step 3: Gather (nftNumber, liquidityUSD) pairs
	liquidity_info = []
	for row in all_results:
		nft = row["nftNumber"]
		try:
			print("nft: ", nft)
			print()
			liquidity_usd = getNftLiquUSD(nft)
			print("liquidity_usd: ", liquidity_usd)
			print()
			liquidity_info.append((nft, float(liquidity_usd)))
		except Exception as e:
			print(f"Error fetching liquidity for NFT {nft}: {e}")

	# Step 4: Sort remaining by liquidity descending
	sorted_nfts = [nft for nft, _ in sorted(liquidity_info, key=lambda x: x[1], reverse=True)]
	sorted_liquUSD= [liquUSD for _, liquUSD in sorted(liquidity_info, key=lambda x: x[1], reverse=True)]
	
	# Step 5: Return full list with center first
	return [center_nft_number] + sorted_nfts, [float(getNftLiquUSD(center_nft_number))] + sorted_liquUSD


def getCenterTickLower(droid, cursor):
	nftNumber=getNftNumber(droid, cursor)
	lower, upper = getTickRange(nftNumber)
	return lower


def getTickRange(nftNumber):
	for pos in LpPositionsStat['rawPositions']:
		if(int(nftNumber)==int(pos["id"])):
			tick_lower = int(pos["tickLower"]["id"].split("#")[1])
			tick_upper = int(pos["tickUpper"]["id"].split("#")[1])	
			return tick_lower, tick_upper
	return None, None

def getRatio(nftNumber):
	for pos in LpPositionsStat['positions']:
		if(int(nftNumber)==int(pos["nftNumber"])):
			return pos['coinRatio']
			
	return "00:00"

def get_lp_range(nftNumber):
	record = next((r for r in LpPositionsStat['positions'] if r['nftNumber'] == str(nftNumber)), None)
	if record:
		return record['watchCoinPriceLow'], record['watchCoinPriceHigh']
	else:
		return None, None

# ---------- LOGIC FUNCTIONS ---------- #
def getTriggerStat(droid, cursor) -> str:
	droid_id = droid['id']
	center_pos_bot_id = droid["centerPosBotId"]
	
	
	#!!!!!!!!!!!!!!! start !!!!!!!!!!!!!
	# Step 1: Get lpPositionId from PositionBots
	cursor.execute("SELECT lpPositionId FROM PositionBots WHERE id = %s", (center_pos_bot_id,))
	result = cursor.fetchone()
	if not result:
		print("centerPosBotId not found in PositionBots")
		return None
	lp_position_id = result["lpPositionId"]

	# Step 2: Get nftNumber from LpPositions
	cursor.execute("SELECT nftNumber FROM LpPositions WHERE id = %s", (lp_position_id,))
	result = cursor.fetchone()
	if not result:
		print("lpPositionId not found in LpPositions")
		return None
	nft_number = result["nftNumber"]
	#!!!!!!!!!!!!!! end !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
	
	def get_lp_range(nftNumber):
		record = next((r for r in LpPositionsStat['positions'] if r['nftNumber'] == str(nftNumber)), None)
		if record:
			return record['watchCoinPriceLow'], record['watchCoinPriceHigh']
		else:
			return None, None
	
	# Step 3: Get range from blockchain
	low_usd, high_usd =get_lp_range(nft_number)
	if low_usd is None or high_usd is None:
		print(f"Invalid range returned for nft #{nft_number}")
		print("Re-Setting LpPositions")
		print()
		setPositions(droid['poolId'], OWNER)
		return None

	# Step 4: Calculate the 4 trigger USD values
	def calculate_trigger(trigger_ratio):
		return (high_usd - low_usd) * float(trigger_ratio) + low_usd

	if(droid['tickBuckets']%2==0):
		risingRebalTriggRatio=.75
	else:
		#not even
		risingRebalTriggRatio=.5-(droid['tickBuckets']-1)/(2*droid['tickBuckets'])+(droid['tickBuckets']-1)/droid['tickBuckets']
			
	fallingRebalTriggRatio=1-risingRebalTriggRatio
	print(f"Note calced' trigg' ratios: {fallingRebalTriggRatio} and {risingRebalTriggRatio}")
	triggers = {
		"fallingRebalanceTrigger": calculate_trigger(fallingRebalTriggRatio),
		"risingRebalanceTrigger": calculate_trigger(risingRebalTriggRatio),		
		"fallingSubsequentTrigger": 1,	#calculate_trigger(droid["fallingSubSequentTrigger"]),
		"risingSubsequentTrigger": 1	#calculate_trigger(droid["risingSubSequentTrigger"]),
	}

	# Step 5: Get current value
	trigger_type = droid["triggerType"].lower()
	if trigger_type == "price":
		stableCoinPos=LpPositionsStat['lpPool']['stableCoinPosition']
		if (stableCoinPos==1): 
			erc20Addr=LpPositionsStat['lpPool']['token0Address']
		else:
			erc20Addr=LpPositionsStat['lpPool']['token1Address']
		current_value1 = getMainNetPriceFromPool.get_token_price(erc20Addr)	#get_current_price()
		print("current_value1: ", current_value1)
		print()
		current_value = float(LpPoolStat['token0']['tokenDayData'][0]['priceUSD'])	#TODO: fix this to get price from pool
	elif trigger_type == "ema":
		current_value = LpPoolStat['ema']
	else:
		print(f"Unknown trigger type: {trigger_type}")
		return None

	# Step 6: Compare with previous value
	key = (droid_id, trigger_type)
	previous_value = previous_values.get(key)
	print("current_value: ", current_value)
	print("previous_value: ", previous_value)
	print()

	
	for name, trigger_usd in triggers.items():
		print(name, ": ", trigger_usd)
		if previous_value is not None:

			if "fallingRebalanceTrigger" in name and current_value < triggers['fallingRebalanceTrigger']:	#low_usd:
				previous_values[key] = current_value
				return name
			elif "risingRebalanceTrigger" in name and current_value > triggers['risingRebalanceTrigger']:	#high_usd:
				previous_values[key] = current_value
				return name			
			#if "falling" in name and previous_value > trigger_usd and current_value <= trigger_usd:
			#elif "falling" in name and previous_value > current_value:
			elif "fallingSubsequentTrigger" in name and LpPoolStat['ema_derivative'] < 0:
				previous_values[key] = current_value
				return name
			#elif "rising" in name and previous_value < trigger_usd and current_value >= trigger_usd:
			#elif "rising" in name and previous_value < current_value:
			elif "risingSubsequentTrigger" in name and LpPoolStat['ema_derivative'] > 0:
				previous_values[key] = current_value
				return name

		
	# Always update the cache
	previous_values[key] = current_value
	return None


def determine_ladder_case(ladder: List[int], ladderOffset: int) -> str:
	if all(x == 0 for x in ladder):
		return LADDER_CASES["ORIGINAL"]

	expected_up = [i * ladderOffset for i in range(len(ladder))]
	expected_down = [i * -ladderOffset for i in range(len(ladder))]

	if ladder == expected_up:
		return LADDER_CASES["EXT_UP"]
	elif ladder == expected_down:
		return LADDER_CASES["EXT_DOWN"]
	else:
		return "unknown"


#def determine_required_action(triggerStat: str, ladder_case: str) -> str:
def determine_required_action(triggerStat: str, ladder_case: str, droid, ladder_structure) -> str:
	 #determine_required_action(triggerStat, ladder_case, droid, ladder_structure)
	print(f"  Trigger type/stat: {triggerStat}")
	print(f"  ladder_case: {ladder_case}")
	print()
	'''
	"fallingSubsequentTrigger"
	"risingSubsequentTrigger"
	"fallingRebalanceTrigger"
	"risingRebalanceTrigger"
	'''
	if triggerStat == "risingSubsequentTrigger":
		return "ladder_UP"
			
	elif triggerStat == "fallingSubsequentTrigger":
		return  "ladder_DN"

	elif triggerStat == "risingRebalanceTrigger":
		return "re_balance_UP"

	elif triggerStat == "fallingRebalanceTrigger":
		return "re-balance_DN"

	return None

def getCurrTickBucket(currTick, tickSpacing):
	currTickBucketLow=currTick-(currTick % tickSpacing)
	return currTickBucketLow, currTickBucketLow + tickSpacing

#def checkForExistingPlo(ploEntrConds, positions):
def getExistingNft(newRangeLow, newRangeHigh):
	existingNft=0
	for pos in LpPositionsStat['rawPositions']:
		tick_lower = int(pos["tickLower"]["id"].split("#")[1])
		tick_upper = int(pos["tickUpper"]["id"].split("#")[1])
		if(tick_lower==newRangeLow and tick_upper==newRangeHigh):
			#MATCH FOUND
			existingNft=pos["id"]
			return existingNft
	
	return existingNft

def getNftLiquUSD(currentNft):
	liqu=0
	for pos in LpPositionsStat['positions']:
		if(int(pos['nftNumber'])==int(currentNft)):
			#MATCH FOUND
			liqu=pos['valueUSD']
			return liqu
	
	return liqu

def decay_curve(n, base=0.4):
	weights = [base ** i for i in range(n)]
	total = sum(weights)
	return [w / total for w in weights]

def gaussian_curve(n, sigma=1.5):
	center = 0
	weights = [math.exp(-0.5 * ((i - center) / sigma) ** 2) for i in range(n)]
	total = sum(weights)
	return [w / total for w in weights]

def linear_ramp(n):
	weights = list(range(n, 0, -1))
	total = sum(weights)
	return [w / total for w in weights]

def getLadderIndexFunding(curveType, fundingUSD, maxBots, index):
	indexFundingUSD=0
	#!!!! ADD LOGIC HERE !!!!!!!
	#curveType: {decay, gaussian, linear}
	if curveType=="decay":
		w=decay_curve(maxBots)
	elif curveType=="gaussian":
		w=gaussian_curve(maxBots)
	elif curveType=="linear":
		w=linear_ramp(maxBots)
	
	print("w: ", w)
	print()
	print("index: ", index)
	print()
	
	indexFundingUSD=w[index]*fundingUSD
	return indexFundingUSD

def getCenterNftFunding(curveType, fundingUSD, maxBots):
	centerFundingUSD=0
	#!!!! ADD LOGIC HERE !!!!!!!
	#curveType: {decay, gaussian, linear}
	if curveType=="decay":
		w=decay_curve(maxBots)
	elif curveType=="gaussian":
		w=gaussian_curve(maxBots)
	elif curveType=="linear":
		w=linear_ramp(maxBots)
	
	print("w: ", w)
	print()
	centerFundingUSD=w[0]*fundingUSD
	return centerFundingUSD


def swapRoutine(amountNeeded, tokenNeeded, droid, cursor):
	print("Call Swap Routine HERE!")
	print()

	hedgeEvmAddress = getEvmAddress(droid['hedgeAccount'], cursor)
	hedgeVaultId = fordefiGetApi.getVaultId(hedgeEvmAddress['address'])
	droidVaultId = fordefiGetApi.getVaultId(OWNER)  # guessing

	T1perT0 = float(LpPoolStat['token0Price'])
	T0perT1 = float(LpPoolStat['token1Price'])
	token0Dec = int(LpPoolStat['token0']['decimals'])
	token1Dec = int(LpPoolStat['token1']['decimals'])

	if tokenNeeded == "token0":
		tokenNeededAddr = LpPositionsStat['poolStatus']['token0']
		tokenRepayAddr = LpPositionsStat['poolStatus']['token1']

		# normalize to decimals
		amountToken0 = amountNeeded / (10 ** token0Dec)
		repayToken1 = amountToken0 * T0perT1
		weiToRepay = int(repayToken1 * (10 ** token1Dec))

	else:  # token1 needed
		tokenNeededAddr = LpPositionsStat['poolStatus']['token1']
		tokenRepayAddr = LpPositionsStat['poolStatus']['token0']

		amountToken1 = amountNeeded / (10 ** token1Dec)
		repayToken0 = amountToken1 * T1perT0
		weiToRepay = int(repayToken0 * (10 ** token0Dec))
	
	print("check params to swap: ")
	print(OWNER, "droid request", tokenNeededAddr, amountNeeded, hedgeVaultId)
	print(hedgeEvmAddress['address'], "repay hedge", tokenRepayAddr, weiToRepay, droidVaultId)
	print()
	
	
	# send tokenNeeded from OWNER to Hedge
	txHash = fordefiErc20Tx.sendTokenTx(OWNER, "droid request", tokenNeededAddr, str(amountNeeded), hedgeVaultId)
	if txHash == "fail":
		session_logger.info('Swap Fail!')
		return {"requestTx": "fail", "repayTx": "null"}	#"fail"

	# repay hedge with equivalent token
	repayHash = fordefiErc20Tx.sendTokenTx(hedgeEvmAddress['address'], "repay hedge", tokenRepayAddr, str(weiToRepay), droidVaultId)

	return {"requestTx": txHash, "repayTx": repayHash}
	

def checkForSwap(amount0_desired, amount1_desired):
	time.sleep(4)
	amount0_avail=getErc20Balance.get_erc20_balance_wei(LpPositionsStat['poolStatus']['token0'], OWNER)
	amount1_avail=getErc20Balance.get_erc20_balance_wei(LpPositionsStat['poolStatus']['token1'], OWNER)
	print("amount0_avail, amount0_desired: ", amount0_avail, ", ", amount0_desired)
	print("amount1_avail, amount1_desired: ", amount1_avail, ", ", amount1_desired)
	print()
	if(amount0_avail<amount0_desired): 
		session_logger.info('Token0 funding is LOW!')
		print("   ⚠️  Token0 funding is LOW!")
		print()
		#amount0_desired=int(.75*amount0_avail)
		amountNeeded=amount0_desired-amount0_avail
		print("   ⚠️  Token0 funding is LOW!")
		print("amountNeeded: ", amountNeeded)
		print()		
		return amountNeeded, "token0"
	if(amount1_avail<amount1_desired): 
		amountNeeded=amount1_desired-amount1_avail
		session_logger.info('Token1 funding is LOW!')
		print("   ⚠️  Token1 funding is LOW!")
		print("amountNeeded: ", amountNeeded)
		print()		
		return amountNeeded, "token1"
	return 0, "na"


#buildMintParams(poolId, tick_lower, tick_upper, liquUSD, cursor, lp_pool_stat, lp_positions_stat)
def buildMintParams(droid, tick_lower, tick_upper, liquUSD, cursor):
	#import time
	poolId=droid['poolId']
	currTick = int(LpPoolStat['tick'])  # Current tick from global pool status

	# Token metadata
	stable_pos = LpPositionsStat['lpPool']['stableCoinPosition']	
	token0 = LpPositionsStat['poolStatus']['token0']
	token1 = LpPositionsStat['poolStatus']['token1']

	stable_dec = int(LpPoolStat['token0']['decimals'] if stable_pos == 0 else LpPoolStat['token1']['decimals'])
	watch_dec = int(LpPoolStat['token1']['decimals'] if stable_pos == 0 else LpPoolStat['token0']['decimals'])
	watch_price = float(LpPoolStat['token0']['tokenDayData'][0]['priceUSD']) if stable_pos == 1 else float(LpPoolStat['token1']['tokenDayData'][0]['priceUSD'])

	#  Handle case: currTick is outside the range
	if currTick <= tick_lower:
		# 100% watchcoin side
		stableUSD = 0
		watchUSD = liquUSD
	elif currTick >= tick_upper:
		# 100% stablecoin side
		stableUSD = liquUSD
		watchUSD = 0		
	else:
		# Normal interpolation
		ratio = (currTick - tick_lower) / (tick_upper - tick_lower)
		stableUSD = liquUSD * ratio
		watchUSD = liquUSD * (1 - ratio)

	#  Convert USD amounts to token amounts
	stable_amt = int(stableUSD * 10 ** stable_dec)
	watch_amt = int((watchUSD / watch_price) * 10 ** watch_dec)

	#  Assign amounts based on stable position
	if stable_pos == 0:
		amount0_desired = stable_amt
		amount1_desired = watch_amt
	else:
		amount0_desired = watch_amt
		amount1_desired = stable_amt

	
	amountNeeded, tokenNeeded=checkForSwap(amount0_desired, amount1_desired)
	if (tokenNeeded!="na"): 
		swapResults=swapRoutine(amountNeeded, tokenNeeded, droid, cursor)
		print("swapResults: ", swapResults)
		print()
		return "fail"
	
	#  Build mint parameters
	mintParams = {
		"token0": token0,
		"token1": token1,
		"fee": LpPositionsStat['lpPool']['feeTier'],
		"tickLower": tick_lower,
		"tickUpper": tick_upper,
		"amount0Desired": amount0_desired,
		"amount1Desired": amount1_desired,
		"amount0Min": int(amount0_desired*.75),
		"amount1Min": int(amount1_desired*.75),
		"recipient": OWNER,
		"deadline": int(time.time()) + 300
	}

	return mintParams


def buildAddLiquParams(nftNumber, liquUSD, droid, cursor):
	# Step 0: Check liquUSD=<totalCurrentFunding
	nftArray, nftsLiquUSD = getNftArray(droid, cursor)
	totalCurrentFunding=sum(nftsLiquUSD)
	print("totalCurrentFunding: ", totalCurrentFunding)
	print()
	maxFunding=droid.get('fundingUSD', 0)
	
	
	if(maxFunding<totalCurrentFunding):
		print("error: DROID POSITIONS ARE OVERFUNDED!!")
		return "fail"	
	
	
	# Step 1: Gather data
	poolStatus = LpPositionsStat['poolStatus']
	tickLower, tickUpper = getTickRange(nftNumber)	
	currTick = int(LpPoolStat['tick'])  # Provided by global context

	# Step 2: Token roles
	stable_pos = LpPositionsStat['lpPool']['stableCoinPosition']	
	stable_dec = int(poolStatus['token0_decimals'] if stable_pos == 0 else poolStatus['token1_decimals'])
	watch_dec = int(poolStatus['token1_decimals'] if stable_pos == 0 else poolStatus['token0_decimals'])
	watch_price = float(LpPoolStat['token0']['tokenDayData'][0]['priceUSD']) if stable_pos == 1 else float(LpPoolStat['token1']['tokenDayData'][0]['priceUSD'])
	
	# Step 3: Compute liquidity split based on tick ratio
	ratio = (currTick - tickLower) / (tickUpper - tickLower)
	stableUSD = liquUSD * ratio
	watchUSD = liquUSD * (1 - ratio)

	# Step 4: Convert USD values to token amounts
	stable_amt = int(stableUSD * 10 ** stable_dec)
	watch_amt = int((watchUSD / watch_price) * 10 ** watch_dec)

	# Step 5: Assign token amounts to token0/token1
	if stable_pos == 0:
		amount0_desired = stable_amt
		amount1_desired = watch_amt
	else:
		amount0_desired = watch_amt
		amount1_desired = stable_amt

	
	amountNeeded, tokenNeeded=checkForSwap(amount0_desired, amount1_desired)
	if (tokenNeeded!="na"): 
		swapResults=swapRoutine(amountNeeded, tokenNeeded, droid, cursor)
		print("swapResults: ", swapResults)
		print()
		return "fail"
	
	# Step 6: Return structured liquidity spec
	
	return {
		"token0": LpPositionsStat['poolStatus']['token0'],
		"token1": LpPositionsStat['poolStatus']['token1'],
		"tokenId": int(nftNumber),
		"amount0Desired": amount0_desired,
		"amount1Desired": amount1_desired,
		"amount0Min": int(amount0_desired*.75),
		"amount1Min": int(amount1_desired*.75)
	}


def moveCenter(droid, existingNft, cursor):
	'''
	Move liquidity from the center position to an existing NFT (no mint).
	If existing NFT is closed → move all funds from center.
	If it already has liquidity → top it up to match center position funding.
	'''
	print("moveCenter() called")
	print()
	movedTo = 0
	movedToBot=0
	existingNftFundingUSD = getNftLiquUSD(existingNft)
	
	curveType =droid['fundingCurveType']

	# Get funding level for center
	centerNftFundingUSD = getCenterNftFunding(curveType, droid['fundingUSD'], droid['maxBots'])

	# Get current center NFT number
	currentCenterNft = getNftNumber(droid, cursor) if droid['centerPosBotId']!=0 else 0
	actualCenterNftFundingUSD= getNftLiquUSD(currentCenterNft)  if droid['centerPosBotId']!=0 else 0.00

	if existingNftFundingUSD > 0:
		print("Existing NFT is currently funded!")
		print()
		differenceUSD = centerNftFundingUSD - float(existingNftFundingUSD)

		if differenceUSD <= 0:
			print("Target NFT already fully funded or overfunded.")
			posRecord=getLpPositionRecord(existingNft, cursor)	#getPosId(existingNft, cursor)
			posId=posRecord['id']
			movedToBot=getBotId(droid['id'], posId, cursor)	#getBotId(existingNft)
			return existingNft, movedToBot

		if(actualCenterNftFundingUSD>0): 
			print("Partial move from center!")
			#perc = differenceUSD / centerNftFundingUSD if actualCenterNftFundingUSD>20 else 1.00	# TODO: check this !!!!
			perc = float(existingNftFundingUSD) / centerNftFundingUSD if actualCenterNftFundingUSD>20 else 1.00
			
			#test="y"  #test=input("Do you want to remove liquidity? ")
			print()
			#if test=="y":
			receipt=lpPositionLiquidate.remLiquAndCollFordefi(currentCenterNft, CHAIN, percentage=perc)
			if(receipt=="fail"):
				print(f"Failed to reduce liquidity by % {perc}")
			else:
				updateLpTxs(droid['id'])

			
		entranceParams = buildAddLiquParams(existingNft, differenceUSD, droid, cursor)
		print("entranceParams: ", entranceParams)
		print()
		#test="y"  #test=input("Do you want to ADD liquidity? ")
		#print()
		if entranceParams!="fail":
			tx_hash, addLiquError = v3AddLiquidity.addLiquFordefi(entranceParams, CHAIN)
			updateLpTxs(droid['id'])
			posRecord=getLpPositionRecord(existingNft, cursor)	#getPosId(existingNft, cursor)
			posId=posRecord['id']
			movedToBot=getBotId(droid['id'], posId, cursor)	#getBotId(existingNft)
			return existingNft, movedToBot
		else:
			return existingNft, movedToBot
	else:
		print("Existing NFT is NOT funded!")
		print()
		# Fully liquidate center and move entire allocation
		
		if(actualCenterNftFundingUSD>0): 
			print("Moving center to existing NFT. Existing NFT is not funded.")
			print()
			receipt=lpPositionLiquidate.remLiquAndCollFordefi(currentCenterNft, CHAIN)
			if(receipt=="fail"): return movedTo, movedToBot
			time.sleep(12)
			setPositions(droid['poolId'], OWNER)	#reSet LpPositionsStat
			#updateLpTxs(droid['id'])
		entranceParams = buildAddLiquParams(existingNft, centerNftFundingUSD, droid, cursor)
		print("entranceParams: ", entranceParams)
		#test="y"  #test=input("do you want to add the Liqu to the NFT? ")
		#print()
		if entranceParams!="fail":
			tx_hash, addLiquError = v3AddLiquidity.addLiquFordefi(entranceParams, CHAIN)
			#time.sleep(10)
			#setPositions(droid['poolId'], OWNER)	#reSet LpPositionsStat
			updateLpTxs(droid['id'])
		print("existingNft, movedToBot: ", existingNft, movedToBot)
		print()
		return existingNft, movedToBot

	return movedTo, movedToBot # Optional fallback


def centerRebalance(droid, cursor, connection):
	print("\n📍 Calling centerRebalance")

	poolTickSpacing = LpPositionsStat['poolStatus']['tick_spacing']
	currTickBucketLow, currTickBucketHigh = getCurrTickBucket(int(LpPoolStat['tick']), poolTickSpacing)
	print(f"Current Tick Buckets → Low: {currTickBucketLow}, High: {currTickBucketHigh}")

	# Decide new range based on EMA derivative
	newRangeLow = currTickBucketLow
	newRangeHigh = currTickBucketHigh

	if LpPoolStat['ema_derivative'] > LpPoolStat['derivativeHigh']:
		print("🟢 Strategy: build_UP")
		newRangeHigh = currTickBucketLow + droid['tickBuckets'] * poolTickSpacing
	elif LpPoolStat['ema_derivative'] < LpPoolStat['derivativeLow']:
		print("🔴 Strategy: build_DN")
		newRangeLow = currTickBucketLow - droid['tickBuckets'] * poolTickSpacing
	else:
		print("🟡 Strategy: build_OUT")
		for n in range(1, droid['tickBuckets']):
			if LpPoolStat['ema_derivative'] > 0:
				# Start expansion on high side
				if n % 2 != 0:
					newRangeHigh += poolTickSpacing
				else:
					newRangeLow -= poolTickSpacing
			else:
				# Start expansion on low side
				if n % 2 != 0:
					newRangeLow -= poolTickSpacing
				else:
					newRangeHigh += poolTickSpacing

	print(f"📈 Proposed Range → Low: {newRangeLow}, High: {newRangeHigh}")

	# Check that current tick falls within new range
	currentTick = int(LpPoolStat['tick'])
	if newRangeLow > currentTick or newRangeHigh < currentTick:
		print("❌ Proposed range does NOT include current tick. Skipping.")
		return {"status": "skipped", "reason": "tick out of range"}

	# Check if that LP position already exists
	existingNft = getExistingNft(newRangeLow, newRangeHigh)
	currentNft = getNftNumber(droid, cursor) if droid['centerPosBotId'] != 0 else 0

	print(f"🔍 existingNft: {existingNft}, currentNft: {currentNft}")

	if existingNft == 0:
		# Minting a new NFT position
		print("🛠️  No existing NFT, creating new one")

		currentNftLiquUSD = getNftLiquUSD(currentNft) if droid['centerPosBotId'] != 0 else 0.0
		if currentNftLiquUSD > 0:
			# Remove liquidity for existing position
			receipt = lpPositionLiquidate.remLiquAndCollFordefi(int(currentNft), CHAIN)	#, percentage=1.0, liquidity=0, priority=1)
			if receipt == "fail":
				print("⚠️  Error removing existing liquidity!")
				return {"status": "failed", "step": "remove_liquidity"}
			updateLpTxs(droid['id'])

		# Build and execute mint
		curveType = droid['fundingCurveType']
		centerNftFundingUSD = getCenterNftFunding(curveType, droid['fundingUSD'], droid['maxBots'])
		
		#            buildMintParams(poolId,           tick_lower,   tick_upper,  liquUSD, cursor, lp_pool_stat, lp_positions_stat)
		mintParams = buildMintParams(droid, newRangeLow, newRangeHigh, centerNftFundingUSD, cursor)	#, LpPoolStat, LpPositionsStat)

		if mintParams == "fail":
			print("❌ Failed to build mint params")
			return {"status": "failed", "step": "mint_build"}

		txHash = v3Mint.mintFordefi(mintParams, CHAIN)
		updateLpTxs(droid['id'])
		newNftInserts.newNftInserts(txHash, droid['centerPosBotId'])

		return {"status": "minted", "newRangeLow": newRangeLow, "newRangeHigh": newRangeHigh}

	else:
		# Move to existing NFT
		print("📦 Moving to existing NFT")
		movedToNft, movedToBot = moveCenter(droid, existingNft, cursor)
		newLpPositionId = newNftInserts.insertMainNetNftAsset(movedToNft, droid['poolId'])

		prevLpPositionId = getLpPosId(droid['centerPosBotId'], cursor)

		if newLpPositionId != 0:
			sql = f"UPDATE PositionBots SET lpPositionId = {newLpPositionId}, droidId = {droid['id']} WHERE id = {droid['centerPosBotId']}"
			cursor.execute(sql)
			connection.commit()
		else:
			lpPositionRecord = getLpPositionRecord(existingNft, cursor)
			if lpPositionRecord:
				registerPositionBot(droid['centerPosBotId'], droid, lpPositionRecord['id'], 0, cursor, connection)
			else:
				print("❗ ERROR: Could not register bot. Missing LP position record.")

		if movedToBot != 0:
			sql = f"UPDATE PositionBots SET lpPositionId = {prevLpPositionId}, droidId = {droid['id']} WHERE id = {movedToBot}"
			cursor.execute(sql)
			connection.commit()

		return {"status": "moved", "movedToNft": movedToNft, "movedToBot": movedToBot}



def get_ladder_tick_range(droid, cursor, ladder_index: int, offset_multiplier: int):
	"""
	Calculate tickLower and tickUpper for a ladder step.
	
	- ladder_index: the position index in the ladder (for clarity, but not used directly here)
	- offset_multiplier: how many tickSpacing units away from the center to shift upward (positive) or downward (negative)
	- tickBuckets: how many tickSpacing units wide each ladder position is (from droid['tickBuckets'])
	"""
	assert isinstance(offset_multiplier, int), "Offset must be integer"
	assert ladder_index >= 1, "Ladder index must be >= 1"

	#from utils.position_utils import get_lp_range  # Adjust if needed
	center_nft = getNftNumber(droid, cursor)
	tick_spacing = int(LpPoolStat.get("tickSpacing", 60))	#TODO: FIX THIS
	tickBuckets = droid["tickBuckets"]	

	# Get center position tick bounds
	centerTickLower, centerTickUpper = getTickRange(center_nft)
	print("centerTickLower, centerTickUpper: ", centerTickLower, centerTickUpper)
	print()

	if offset_multiplier >= 0:
		# Anchor at centerTickUpper and extend up
		base_tick = centerTickLower + offset_multiplier * tick_spacing * ladder_index
		tickLower = base_tick
		tickUpper = base_tick + tickBuckets * tick_spacing
	else:
		# Anchor at centerTickLower and extend down
		base_tick = centerTickUpper + offset_multiplier * tick_spacing * ladder_index  # subtracts because offset is negative
		tickUpper = base_tick
		tickLower = base_tick - tickBuckets * tick_spacing

	return tickLower, tickUpper

def registerPositionBot(botId, droid, lpPositionId, txHash, cursor, connection):
	"""
	Handles registration of a PositionBot depending on the type of action:
	- If txHash is provided, it assumes a new position was minted and calls newNftInserts.
	- If lpPositionId is provided, it assumes an existing position was reassigned.
	"""
	droid_id=droid["id"]
	if(botId==0):
		print("New bot needed for droid")
		poolId=droid['poolId']
		botId=insertPositionBot.insertDroidPosBot("Ethereum", poolId, lpPositionId, droid['id'])
	
	if txHash != 0:
		# Minted position case
		#from utils import newNftInserts  # Adjust path as needed
		newNftInserts.newNftInserts(txHash, botId)
		print(f"Registered new minted position with txHash {txHash} to PositionBot #{botId}")

	elif lpPositionId != 0:
		# Relocated position case
		sql = f"UPDATE PositionBots SET lpPositionId = {lpPositionId}, droidId = {droid_id} WHERE id = {botId}"
		cursor.execute(sql)
		connection.commit()
		print(f"Reassigned PositionBot #{botId} to lpPositionId {lpPositionId}")

	else:
		print("Warning: Both txHash and lpPositionId are 0 — nothing to update.")


def handle_existing_nft_extension(nftNumber, droid, ladder_index, botId, cursor, connection):
	print(f"  ➤ Reusing existing NFT #{nftNumber}")

	fundingUSD = getLadderIndexFunding(
		droid.get("fundingCurveType", "linear"),
		droid["fundingUSD"],
		droid["maxBots"],
		ladder_index
	)

	print(f"  Funding (USD): {fundingUSD}")
	entranceParams = buildAddLiquParams(nftNumber, fundingUSD, droid, cursor)
	print("entranceParams: ", entranceParams)
	print()
	
	if entranceParams!="fail":
		if entranceParams['amount0Desired'] <= 0 or entranceParams['amount1Desired'] <= 0:
			print("  ✘ Position out of range — skipping.")
			return 2

	print("  Liquidity Params:", entranceParams)
	#if input("  Continue to add liquidity? (y/n): ").lower() == "y":
	if entranceParams!="fail":
		tx_hash, addLiquError = v3AddLiquidity.addLiquFordefi(entranceParams, CHAIN)
		updateLpTxs(droid['id'])

	lpPositionRecord = getLpPositionRecord(nftNumber, cursor)
	if lpPositionRecord and entranceParams!="fail" and addLiquError=="success":
		registerPositionBot(botId, droid, lpPositionRecord['id'], 0, cursor, connection)
	else:
		print("  ✘ No LP record found or entranceParams: fail! — registration skipped.")
		return 1

	return 0

def handle_new_mint_position(droid, ladder_index, tickLower, tickUpper, botId, cursor, connection):
	print("  ➤ Minting new position...")

	fundingUSD = getLadderIndexFunding(
		droid.get("fundingCurveType", "linear"),
		droid["fundingUSD"],
		droid["maxBots"],
		ladder_index
	)

	print(f"  Funding (USD): {fundingUSD}")
	
	#buildMintParams(poolId, tick_lower, tick_upper, liquUSD, cursor, lp_pool_stat, lp_positions_stat)
	mintParams = buildMintParams(droid, tickLower, tickUpper, fundingUSD, cursor)	#, LpPoolStat, LpPositionsStat)

	if(mintParams!="fail"):
		if mintParams['amount0Desired'] <= 0 or mintParams['amount1Desired'] <= 0:
			print("  ✘ Mint parameters out of range — skipping.")
			return 3

		print("  Mint Params:", mintParams)
		#if input("  Continue to mint? (y/n): ").lower() == "y":
		txHash = v3Mint.mintFordefi(mintParams, CHAIN)
		updateLpTxs(droid['id'])
		registerPositionBot(botId, droid, 0, txHash, cursor, connection)
	else:
		print("  ✘ Mint parameters out of range OR buildMint: fail — skipping.")
		return 3
	
	return 0


def extendLadderPosition(droid, ladder_index: int, offset_multiplier: int, cursor, connection, botId):
	print("\nExtending ladder:")
	print(f"  Ladder Index       : {ladder_index}")
	print(f"  Offset Multiplier  : {offset_multiplier}")
	print(f"  Assigned Bot ID    : {botId}\n")

	tickLower, tickUpper = get_ladder_tick_range(droid, cursor, ladder_index, offset_multiplier)
	print(f"  Target Range: [{tickLower}, {tickUpper}]")

	existing_nft = getExistingNft(tickLower, tickUpper)
	if existing_nft != 0:
		errorStat = handle_existing_nft_extension(existing_nft, droid, ladder_index, botId, cursor, connection)
	else:
		errorStat = handle_new_mint_position(droid, ladder_index, tickLower, tickUpper, botId, cursor, connection)

	connection.commit()
	return errorStat

def checkExtendLadderPos(droid, ladder_index: int, offset_multiplier: int, cursor, connection):
	print("\nExtending ladder:")
	print(f"  Ladder Index       : {ladder_index}")
	print(f"  Offset Multiplier  : {offset_multiplier}")
	
	tickLower, tickUpper = get_ladder_tick_range(droid, cursor, ladder_index, offset_multiplier)
	print(f"  Target Range: [{tickLower}, {tickUpper}]")
	
	currTick=int(LpPoolStat['tick'])
	percInRange=(currTick-tickLower)/(tickUpper-tickLower)
	print("percInRange: ", percInRange)
	print()
	return percInRange


def remove_position(droid, cursor, connection, direction="highest"):
	"""
	Removes either the highest or lowest priced position in a droid's position ladder.

	Args:
		droid: dict containing the droid record.
		cursor: MySQL cursor for DB access.
		connection: MySQL connection for commits.
		direction: "highest" or "lowest" — determines which position to remove.

	Returns:
		botId (int) of the removed bot, or 0 on failure.
	"""

	droid_id = droid["id"]
	cursor.execute("SELECT id, lpPositionId FROM PositionBots WHERE droidId = %s", (droid_id,))
	bots = cursor.fetchall()

	if not bots:
		print(f"No PositionBots found for Droid #{droid_id}")
		return 0

	nft_info = []
	for bot in bots:
		bot_id = bot["id"]
		lp_position_id = bot["lpPositionId"]

		cursor.execute("SELECT nftNumber FROM LpPositions WHERE id = %s", (lp_position_id,))
		row = cursor.fetchone()
		if not row:
			continue
		nft_number = int(row["nftNumber"])

		pos = next((p for p in LpPositionsStat['positions'] if str(p['nftNumber']) == str(nft_number)), None)
		if pos:
			nft_info.append({
				"nftNumber": nft_number,
				"price_center": pos["watchCoinPriceCenter"],
				"bot_id": bot_id,
				"liquidityUSD": pos['valueUSD']
			})

	if not nft_info:
		print("No matching position data found in LpPositionsStat.")
		return 0

	# Choose based on direction
	reverse_sort = True if direction == "highest" else False
	nft_info_sorted = sorted(nft_info, key=lambda x: x["price_center"], reverse=reverse_sort)

	target = nft_info_sorted[0]
	nftNumber = target["nftNumber"]
	botId = target["bot_id"]
	liquidityUSD=target["liquidityUSD"]
	
	if(liquidityUSD>0):
		print(f"Removing {direction} position NFT #{nftNumber} (botId #{botId})")
		print()
		try:
			#from utils import lpPositionLiquidate
			test="y"  #test=input("Do you want to remove liquidity? ")
			print()
			if test=="y":
				receipt=lpPositionLiquidate.remLiquAndCollFordefi(int(nftNumber), CHAIN)
				if (receipt=="fail"): return 0
				else: updateLpTxs(droid['id'])
		except Exception as e:
			print(f"Error removing liquidity for NFT #{nftNumber}: {e}")
			return 0
	else:
		print("Liqudidity value = 0. No remove_and_collect() needed.")
		print()
	
	time.sleep(12)
	setPositions(droid['poolId'], OWNER)
	
	return botId


def pruneDroid(droid, cursor, connection):
	print("Pruning droid !")
	if droid['centerPosBotId']==0:
		print("Droid NOT initialized!!")
		print()
		return 0
	print("removing most out of range bot-position")
	print()
	nftArray, nftsLiquUSD, lpPosArray, botArray, ratioArray=prepare_droid_arrays(droid, cursor, connection)
	print("nftArray, nftsLiquUSD, lpPosArray, botArray, ratioArray: ")
	print(nftArray, nftsLiquUSD, lpPosArray, botArray, ratioArray)
	print()
	max_dev_index=index_furthest_from_50_50(ratioArray)
	print("max_dev_index: ", max_dev_index)
	print()
	inRange=classify_ratio_sign(ratioArray[max_dev_index]) if max_dev_index!=None else 0
	print("inRange: ", inRange)
	print()
	
	max_gas_calc=getMaxGasGwei(droid['fundingUSD'])
	print("max_gas_calc: ", max_gas_calc)
	print()
	gasCheck=getGasCheck(max_gas_calc)	#True/False return. 
	
	if(inRange<0 and gasCheck):
		print(f"Item {max_dev_index} to be removed !!")
		print()	
		try:
			#from utils import lpPositionLiquidate
			test="y"  #test=input("Do you want to remove liquidity? ")
			print()
			if test=="y":
				receipt=lpPositionLiquidate.remLiquAndCollFordefi(nftArray[max_dev_index], CHAIN)
				if(receipt=="fail"): return 0
				updateLpTxs(droid['id'])
		except Exception as e:
			print(f"Error removing liquidity for NFT #{nftArray[max_dev_index]}: {e}")
			return 0
		sql = f"UPDATE PositionBots SET lpPositionId=0, droidId=0 WHERE id = {botArray[max_dev_index]}"
		cursor.execute(sql)
		connection.commit()
		
	else: 
		reDistrAction=fundingDistrCheck(droid, cursor, connection)
		print("reDistrAction: ", reDistrAction)
		print()

def classify_ratio_sign(ratio_str):
	"""
	Classify a ratio string like '50:50', '-51:151', or '0:100'.

	Returns:
	-1 if either value is negative  
	 0 if either value is zero  
	 1 if both values are positive
	"""
	try:
		a_str, b_str = ratio_str.split(":")
		a = float(a_str)
		b = float(b_str)

		if a < 0 or b < 0:
			return -1
		elif a == 0 or b == 0:
			return 0
		else:
			return 1
	except Exception as e:
		print(f"Invalid ratio format '{ratio_str}': {e}")
		return None  # You could raise an error instead if preferred


def percentInRange(strRatio):
	try:
		a_str, b_str = strRatio.split(":")
		a = float(a_str)
		b = float(b_str)
		return a
	except Exception as e:
		print(f"Problem calculating percentInRange: {e}")
		print()
		return None

def index_furthest_from_50_50(ratios):
	"""
	Returns the index of the ratio that is furthest from a 50:50 balance,
	ignoring the first index (index 0).
	Each ratio is expected as a string "a:b".
	"""
	if len(ratios) <= 1:
		return None

	deviations = []

	for i in range(1, len(ratios)):  # Start from index 1
		try:
			a_str, b_str = ratios[i].split(":")
			a = float(a_str)
			b = float(b_str)
			score = abs(a - 50) + abs(b - 50)
			deviations.append((i, score))
		except Exception as e:
			print(f"Skipping invalid ratio '{ratios[i]}': {e}")

	if not deviations:
		return None

	# Return index with highest deviation
	return max(deviations, key=lambda x: x[1])[0]

def checkFunds(percT1, index, droid):
	print(f"Checking for funds avail for position pecent in range {percT1}")
	print()
	isFundingAvail=False
	'''
	indexMaxFundingUSD=getLadderIndexFunding(droid['fundingCurveType'], droid['fundingUSD'], droid['maxBots'], index)
	amountNeededT1USD=percT1*indexMaxFundingUSD
	amountNeededT0USD=abs(indexMaxFundingUSD-amountNeededT1USD)
	
	amountNeededWeiT1=convertUSDtoWEI(amountUSD, token)
	t0dec=getT0Dec()
	amountNeededWeiT0=(amountNeededT0USD/t0priceUSD)*10**t0dec
	
	swapAmount, swapToken=checkForSwap(amountNeededWeiT0, amountNeededWeiT1)
	if(swapAmount==0): isFundingAvail=True
	'''
	return isFundingAvail

def authorizeLadderOp(droid, cursor, proposedPercInRange, ladder_structure):
	print("Request for Ladder Op: calling authorizeLadderOp()")
	#START !!!!!!!EVALUATE IN RANGE AMOUNT FOR LADDERING!!!!!!!!!
	if(len(ladder_structure) >= droid['maxBots']):
		#botId = remove_position(droid, cursor, connection, direction="highest")
		nftArray, nftsLiquUSD = getNftArray(droid, cursor)
		nftIndex=droid['maxBots']-1
		print("nftIndex: ", nftIndex)
		#print()
		nftNumber=nftArray[nftIndex]			
		existingRatio=getRatio(nftNumber)
		print("existingRatio: ", existingRatio)
		#print()
		existingPercInRange=(percentInRange(existingRatio))/100
		print("existingPercInRange: ", existingPercInRange)
		#print()
		#'WHO' is closer to 50:50: existingPerInRange or percInRange
		#existingDistanceTo5050=abs(existingPercInRange-50)
		#proposedDistanceTo5050=abs(proposedPercInRange-50)
		existingDistanceTo5050=abs(existingPercInRange-.50)
		proposedDistanceTo5050=abs(proposedPercInRange-.50)		
		print("existingDistanceTo5050: ", existingDistanceTo5050)
		print("proposedDistanceTo5050: ", proposedDistanceTo5050)
		percMargin=.03	#margin to surpase to avoid continous 'flip-flop'
		if(existingDistanceTo5050>(proposedDistanceTo5050+percMargin)):
			#proposed is closer
			fundingAvail=checkFunds(proposedPercInRange, nftIndex, droid)	
			if (fundingAvail): 
				print("Ladder OP authorized!")
				return True
			else:
				print("No funds avail for ladder op. Op NOT authorized")
				return False
		else:
			#existing is closer
			print("Ladder OP NOT authorized!")
			return False		
		print()
	else:
		return True
	#END !!!!!!!EVALUATE IN RANGE AMOUNT FOR LADDERING!!!!!!!!!


def ladderDn(droid, cursor, connection):
	error="na"
	
	try:
		ladder_structure = get_ladder_structure(droid, cursor)
	except Exception as e:
		print(f"get Ladder stucture error: {e}")
		print()
		return "ladderStuctureError"
	
	offset_multiplier=droid.get("bucketOffset", 1)	
	case = determine_ladder_case(ladder_structure, offset_multiplier)
	tickBuckets = droid.get("tickBuckets", 0)

	print("case: ", case)
	print()

	if case == LADDER_CASES["ORIGINAL"]:
		if(len(ladder_structure)<droid['maxBots']):
			botId = 0
			extendLadderPosition(droid, 1, -offset_multiplier, cursor, connection, botId)
		else:
			print("Overlapping ladder structure!!")
			print("Remove greatest indexed bot!")
			nftArray, nftsLiquUSD = getNftArray(droid, cursor)
			nftNumber=nftArray[1]
			receipt=lpPositionLiquidate.remLiquAndCollFordefi(int(nftNumber), CHAIN)
			if (receipt!="fail"): updateLpTxs(droid['id'])
			print()

	elif case == LADDER_CASES["EXT_DOWN"]:
		down_count = sum(1 for x in ladder_structure if x <= 0)
		if down_count < droid['maxBots']:
			botId = 0
			extendLadderPosition(droid, down_count, -(offset_multiplier), cursor, connection, botId)
		else:
			reDistrAction=fundingDistrCheck(droid, cursor, connection)
			print("reDistrAction: ", reDistrAction)
			print()

	elif case == LADDER_CASES["EXT_UP"]:
		#ladder_structure = get_ladder_structure(droid, cursor)
		#down_count = sum(1 for x in ladder_structure if x <= 0)
		#ladder_index=	1	#len(ladder_structure)-1	#down_count + 0 #if ladder_index==9999 else ladder_index		
		ladder_index=droid['maxBots']-1 if len(ladder_structure)>=droid['maxBots'] else len(ladder_structure)

		percInRange=checkExtendLadderPos(droid, ladder_index, -(offset_multiplier), cursor, connection)
		print("Proposed position percent in range: ", percInRange)
		print()		
		#performLadderOp=True
		performLadderOp=authorizeLadderOp(droid, cursor, percInRange, ladder_structure)
		
		
		if(percInRange>0 and percInRange<1 and performLadderOp):
			#ladder_index=9999
			if(len(ladder_structure) >= droid['maxBots']):
				botId = remove_position(droid, cursor, connection, direction="highest")
			else:
				botId = 0
			
			extendLadderPosition(droid, ladder_index, -(offset_multiplier), cursor, connection, botId)
			#checkExtendLadderPos(droid, ladder_index: int, offset_multiplier: int, cursor, connection)
		else:
			print("Proposed Position NOT in Range. Ladder NOT extended !")
			print()
	
	else:
		print("Non-standard ladder structure case — reEvaluating.")
		pruneDroid(droid, cursor, connection)
	
	return error

def fundingDistrCheck(droid, cursor, connection):
	print("🧠 Funding distribution check!")
	print()
	nftArray, nftsLiquUSD, lpPosArray, botArray, ratioArray=prepare_droid_arrays(droid, cursor, connection)
	n=-1
	if len(nftsLiquUSD)>droid['maxBots']: 
		print("Max Bot error")
		print("len(nftsLiquUSD) : ", len(nftsLiquUSD))
		print()
		removeNft= nftArray[len(nftsLiquUSD)-1]
		if(nftsLiquUSD[len(nftsLiquUSD)-1])>0: 
			receipt=lpPositionLiquidate.remLiquAndCollFordefi(removeNft, CHAIN)
			#update droidId to botArray[len(nftsLiquUSD)-1] bot record
			if (receipt!="fail"):
				botId=botArray[len(nftsLiquUSD)-1]
				sql = f"UPDATE PositionBots SET droidId=0 WHERE id = {botId}"
				cursor.execute(sql)
				connection.commit()
				return "nftRemoved"
		else:
			#remove DroidId from Botrecord
			botId=botArray[len(nftsLiquUSD)-1]
			sql = f"UPDATE PositionBots SET droidId=0 WHERE id = {botId}"
			cursor.execute(sql)
			connection.commit()		
			return "nftRemoved"	

	
	for liquUSD in nftsLiquUSD:
		n=n+1
		expectedFunding = getLadderIndexFunding(
			droid.get("fundingCurveType", "linear"),
			droid["fundingUSD"],
			droid["maxBots"],
			n
		)
		print("expectedFunding: ", expectedFunding)
		print()
		percDiff=(expectedFunding-liquUSD)/expectedFunding 
		print("percDiff: ", percDiff)
		print()
		if abs(percDiff)>.25:
			if(percDiff>0):
				print(f"Bot-position is UNDER fundeded. ADD funds to {nftArray[n]}!")
				print(f"Percent to add: {percDiff}")
				print("Amount to add USD: ", (expectedFunding-liquUSD))
				print("Ladder Index to add to: ", n)
				print()
				entranceParams = buildAddLiquParams(nftArray[n], (expectedFunding-liquUSD), droid, cursor)
				if(entranceParams!="fail"): 
					tx_hash, addLiquError = v3AddLiquidity.addLiquFordefi(entranceParams, CHAIN)
					updateLpTxs(droid['id'])
					return "fundsAdded"
				else:
					print(f"entrance params fail: {entranceParams}")
					
			if(percDiff<0):
				print(f"Bot-position is OVER fundeded. REMOVE funds from {nftArray[n]}!")
				print()	
				#test=input("MANUAL OPERATIONS NEEDED!")
				
				perc=(liquUSD-expectedFunding)/liquUSD	#abs(percDiff)
				print("Percent to remove: ", perc)
				print()
				receipt="fail"
				if(perc>0 and perc<1): receipt=lpPositionLiquidate.remLiquAndCollFordefi(nftArray[n], CHAIN, percentage=perc)
				if(receipt!="fail"): 
					updateLpTxs(droid['id'])
					return "fundsReducedNeeded"
	
	return "noChanges"
	
def ladderUp(droid, cursor, connection):
	#ladder_structure = get_ladder_structure(droid, cursor)
	error="na"
	
	try:
		ladder_structure = get_ladder_structure(droid, cursor)
	except Exception as e:
		print(f"get Ladder stucture error: {e}")
		print()
		return "ladderStuctureError"	
	
	offset_multiplier=droid.get("bucketOffset", 1)	
	case = determine_ladder_case(ladder_structure, offset_multiplier)
	tickBuckets = droid.get("tickBuckets", 0)
	
	print("case: ", case)
	print()

	if case == LADDER_CASES["ORIGINAL"]:
		#NOTE: extendLadderPosition(droid, ladder_index: int, offset_multiplier: int, cursor, connection):
		if(len(ladder_structure)<droid['maxBots']):
			botId=0
			extendLadderPosition(droid, +1, offset_multiplier, cursor, connection, botId)
		else:
			print("Overlapping ladder stucture!")
			print("Remove greatest indexed bot!")
			nftArray, nftsLiquUSD = getNftArray(droid, cursor)
			nftNumber=nftArray[1]
			receipt=lpPositionLiquidate.remLiquAndCollFordefi(int(nftNumber), CHAIN)
			if (receipt!="fail"): updateLpTxs(droid['id'])
			print()

	elif case == LADDER_CASES["EXT_UP"]:
		up_count = sum(1 for x in ladder_structure if x >= 0)
		#up_count=len(ladder_structure)-1
		if up_count < droid['maxBots']:
			botId=0
			extendLadderPosition(droid, up_count, offset_multiplier, cursor, connection, botId)
		else:
			reDistrAction=fundingDistrCheck(droid, cursor, connection)
			print("reDistrAction: ", reDistrAction)
			print()

	elif case == LADDER_CASES["EXT_DOWN"]:
		#ladder_index=1	#up_count + 0 #if ladder_index==9999 else ladder_index		
		#ladder_index=len(ladder_structure)-1
		ladder_index=droid['maxBots']-1 if len(ladder_structure)>=droid['maxBots'] else len(ladder_structure)
		percInRange=checkExtendLadderPos(droid, ladder_index, (offset_multiplier), cursor, connection)
		performLadderOp=authorizeLadderOp(droid, cursor, percInRange, ladder_structure)
		if(percInRange>0 and percInRange<1 and performLadderOp):				
			#ladder_index=9999
			if(len(ladder_structure) >= droid['maxBots']):
				botId = remove_position(droid, cursor, connection, direction="lowest")
			else:
				botId = 0
			
			extendLadderPosition(droid, ladder_index, (offset_multiplier), cursor, connection, botId)
		else:
			print("Proposed Position NOT in Range. Ladder NOT extended !")
			print()

	else:
		print("non-Standard ladder structure case (DisArray).")
		pruneDroid(droid, cursor, connection)
	
	return error
			
def getGasCheck(maxGasPrice):
	print("Gas Check Here!!")
	gasRange=getMainNetGas.getGasRange()	
	print("gasRange: ", gasRange)
	print()
	if(maxGasPrice==0.0):
		test="y"  #test=input("Is this gas Range acceptable? (y/n): ")
		if test=="y": return True
	else:
		if(gasRange[3]<maxGasPrice): return True
	return False

def getMaxGasGwei(funding_usd, expected_fee_per_1000=15, gas_budget_ratio=0.25, estimated_gas_units=290_000):
	"""
	Estimate the maximum acceptable gas price (in GWEI) for creating/rebalancing a Uniswap V3 position.

	Args:
	- funding_usd (float): Total liquidity being provided in USD.
	- expected_fee_per_1000 (float): Estimated fee return per $1000 of funding (e.g., $15).
	- gas_budget_ratio (float): Portion (0–1) of the expected fee return you're willing to spend on gas (e.g., 0.25 = 25%).
	- estimated_gas_units (int): Estimated gas units for mint or rebalance operation (default = 200,000).

	Returns:
	- max_gas_price_gwei (float): The max gas price in GWEI you should allow for this operation.
	"""

	# Estimate expected return
	expected_fees = (funding_usd / 1000) * expected_fee_per_1000
	
	# Allow only a fraction of that for gas
	max_gas_cost_usd = expected_fees * gas_budget_ratio

	# Estimate acceptable GWEI price
	# gas_price_usd = gas_units * gas_price_gwei * 1e-9 * eth_price
	eth_price_usd = float(LpPoolStat['token0']['tokenDayData'][0]['priceUSD'])
	max_gas_price_gwei = (max_gas_cost_usd / (estimated_gas_units * eth_price_usd)) * 1e9
	maxGasPriceOveride=15	#TODO: FIX THIS to operator control
	if(max_gas_price_gwei>maxGasPriceOveride): max_gas_price_gwei=maxGasPriceOveride	
	return round(max_gas_price_gwei, 2)

	
def perform_droid_action(droid: dict, action: str, cursor, connection):
	result="Attempted"+action
	max_gas_calc=getMaxGasGwei(droid['fundingUSD'])
	print("max_gas_calc: ", max_gas_calc)
	print()
	#gasCheck=getGasCheck(max_gas_calc)	#True/False return. 
	gasCheck=True	#TODO: THIS IS A TEST REMOVE Latter.
	if(gasCheck):
		print("Updating Positions...")
		print()
		setPositions(droid['poolId'], OWNER)	#reSet LpPositionsStat
		print(f"  Performing action: {action}")
		print()
		if (action=="re_balance_UP"): result=centerRebalance(droid, cursor, connection)
		if (action=="re-balance_DN"): result=centerRebalance(droid, cursor, connection)
		if (action=="ladder_UP"): ladderUp(droid, cursor, connection)	
		if (action=="ladder_DN"): ladderDn(droid, cursor, connection)	
		
		
		print("Waiting for Subgraph update......")
		print()
		time.sleep(15)
		setPositions(droid['poolId'], OWNER)	#reSet LpPositionsStat
		
	else:
		result="gasPriceCheck-FAIL"
		print("No action perfromed: ❌️ Gas Check= Fail!!")
		print()
	
	prepare_droid_arrays(droid, cursor, connection)
	return result


def insert_droid_controller_session(droid_id, cursor, connection):
	"""
	Inserts a new session record into DroidControllerSessions with only the droidId.
	The timestamp is auto-set by the DB, other fields remain NULL/default.
	"""
	try:
		query = "INSERT INTO DroidControllerSessions (droidId) VALUES (%s);"
		cursor.execute(query, (droid_id,))
		connection.commit()
		print(f"✅ New session started for Droid ID {droid_id}")
		return cursor.lastrowid  # Return the inserted session ID
	except Exception as e:
		print(f"❌ Failed to insert session: {e}")
		return None


def run():
	DROID_ID = int(input("Enter droid ID: "))
	while True:
		try:
			main(DROID_ID)
			break  # Exit loop on successful completion
		except Exception as e:
			print(f"\n❌ An error occurred: {e}")
			print("🔁 Restarting program...\n")
			time.sleep(30)  # Optional pause before restarting

def ladderGraphic(ladder_structure, droid, cursor):
	centerTickLower=getCenterTickLower(droid, cursor)
	drawLadderGraphic.draw_staggered_ladder(ladder_structure, droid['tickBuckets'], int(LpPoolStat['tick']), int(LpPositionsStat['poolStatus']['tick_spacing']), centerTickLower, droid['bucketOffset'])
	print()					


def update_droid_controller_session(cursor, connection):
	for droid_id, session_data in DROID_SESSION.items():
		session_id = session_data.get('sessionId')
		if not session_id:
			message = f"❌ No sessionId for droidId {droid_id}, skipping update."
			print(message)
			session_logger.info(message)
			continue

		query = """
			UPDATE DroidControllerSessions
			SET 
				status = %s,
				startingEthGasAmount = %s,
				actionResult = %s,
				prevActionTime = %s,
				triggerStatReady = %s,
				loopCycleCount = %s,
				triggerStatSet = %s,
				breakerTrip = %s
			WHERE id = %s;
		"""

		values = (
			session_data.get('status'),
			session_data.get('startingEthGasAmount'),
			session_data.get('actionResult'),
			session_data.get('prevActionTime'),
			session_data.get('triggerStatReady'),
			session_data.get('loopCycleCount'),
			session_data.get('triggerStatSet'),
			session_data.get('breakerTrip'),
			session_id
		)

		try:
			cursor.execute(query, values)
			connection.commit()
			message = f"✅ Updated DroidControllerSession ID {session_id} for Droid {droid_id}"
			print(message)
			#session_logger.info(message)
		except Exception as e:
			message = f"❌ Failed to update session ID {session_id} for Droid {droid_id}: {e}"
			print(message)
			session_logger.info(message)


def ensure_string(value):
	if isinstance(value, dict):
		# Option 1: Pretty JSON string
		return json.dumps(value)

		# Option 2: Custom "key=value" format
		# return ", ".join(f"{k}={v}" for k, v in value.items())

	else:
		# If already a string or other type, cast to string
		return str(value)


def updateSession(actionResult, prevActionTime, triggerStatReady, triggerStatSet, loopCycleCount, breakerTrip, droidId):
	print("Updating session with:")
	print(actionResult, prevActionTime, triggerStatReady, triggerStatSet, loopCycleCount, breakerTrip, droidId)
	print()
	
	if(DROID_SESSION[droidId].get('prevActionTime')):
		isUpdateSessionLogger=True if DROID_SESSION[droidId]['prevActionTime']!=int(prevActionTime) else False
	else:
		isUpdateSessionLogger=True
	
	
	#example variable set: DROID_SESSION[droid['id']]['status']= "initialized"
	actionResult=ensure_string(actionResult)
	DROID_SESSION[droidId]['actionResult']=actionResult
	DROID_SESSION[droidId]['prevActionTime']=int(prevActionTime)
	DROID_SESSION[droidId]['triggerStatReady']=triggerStatReady
	DROID_SESSION[droidId]['loopCycleCount']=loopCycleCount
	DROID_SESSION[droidId]['triggerStatSet']=triggerStatSet
	DROID_SESSION[droidId]['breakerTrip']=breakerTrip
	#update_droid_controller_session(cursor, connection)
	# Log nicely formatted status
	now=int(time.time())
	if isUpdateSessionLogger: session_logger.info(f"Session Status @ {now}: {json.dumps(DROID_SESSION, default=str)}")


	
# ---------- MAIN ENTRY ---------- #
def main(DROID_ID):
	connection = pymysql.connect(**DB_CONFIG)
	cursor = connection.cursor()	
	poolId=getPoolId(DROID_ID, cursor)
	droid = getDroid(DROID_ID, cursor)
	setOwner(droid['accountId'], cursor)
	setPositions(poolId, OWNER)
	poolAddress=getPoolAddress(poolId, cursor)	
	loopCycleCount=0
	prevAction=0
	timeOutSession=0
	prevTimeOutSession=0
	actionResult="null"
	#sessionId=insert_droid_controller_session(DROID_ID, cursor, connection)
	#print("sessionId: ", sessionId)
	#DROID_SESSION[DROID_ID]['sessionId']=sessionId
	#print("DROID_SESSION: ", DROID_SESSION)
	
	while True:	#Note: Loop Is Pool specific and Wallet specific.
		droid = getDroid(DROID_ID, cursor)
		print()
		print("-----------------------------------------🤖----------------------------------------------")		
		print("DROID_SESSION: ", DROID_SESSION)
		print("loopCycleCount: ", loopCycleCount)
		print()
		
		setPoolStat(poolAddress, droid['emaLength'])
		print("LpPoolStat: ", LpPoolStat)
		print()
		print(f"Note Droid ID {droid['id']}...")
		#print(f"Index at {active_droids.index(droid)}")
		print()
		session=getDroidSession(droid['id'], cursor, connection)
		print("session: ", session)
		print()
		
		ladder_structure = get_ladder_structure(droid, cursor)
		print("ladder_structure: ", ladder_structure)
		if(droid['centerPosBotId']!=0): 
			ladderGraphic(ladder_structure, droid, cursor)
			triggerStat = getTriggerStat(droid, cursor)
		
		if(droid['centerPosBotId']==0): triggerStat=None
		
		triggerStatReady=triggerStat
		print(f"Trigger Stat 'ready': {triggerStatReady}")
		print()
		
		#if(droid['centerPosBotId']==0): triggerStat=None
		
		if (loopCycleCount==droid['emaLength']+1): 
			triggerStat=iniDroid(droid, cursor, connection)
			if(triggerStat==None): DROID_SESSION[droid['id']]['status']= "initialized"
			ladder_structure = get_ladder_structure(droid, cursor) 
		elif (droid['centerPosBotId']==0):
			if(loopCycleCount>droid['emaLength']+1):
				triggerStat=iniDroid(droid, cursor, connection)
		
		timeOut=droid['actionTimeOut']	#60	
		if(time.time()-prevAction<timeOut): 
			triggerStat=None
			print("waiting on 'Action' time out! .... ")
			timeRemaining=timeOut-(time.time()-prevAction)
			if(prevTimeOutSession<timeOutSession):
				prevTimeOutSession=timeOutRoutines(timeOutSession, timeRemaining, droid, cursor, connection)
			print("timeRemaining: ", round(timeRemaining, 1))
			print()
		else:
			timeOutSession=timeOutSession+1
		
		if(triggerStat=="iniCenterPos"):
			print("Center Position is NOT funded AND needs to be initialized!!")
			print()
			triggerStat="fallingRebalanceTrigger"
			#loopCycleCount=loopCycleCount-1
			DROID_SESSION[droid['id']]['status'] = "ini_in_process"
		
		breakerTrip=check_breakers(droid, session)
		if(breakerTrip!=None):
			print("breakerTrip: ", breakerTrip)
			print()
			triggerStat=None
		
		print(f"Trigger Stat SET: {triggerStat}")
		print()
		#CHECK FOR BLOCK CHAIN ACTION HERE	
		if triggerStat is not None and loopCycleCount>droid['emaLength']:
			ladderOffest=droid['bucketOffset']
			ladder_case = determine_ladder_case(ladder_structure, ladderOffest)
			print(f"  Ladder case: {ladder_case}")
			print()

			#action = determine_required_action(triggerStat, ladder_case)
			action = determine_required_action(triggerStat, ladder_case, droid, ladder_structure)
			print(f"Attempting action: {action}")
			print()
			actionResult="null"
			if action:
				actionResult=perform_droid_action(droid, action, cursor, connection)
			
			prevAction=time.time()
		else:
			print("No Ladder Operations performed!")

		updateSession(actionResult, prevAction, triggerStatReady, triggerStat, loopCycleCount, breakerTrip, droid['id'])
		update_droid_controller_session(cursor, connection)
		loopCycleCount=loopCycleCount + 1
		connection.commit()
		time.sleep(5)  # wait 5 seconds before next cycle

# ---------- EXECUTE ---------- #
if __name__ == "__main__":
	run()
	
	
	
	
	

