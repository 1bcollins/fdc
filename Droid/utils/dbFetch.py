from typing import List

# ---------- DB FETCH FUNCTIONS ---------- #

def getEvmAddress(accountId, cursor):
	cursor.execute(f"SELECT address FROM Accounts WHERE id = {accountId}")
	return cursor.fetchone()

def get_active_droids(cursor) -> List[dict]:
	cursor.execute("SELECT * FROM Droids WHERE active = 1")
	return cursor.fetchall()

def getDroid(DROID_ID, cursor):
	cursor.execute(f"SELECT * FROM Droids WHERE id = {DROID_ID}")
	return cursor.fetchone()

def getPoolId(DROID_ID, cursor):
	cursor.execute(f"SELECT poolId FROM Droids WHERE id = {DROID_ID}")
	record = cursor.fetchone()
	return record['poolId']

def getLpPosId(botId, cursor):
	cursor.execute("SELECT lpPositionId FROM PositionBots WHERE id= %s", (botId,))
	botRecord = cursor.fetchone()
	return botRecord['lpPositionId']

def getUnusedBotId(cursor):
	cursor.execute("SELECT id FROM PositionBots WHERE droidId=0 AND lpPositionId = 0 AND blockChain='Ethereum'")
	botRecord = cursor.fetchone()
	if not botRecord:
		return 0
	return botRecord['id']	

def getBotId(droidId, posId, cursor):
	cursor.execute("SELECT id FROM PositionBots WHERE droidId= %s AND lpPositionId = %s", (droidId, posId,))
	botRecord = cursor.fetchone()
	if not botRecord:
		return 0
	return botRecord['id']

def getPoolAddress(poolId, cursor):
	cursor.execute(f"SELECT poolAddress FROM LpPools WHERE id = {poolId}")
	record = cursor.fetchone()
	return record['poolAddress']

def getLpPoolRecord(poolId, cursor):
	cursor.execute("SELECT * FROM LpPools WHERE id = %s", (poolId,))
	return cursor.fetchone()

def getLpPositionRecord(nftNumber, cursor):
	cursor.execute("SELECT * FROM LpPositions WHERE nftNumber = %s", (nftNumber,))
	return cursor.fetchone()

def get_position_bots_for_droid(droid_id, cursor):
	cursor.execute("SELECT * FROM PositionBots WHERE droidId = %s", (droid_id,))
	return cursor.fetchall()

def getDuplicateBots(_duplicate, droidId, cursor):
	duplicate = int(_duplicate)
	print(f"geting list of bots for duplicate {duplicate}\n")
	query = f"SELECT id from PositionBots where lpPositionId={duplicate} AND droidId={droidId}"
	cursor.execute(query)
	return cursor.fetchall()

def getNftNumber(droid, cursor):
	center_pos_bot_id = droid["centerPosBotId"]
	cursor.execute("SELECT lpPositionId FROM PositionBots WHERE id = %s", (center_pos_bot_id,))
	result = cursor.fetchone()
	if not result:
		print("centerPosBotId not found in PositionBots")
		return None
	lp_position_id = result["lpPositionId"]

	cursor.execute("SELECT nftNumber FROM LpPositions WHERE id = %s", (lp_position_id,))
	result = cursor.fetchone()
	if not result:
		print("lpPositionId not found in LpPositions")
		return None
	return result["nftNumber"]

