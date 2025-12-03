import pymysql
from updateDroidField import update_droid_field
import requests
#from getDroidAUM import get_droid_aum
from utils import getDroidWatchCoinCost
from utils import updateLpTxsGas

conn = pymysql.connect(
	host="localhost", user="username", password="password", database="helix"
)
cursor = conn.cursor(pymysql.cursors.DictCursor)


def print_last_n_lines(file_path: str, n: int):
    """
    Print the last n lines of a file.

    :param file_path: Path to the file
    :param n: Number of lines to print from the end
    """
    try:
        with open(file_path, "r") as f:
            # Read all lines into memory (fine for small/medium files)
            lines = f.readlines()
            # Slice last n lines
            last_lines = lines[-n:]
            
            for line in last_lines:
                print(line, end="")  # avoid double newlines
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


# Example usage:
if __name__ == "__main__":
    filename = "example.txt"
    n = 5  # number of lines
    print_last_n_lines(filename, n)


#call to http://localhost:8080/run?script=GetDroidAUM&address=3
def fetch_json_from_api(url, params=None, headers=None, timeout=120):
	"""
	Fetch JSON data from a web API.

	Args:
		url (str): The full API endpoint URL.
		params (dict, optional): Query parameters to include in the request.
		headers (dict, optional): Custom headers to send with the request.
		timeout (int, optional): Timeout in seconds for the request. Default is 10.

	Returns:
		dict: Parsed JSON response from the API.
	"""
	print("calling fetch_json_from_api")
	print()
	try:
		response = requests.get(url, params=params, headers=headers, timeout=timeout)
		response.raise_for_status()  # Raise error for bad HTTP codes
		return response.json()
	except requests.exceptions.RequestException as e:
		print(f"❌ API request failed: {e}")
		return None


def updateDroidAum(droid_id):
	#updateLpTxsGas.main()
	print()
	print(f"🔄 Updating Droid AUM record {droid_id}... ")
	url=f"http://localhost:8080/run?script=GetDroidAUM&address={droid_id}"
	result=fetch_json_from_api(url)	

def calcDroidAumGain(dcWatchCoinCost, droidStatReport):
	droidAumGain=droidStatReport['totalLiquidity'] 
	coeff=dcWatchCoinCost['avgAddPrice'] if (dcWatchCoinCost['watchCoinAccumulated']<0) else dcWatchCoinCost['avgRemovedPrice']
	droidAumGain=droidAumGain+dcWatchCoinCost['watchCoinAccumulated']*coeff+dcWatchCoinCost['stableCoinAccumulated']
	droidAumGain=droidAumGain-(droidStatReport['remove_GasFeeETH']  - droidStatReport['add_GasFeeETH'])*droidStatReport['watchCoinPriceLastTx']
	droidAumGain=droidAumGain-droidStatReport['totalFeesCollectedUSD']
	return droidAumGain
	
	
def monitor_droid(droid_id):
	updateLpTxsGas.main()
	print()
	print(f"🔄 Monitoring droid {droid_id}... ")
	url=f"http://localhost:8080/run?script=GetDroidStatusReport&address={droid_id}"
	fetchResult=fetch_json_from_api(url)
	#print(result)
	print()
	for item in fetchResult:
		print(item, ": ", fetchResult[item])
	print()
	dcWatchCoinCost=getDroidWatchCoinCost.run(droid_id, stableCoinPos=1)
	
	for item in dcWatchCoinCost:
		print(item, ": ", dcWatchCoinCost[item])
	
	droidAumGain=calcDroidAumGain(dcWatchCoinCost, fetchResult)
	print()
	print("droidAumGain (totalInPositions + watchCoinAccumUSD + stableCoinAccumUSD - feesTotalUSD - gasTotalUSD): ", droidAumGain)
	
def showSettings(droid_id):
	cursor.execute(f"SELECT * FROM Droids where id={droid_id}")
	droid = cursor.fetchall()
	print()
	for setting in droid[0]:
		print(setting, ": ", droid[0][setting])

def modify_droid_field(droid_id):
	'''
		+-------------------------+--------------+------+-----+---------+----------------+
	| Field                   | Type         | Null | Key | Default | Extra          |
	+-------------------------+--------------+------+-----+---------+----------------+
	| id                      | int          | NO   | PRI | NULL    | auto_increment |
	| blockChain              | text         | NO   |     | NULL    |                |
	| active                  | tinyint(1)   | NO   |     | 1       |                |
	| poolId                  | int          | NO   |     | NULL    |                |
	| centerPosBotId          | int          | NO   |     | NULL    |                |
	| fundingUSD              | float        | NO   |     | NULL    |                |
	| spread                  | float        | NO   |     | NULL    |                |
	| fallingRebalanceTrigger | decimal(5,4) | NO   |     | NULL    |                |
	| risingRebalanceTrigger  | decimal(5,4) | NO   |     | NULL    |                |
	| triggerType             | text         | NO   |     | NULL    |                |
	| tickBuckets             | int          | YES  |     | NULL    |                |
	| bucketOffset            | int          | YES  |     | NULL    |                |
	| fundingCurveType        | varchar(50)  | NO   |     | linear  |                |
	| maxBots                 | int          | NO   |     | 2       |                |
	| accountId               | int          | YES  |     | NULL    |                |
	| maxPrice                | float        | YES  |     | NULL    |                |
	| gasBudgetLimit          | float        | YES  |     | NULL    |                |
	| minPrice                | float        | YES  |     | NULL    |                |
	| actionTimeOut           | int          | YES  |     | NULL    |                |
	| emaLength               | int          | YES  |     | NULL    |                |
	| hedgeAccount            | int          | YES  |     | NULL    |                |
	+-------------------------+--------------+------+-----+---------+----------------+

	'''
	
	ALLOWED_FIELDS = {
		"maxPrice": float,
		"minPrice": float,
		"gasBudgetLimit": float,
		"actionTimeOut": int,
		"emaLength": int,
		"fundingUSD": float,
		"triggerType": str,
		"tickBuckets": int,
		"bucketOffset": int,
		"fundingCurveType": str,
		"maxBots": int,
		"hedgeAccount": int,
		"active": int
	}
	print("\n🛠 Editable Fields:")
	for field in ALLOWED_FIELDS:
		print(f" - {field}")
	field_name = input("Field to update: ").strip()
	if field_name not in ALLOWED_FIELDS:
		print("Invalid field.")
		return
	new_value_raw = input(f"Enter new value for {field_name}: ")
	try:
		new_value = ALLOWED_FIELDS[field_name](new_value_raw)
		update_droid_field(droid_id, field_name, new_value)
	except ValueError:
		print("Invalid value type.")

def get_droid_value(droid_id): #, wallet_address):
	print()
	print("\n💰 Getting droid AUM value...")
	url=f"http://localhost:8080/run?script=GetDroidAUM&address={droid_id}"
	result=fetch_json_from_api(url)
	#print(result)
	print()
	for item in result:
		print(item, ": ", result[item])

def viewLog():
	lines=int(input("How many lines to print?: "))
	print_last_n_lines("session_updates.log", lines)

def remoteManualReset(droid_id):
	resetGo=input("Are you sure you want to reset the droid? (y/n): ")
	if (resetGo=="y"):
		update_droid_field(droid_id, "active", 2) 
		print("Message sent to Droid Controller program to reset/restart Droid!")
		print("Note: Droid will reset at 'top' of next cylce.")

def show_droid_menu(droid_id):	#, wallet_address):
	while True:
		print("\n📦 Select an operation:")
		print("1. Modify Droid Field")
		print("2. Get Current AUM")
		print("3. Droid Status Report")
		print("4. Exit to Main Menu")
		print("5. Show Droid Settings")
		print("6. View Log")
		print("7. Remote Manual Reset")
		

		choice = input("Enter option: ").strip()

		if choice == "1":
			modify_droid_field(droid_id)
		elif choice == "2":
			get_droid_value(droid_id)	#, wallet_address)
		elif choice == "3":
			monitor_droid(droid_id)
		elif choice == "4":
			break
		elif choice == "5":
			showSettings(droid_id)	
		elif choice == "6":
			viewLog()
		elif choice == "7":
			remoteManualReset(droid_id)
					
		else:
			print("Invalid selection.")

def newDroid():
	print("\n🆕 Creating a New Droid")
	print("Leave blank to use default values.\n")

	# Prompt for user-input fields
	def get_input(prompt, default, cast_type=str):
		val = input(f"{prompt} [{default}]: ").strip()
		return cast_type(val) if val else default

	poolId = get_input("Pool ID", 2, int)
	fundingUSD = get_input("Funding USD", 1000.0, float)
	triggerType = get_input("Trigger Type", "ema", str)
	tickBuckets = get_input("Tick Buckets", 4, int)
	bucketOffset = get_input("Bucket Offset", 1, int)
	maxBots = get_input("Max Bots", 3, int)
	maxPrice = get_input("Max Price", 999999.0, float)
	minPrice = get_input("Min Price", 0.0, float)
	gasBudgetLimit = get_input("Gas Budget Limit (ETH)", 0.02, float)
	actionTimeOut = get_input("Action Timeout (seconds)", 360, int)
	emaLength = get_input("EMA Length", 16, int)

	# Standard/default values
	blockChain = "Ethereum"
	active = 0
	spread = 0.0
	fallingRebalanceTrigger = 0.25
	risingRebalanceTrigger = 0.75
	fundingCurveType = "linear"
	accountId = 2
	centerPosBotId=0

	# Insert into DB
	sql = """
		INSERT INTO Droids (
			blockChain, active, poolId, centerPosBotId, fundingUSD, spread,
			fallingRebalanceTrigger, risingRebalanceTrigger, triggerType,
			tickBuckets, bucketOffset, fundingCurveType, maxBots, maxPrice,
			minPrice, gasBudgetLimit, actionTimeOut, emaLength, accountId
		) VALUES (
			%s, %s, %s, %s, %s, %s,
			%s, %s, %s,
			%s, %s, %s, %s, %s,
			%s, %s, %s, %s, %s
		)
	"""
	values = (
		blockChain, active, poolId, centerPosBotId, fundingUSD, spread,
		fallingRebalanceTrigger, risingRebalanceTrigger, triggerType,
		tickBuckets, bucketOffset, fundingCurveType, maxBots, maxPrice,
		minPrice, gasBudgetLimit, actionTimeOut, emaLength, accountId
	)

	cursor.execute(sql, values)
	conn.commit()
	new_id = cursor.lastrowid

	print(f"\n✅ New Droid added successfully with ID: {new_id}\n")
	return new_id

	
	
def main():
	'''
	conn = pymysql.connect(
		host="localhost", user="username", password="password", database="helix"
	)
	cursor = conn.cursor(pymysql.cursors.DictCursor)
	'''
	print()
	print("------------------------------------------------------------------------------------------")
	cursor.execute("SELECT id, blockChain, active, poolId FROM Droids")
	droids = cursor.fetchall()
	print("\n📋 Available Droids:")
	for d in droids:
		print(f"  ID: {d['id']} | Chain: {d['blockChain']} | Active: {bool(d['active'])}")

	droid_ids = [d['id'] for d in droids]

	while True:
		try:
			droid_id = int(input("\nEnter Droid ID to work with: "))
			if(droid_id==0):
				droid_id=newDroid()
				droid_ids.append(droid_id)
			if droid_id not in droid_ids:
				print("Invalid ID.")
				continue
			break
		except ValueError:
			
			print("Please enter a number.")

	
	
	show_droid_menu(droid_id)	#, wallet_address)

	cursor.close()
	conn.close()

if __name__ == "__main__":
	main()

