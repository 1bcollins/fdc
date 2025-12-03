import droidController
import pymysql

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


connection = pymysql.connect(**DB_CONFIG)
cursor=connection.cursor() 
cursor.execute("SELECT * FROM Droids WHERE active = 1")
droids=cursor.fetchall()

n=-1
for droid in droids:
	n=n+1
	print(n, "- ", droids)

droidId = int(input("Droid item: "))


OWNER = "0x7BF2bd6B212Ad91A5B4686fC1e504CC708461C0e"	#LP Pool account on Python (aka: PyTradeBot)
#display wallets avail
print("Select Wallet!")
print("1: Trade Bot ('1C0e)")
print("2: Primary LP Pools ('2f67)")	#0xec92fdC275B81165317a58Ad50D5D134828c2f67
walletSelection=input("Enter Wallet item: ")
print()
if walletSelection=="1": 
	OWNER = "0x7BF2bd6B212Ad91A5B4686fC1e504CC708461C0e"
	print("'1C0e Selected")
elif walletSelection=="2": 
	OWNER = "0xec92fdC275B81165317a58Ad50D5D134828c2f67"
	print("'2f67 Selected")
else:
	print("Selectio NOT identified. Using '1C0e")
	OWNER = "0x7BF2bd6B212Ad91A5B4686fC1e504CC708461C0e"
print()



lpPoolStat=droidController.setPositions(2, OWNER)
#for pos in positions['positions']:
#	print(pos)
print(lpPoolStat['positions'][3])


target_nft = '962200'
record = next((r for r in lpPoolStat['positions'] if r['nftNumber'] == target_nft), None)

if record:
	print(record)
else:
	print("Record not found.")


#tripped=droidController.getTriggerStat(droids[droidId], cursor)
