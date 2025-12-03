import pymysql


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

init_db()  # Ensure DB is initialized

def getActiveBots():
	sql = f"SELECT * FROM PositionBots WHERE active=1"
	cc.execute(sql)
	return cc.fetchall()
	
def getBotRecord(botId):
	sql = f"SELECT * FROM PositionBots WHERE id={botId}"
	cc.execute(sql)
	return cc.fetchone()

def getEntrConds(botId):
	sql = f"SELECT * FROM EntranceConditionals WHERE botId={botId}"
	cc.execute(sql)
	return cc.fetchone()

def getExitConds(botId):
	sql = f"SELECT * FROM ExitConditionals WHERE botId={botId}"
	cc.execute(sql)
	return cc.fetchone()

def getRebalConds(botId):
	sql = f"SELECT * FROM RebalanceConditionals WHERE botId={botId}"
	cc.execute(sql)
	return cc.fetchone()

def getPositionRecord(lpPosId):
	sql = f"SELECT * FROM LpPositions WHERE id={lpPosId}"
	cc.execute(sql)
	return cc.fetchone()
	
def displayActiveBots():
	activeBots=getActiveBots()
	for bot in activeBots:
		print(bot)

def displayRecords(botRecords):
	#print()
	botType=translateBotTypes(botRecords)
	print("Bot Type: ", botType)
	print("Entrance Cond's: ", botRecords['entrConds'])
	print("Exit Cond's: ", botRecords['exitConds'])
	print("Rebalance Cond's: ", botRecords['rebalConds'])
	print("Position Info: ", botRecords['positionRecord'])
	print()

def getRecords(botId):
	botRecord=getBotRecord(botId)
	entrConds=getEntrConds(botId)
	exitConds=getExitConds(botId)
	rebalConds=getRebalConds(botId)
	positionRecord=getPositionRecord(botRecord['lpPositionId'])
	return {
		"entrConds": entrConds,
		"exitConds": exitConds,
		"rebalConds": rebalConds,
		"positionRecord": positionRecord
	}
	
def translateBotTypes(botRecord):
	'''
	NOTE: posBotType: 
	ploWatch="plo to recieve watch coin", 
	ploStable="plo to recieve stable coin"
	6040BotLiqu="Bot to liquidate at 60:40 ratio. and not rebalance"
	7030BotLiqu="bot to liquidate at 70:30 ratio and not rebalance"
	
	
	#insert exit conditionals
		if(posBotType=="ploWatch"): exCondId=insertExitConditional.insert_exit_conditional(botId, -1.0, 1.0, "percents")
		if(posBotType=="ploStable"): exCondId=insertExitConditional.insert_exit_conditional(botId, 0, 2, "percents")
		if(posBotType=="6040BotLiqu"): exCondId=insertExitConditional.insert_exit_conditional(botId, .40, .60, "percents")
		if(posBotType=="7030BotLiqu"): exCondId=insertExitConditional.insert_exit_conditional(botId, .30, .70, "percents")
	'''
	try:	
		#PLO_BOT_TYPES = ["ploWatch", "ploStable", "6040BotLiqu", "7030BotLiqu"]
		if (botRecord['exitConds']['exitType']=="percents" and float(botRecord['exitConds']['minWatchCoinPercent'])==float(-1.0000) and float(botRecord['exitConds']['maxWatchCoinPercent'])==float(1.0000)):
			botType=["ploWatch", "PLO to Recieve Watch Coin"]
		elif (botRecord['exitConds']['exitType']=="percents" and float(botRecord['exitConds']['minWatchCoinPercent'])==float(0.0000) and float(botRecord['exitConds']['maxWatchCoinPercent'])==float(2.0000)):
			botType=["ploStable", "PLO to Receive Stable Coin"]
		elif (botRecord['exitConds']['exitType']=="percents" and float(botRecord['exitConds']['minWatchCoinPercent'])==float(.40) and float(botRecord['exitConds']['maxWatchCoinPercent'])==float(.60)):
			botType=["6040BotLiqu", "Bot to liquidate at 60:40 ratio. And Not rebalance"]
		elif (botRecord['exitConds']['exitType']=="percents" and float(botRecord['exitConds']['minWatchCoinPercent'])==float(.30) and float(botRecord['exitConds']['maxWatchCoinPercent'])==float(.70)):
			botType=["7030BotLiqu", "Bot to liquidate at 70:30 ratio. And Not rebalance"]
		else:
			botType=["other", "Unspecified Bot Type"]
		return botType
	except:
		return "error"

if __name__ == "__main__":
	botId=int(input("Enter Bot Id number: "))
	records=getRecords(botId)
	displayRecords(records)
	
	



