import pymysql
from getTxFeesCollected import getV3Fees  # assuming it returns (fee0, fee1)
import os
import getErc20Balance
from dotenv import load_dotenv
import time

load_dotenv()

DB_CONFIG = {
	"host": os.getenv("DB_HOST", "localhost"),
	"user": os.getenv("DB_USER"),
	"password": os.getenv("DB_PASSWORD"),
	"database": os.getenv("DB_NAME"),
	"cursorclass": pymysql.cursors.DictCursor
}

def translateFeeData(feesWei, tokenPosition, assetId, cursor):
	print(feesWei, tokenPosition, assetId)
	print()
	
	query = """
		SELECT lp.{tokenField} AS addr
		FROM LpPositions AS p
		JOIN LpPools AS lp ON p.poolAddress = lp.poolAddress
		WHERE p.assetId = %s
	"""
	tokenField = "token0Address" if tokenPosition == 0 else "token1Address"
	cursor.execute(query.format(tokenField=tokenField), (assetId,))
	
	tokenAddr = cursor.fetchone()
	if not tokenAddr or not tokenAddr['addr']:
		print("❌ Token address not found for assetId", assetId)
		return None

	print(tokenAddr['addr'])
	print()

	fees = getErc20Balance.fixDecimals(tokenAddr['addr'], feesWei)
	return fees

	
def update_fees():
	connection = pymysql.connect(**DB_CONFIG)
	with connection:
		with connection.cursor() as cursor:
			# Step 1: Get rows with NULL fees
			cursor.execute("""
				SELECT id, tx_hash, asset_id 
				FROM LpRemoveLiquTxs 
				WHERE timestamp>1748981171 AND feesCollectedT0 IS NULL OR feesCollectedT1 IS NULL
			""")
			records = cursor.fetchall()
			
			print(f"🔎 Found {len(records)} rows needing updates.")
			
			for row in records:
				tx_hash = str(row["tx_hash"])
				tx_id = row["id"]
				#print(row)

				try:
					txFeesData = getV3Fees(tx_hash)
					print(txFeesData)
					print()
					fee0=txFeesData['fee0']
					fee1=txFeesData['fee1']
					
					#step 1.2: get Asset id
					assetId=row['asset_id']
					
					#step 1.5: Translate fee data from wei 
					fee0=translateFeeData(fee0, 0, assetId, cursor) if fee0>0 else 0
					fee1=translateFeeData(fee1, 1, assetId, cursor) if fee1>1 else 0
					
					print(f"↳ TX {tx_hash} => Fee0: {fee0}, Fee1: {fee1}")
					print()
					#test=input("pause")
					
					
					# Step 2: Update the table
					cursor.execute("""
						UPDATE LpRemoveLiquTxs
						SET feesCollectedT0 = %s, feesCollectedT1 = %s
						WHERE id = %s
					""", (fee0, fee1, tx_id))
					
					#step 3: insert delay to not overrun processor
					time.sleep(1)  # wait 5 seconds before next cycle
					
				except Exception as e:
					print(f"❌ Error on tx {tx_hash}: {e}")
					#test=input("pause")

			connection.commit()
			print("✅ Updates complete.")

if __name__ == "__main__":
	update_fees()

