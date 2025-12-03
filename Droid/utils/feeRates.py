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
	
def getHours(assetId):
	sql = f"select timeStamp from LpValuations where assetId={assetId} order by id desc limit 1"
	cc.execute(sql)
	_t1=cc.fetchone()
	t1=_t1['timeStamp']
	
	sql = f"select timeStamp from LpValuations where assetId={assetId} and uncollected_fees_token0=0 and  uncollected_fees_token1=0 order by id desc limit 1"
	cc.execute(sql)
	_t0=cc.fetchone()
	
	if(_t0!=None):
		t0=_t0['timeStamp']	
	else:
		sql=f"select MIN(timeStamp) AS timeStamp from LpValuations where assetId={assetId} and (uncollected_fees_token0=0 or uncollected_fees_token1=0)"
		cc.execute(sql)
		_t0=cc.fetchone()
		t0=_t0['timeStamp']	
	
	timeDelta=t1-t0
	timeDeltaSecs=timeDelta.total_seconds()
	timeDeltaHours=(timeDeltaSecs/ 3600)
	return timeDeltaHours

def getCurrentFees(assetId):
	sql = f"select uncollected_fees_token0*token0_priceUSD+uncollected_fees_token1*token1_priceUSD as fees from LpValuations where assetId={assetId} order by id desc limit 1"
	cc.execute(sql)
	currFees=cc.fetchone()
	return currFees['fees']

def getFeesPerHour(nftNumber):
	#nftNumber=input(" Enter Nft Number: ")		
	try:
		assetId=getAssetId(nftNumber)
		upTimeHours=(getHours(assetId))
		currFees=(getCurrentFees(assetId))
		feeRate=float(currFees)/float(upTimeHours) if float(upTimeHours)!=0 else 0.00
		return feeRate
	except:
		print()
		print("Error getting Fee Rates!")
		return 0
	
if __name__ == "__main__":
	nftNumber=input(" Enter Nft Number: ")		
	assetId=getAssetId(nftNumber)
	print("assetId: ", assetId)
	upTimeHours=(getHours(assetId))
	print(getCurrentFees(assetId))
	print(getFeesPerHour(nftNumber))
	
	
	
	
