import pymysql
import getV3Events

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
    sql = "SELECT poolAddress FROM LpPools WHERE id=%s"
    cc.execute(sql, (poolId,))
    return cc.fetchone()

def getPoolRecord(poolId):
    """Fetch liquidity pool details for the given poolId."""
    sql = "SELECT * FROM LpPools WHERE id=%s"
    cc.execute(sql, (poolId,))
    return cc.fetchone()

def getBotRecord(botId):
    sql = "SELECT * FROM PositionBots WHERE id=%s"
    cc.execute(sql, (botId,))
    return cc.fetchone()

def insertLpPosition(nftId, poolId):
    sql = "SELECT id FROM Assets WHERE nftNumber = %s"
    cc.execute(sql, (nftId,))
    _assetId = cc.fetchone()    
    assetId=_assetId['id']
    print("assetId: ", assetId)
    poolRecord = getPoolRecord(poolId)
    blockChain = poolRecord['blockChain']
        
    poolAddress = poolRecord['poolAddress']
    stableCoinPos = poolRecord['stableCoinPosition']

    # Insert into LpPositions table
    sql = """
        INSERT INTO LpPositions (assetId, poolAddress, nftNumber, stableCoinPosition)
        VALUES (%s, %s, %s, %s)
    """
    cc.execute(sql, (assetId, poolAddress, nftId, stableCoinPos))
    conn.commit()

    # Get new LP Position ID
    lpPositionId = cc.lastrowid
    
    '''
    # Update PositionBots table with new LpPosition ID
    sql = "UPDATE PositionBots SET lpPositionId = %s WHERE id = %s"
    cc.execute(sql, (lpPositionId, posBotId))
    conn.commit()
    '''
    
    print("New NFT inserts complete")
    return lpPositionId


def insertMainNetNftAsset(nftId, poolId):
    """Insert a new NFT record into Assets and LpPositions tables."""
    
    # Get NFT ID from blockchain
    #nftId = getV3Events.findNftId(txHash)
    
    # Check if NFT already exists in Assets table
    sql = "SELECT id FROM Assets WHERE nftNumber = %s"
    cc.execute(sql, (nftId,))
    existing_asset = cc.fetchone()
    
    if existing_asset:
        print("Asset is already set!")
        return 0

    # Get bot and pool records from DB
    #botRecord = getBotRecord(posBotId)
    #poolId = botRecord['poolId']
    poolRecord = getPoolRecord(poolId)
    blockChain = poolRecord['blockChain']

    # Set NFT address (standard for v3 pools)
    nftAddr = "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"

    # Generate asset details
    assetType = "LP_POOL"
    assetName = f"V3-NFT-{nftId}"

    # Insert into Assets table
    sql = """
        INSERT INTO Assets (name, address, blockChain, nftNumber, type)
        VALUES (%s, %s, %s, %s, %s)
    """
    cc.execute(sql, (assetName, nftAddr, blockChain, nftId, assetType))
    conn.commit()

    # Get new Asset ID
    assetId = cc.lastrowid

    print("New Asset record inserted successfully.")

    # Get pool details
    poolAddress = poolRecord['poolAddress']
    stableCoinPos = poolRecord['stableCoinPosition']

    # Insert into LpPositions table
    sql = """
        INSERT INTO LpPositions (assetId, poolAddress, nftNumber, stableCoinPosition)
        VALUES (%s, %s, %s, %s)
    """
    cc.execute(sql, (assetId, poolAddress, nftId, stableCoinPos))
    conn.commit()

    # Get new LP Position ID
    lpPositionId = cc.lastrowid
    
    '''
    # Update PositionBots table with new LpPosition ID
    sql = "UPDATE PositionBots SET lpPositionId = %s WHERE id = %s"
    cc.execute(sql, (lpPositionId, posBotId))
    conn.commit()
    '''
    
    print("New NFT inserts complete")
    return lpPositionId


def newNftInserts(txHash, posBotId):
    """Insert a new NFT record into Assets and LpPositions tables."""
    
    # Get NFT ID from blockchain
    nftId = getV3Events.findNftId(txHash)
    
    # Check if NFT already exists in Assets table
    sql = "SELECT id FROM Assets WHERE nftNumber = %s"
    cc.execute(sql, (nftId,))
    existing_asset = cc.fetchone()
    
    if existing_asset:
        print("ERROR: Asset already set!")
        return

    # Get bot and pool records from DB
    botRecord = getBotRecord(posBotId)
    poolId = botRecord['poolId']
    poolRecord = getPoolRecord(poolId)
    blockChain = poolRecord['blockChain']

    # Set NFT address (standard for v3 pools)
    nftAddr = "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"

    # Generate asset details
    assetType = "LP_POOL"
    assetName = f"V3-NFT-{nftId}"

    # Insert into Assets table
    sql = """
        INSERT INTO Assets (name, address, blockChain, nftNumber, type)
        VALUES (%s, %s, %s, %s, %s)
    """
    cc.execute(sql, (assetName, nftAddr, blockChain, nftId, assetType))
    conn.commit()

    # Get new Asset ID
    assetId = cc.lastrowid

    print("New Asset record inserted successfully.")

    # Get pool details
    poolAddress = poolRecord['poolAddress']
    stableCoinPos = poolRecord['stableCoinPosition']

    # Insert into LpPositions table
    sql = """
        INSERT INTO LpPositions (assetId, poolAddress, nftNumber, stableCoinPosition)
        VALUES (%s, %s, %s, %s)
    """
    cc.execute(sql, (assetId, poolAddress, nftId, stableCoinPos))
    conn.commit()

    # Get new LP Position ID
    lpPositionId = cc.lastrowid

    # Update PositionBots table with new LpPosition ID
    sql = "UPDATE PositionBots SET lpPositionId = %s WHERE id = %s"
    cc.execute(sql, (lpPositionId, posBotId))
    conn.commit()

    print("New NFT inserts complete")

if __name__ == "__main__":
    # Example usage
    #txHash = "0x18a0e63ec132f9aee7457a441badc6a1718c8093831692a513a97a414f801f04"
    #newNftInserts(txHash, 15)
    #print(nft_id)
    #insertMainNetNftAsset(997594, 2)
    print("test")
    
    

