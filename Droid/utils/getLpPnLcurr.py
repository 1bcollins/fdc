import pymysql
import json

def calculate_asset_adjusted_value(asset_id: int) -> dict:
	conn = pymysql.connect(
		host='localhost',
		user='username',
		password='password',
		database='helix',
		cursorclass=pymysql.cursors.DictCursor
	)

	try:
		with conn.cursor() as cursor:
			# Step 1: Get the latest zero-liquidity record's Unix timestamp
			cursor.execute("""
				SELECT UNIX_TIMESTAMP(timeStamp) AS unix_time
				FROM LpValuations
				WHERE (liquidity_amount_token0 + liquidity_amount_token1 + uncollected_fees_token0 + uncollected_fees_token1 = 0)
				  AND assetId = %s
				ORDER BY id DESC
				LIMIT 1;
			""", (asset_id,))
			row = cursor.fetchone()

			if not row or row["unix_time"] is None:
				#return {
				#	"assetId": asset_id,
				#	"status": "error",
				#	"message": "No zero-liquidity record found"
				#}
				unix_timestamp = 0

			else:
				unix_timestamp = row["unix_time"]

			# Step 2: Run the main calculation query
			cursor.execute("""
				SELECT
				  lv.assetId,
				  ROUND(
				    (lv.token0_priceUSD * lv.liquidity_amount_token0 + lv.token1_priceUSD * lv.liquidity_amount_token1)
				    - IFNULL(la.total_adds, 0)
				    + IFNULL(lr.total_removes, 0),
				    2
				  ) AS result_value
				FROM (
				  SELECT * FROM LpValuations
				  WHERE assetId = %s
				  ORDER BY timeStamp DESC
				  LIMIT 1
				) AS lv
				LEFT JOIN (
				  SELECT asset_id, SUM(amountUSD) AS total_adds
				  FROM LpAddLiquTxs
				  WHERE asset_id = %s AND timestamp > %s
				  GROUP BY asset_id
				) AS la ON la.asset_id = lv.assetId
				LEFT JOIN (
				  SELECT asset_id, SUM(amountUSD) AS total_removes
				  FROM LpRemoveLiquTxs
				  WHERE asset_id = %s AND timestamp > %s
				  GROUP BY asset_id
				) AS lr ON lr.asset_id = lv.assetId;
			""", (asset_id, asset_id, unix_timestamp, asset_id, unix_timestamp))

			result = cursor.fetchone()
			if result and result['result_value'] is not None:
				return {
					"assetId": result['assetId'],
					"adjustedValueUSD": float(result['result_value']),
					"status": "success"
				}
			else:
				return {
					"assetId": asset_id,
					"status": "error",
					"message": "No valuation data found"
				}
	finally:
		conn.close()

# Optional: test locally
if __name__ == "__main__":
	asset_id_input = int(input("Enter asset ID: "))
	response = calculate_asset_adjusted_value(asset_id_input)
	print(json.dumps(response, indent=2))

