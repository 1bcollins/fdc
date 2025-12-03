import getMainNetLpPoolData
import pymysql 

#conn = pymysql.connect(db='testWtf', user='root',passwd='',host='localhost')
conn = pymysql.connect(db='helix', user='username',passwd='password',host='localhost')
cc = conn.cursor()

def addLpDataRecord(assetId, data):
	'''
	 liquidity_amount_token0 DECIMAL(18, 8) NOT NULL,
		  ->     liquidity_amount_token1 DECIMAL(18, 8) NOT NULL,
		  ->     uncollected_fees_token0 DECIMAL(18, 8) NOT NULL,
		  ->     uncollected_fees_token1 DECIMAL(18, 8) NOT NULL,
		  ->     token0_priceUSD DECIMAL(18, 8) NOT NULL,
		  ->     token1_priceUSD DECIMAL(18, 8) NOT NULL

	'''
	sql=("INSERT INTO LpValuations(assetId, liquidity_amount_token0, liquidity_amount_token1, uncollected_fees_token0, uncollected_fees_token1, token0_priceUSD, token1_priceUSD) VALUES ({}, {}, {}, {}, {}, {}, {});".format(assetId, data["liquidity_amount_token0"], data["liquidity_amount_token1"], data["uncollected_fees_token0"], data["uncollected_fees_token1"], data["token0_priceUSD"], data["token1_priceUSD"]))
	cc.execute(sql)	 #, (assetId, val,))
	conn.commit()		#will not update DB without this line???
	log_id = cc.lastrowid
	return log_id

def getMainLpPoolAssets(nftId):
	sql = (f"SELECT * FROM Assets WHERE blockChain='Ethereum' AND type='LP_POOL' AND nftNumber={nftId}") 
	cc.execute(sql)						#requires "cc" defined
	result = cc.fetchall()
	return result

def getPolyLpPoolAssets(nftId):
	sql = (f"SELECT * FROM Assets WHERE blockChain='Polygon' AND type='LP_POOL' AND nftNumber={nftId}") 
	cc.execute(sql)						#requires "cc" defined
	result = cc.fetchall()
	return result	

def getAssetRecord(blockChain, nftId):
	#print("do something to look up DB record")
	asset=getPolyLpPoolAssets(nftId) if (blockChain=="Polygon") else getMainLpPoolAssets(nftId)
	#print("asset: ", asset)
	res=asset[0] if len(asset)>0 else 0
	return res
	
	
def insertWithBotId(botId):
	print("use botId to find assetId")
	

def insertWithNftId(blockChain, nftId):
	asset=getAssetRecord(blockChain, nftId)
	if (asset!=0):
		#print("asset: ", asset)
		nftAddress = asset[2]
		assetId=asset[0]
		nftNumber=asset[4]
		dataResults = getMainNetLpPoolData.get_liquidity_and_fees(nftAddress, nftNumber)
		#print(f"price: {price}")
		#print("dataResults: ", dataResults)
		valId=addLpDataRecord(assetId, dataResults)
		#print("valId: ", valId)
	#else:
		#print("no asset found for NFT Positon")

if __name__ == "__main__":
	blockChain=input("Input blockchain (Polygon or Ethereum): ")
	nftId=int(input("Input nft id: "))
	insertWithNftId(blockChain, nftId)



		  
