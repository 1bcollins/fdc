import getLpPnLcurr
import pymysql
import sys
import json

nftNumber = int(sys.argv[1])

conn = pymysql.connect(
	host='localhost',
	user='username',
	password='password',
	database='helix',
	cursorclass=pymysql.cursors.DictCursor
)

with conn.cursor() as cursor:
	sql = "SELECT id FROM Assets WHERE nftNumber = %s"
	cursor.execute(sql, (nftNumber,))
	assetId = cursor.fetchone()

	if not assetId:
		print(json.dumps({"error": "Asset not found"}, indent=2))
		sys.exit(1)

	aId = assetId['id']

conn.close()

response = getLpPnLcurr.calculate_asset_adjusted_value(aId)
print(json.dumps(response, indent=2))

