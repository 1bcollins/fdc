import pymysql

def insert_droid():
	# Connect to MySQL
	db = pymysql.connect(
		host="localhost",        # Change if needed
		user="username",    # Replace with your MySQL username
		password="password",# Replace with your MySQL password
		database="helix" # Replace with your database name
	)

	cursor = db.cursor()

	# Get input from user
	print("Enter values for new Droid record:")
	blockChain = input("Blockchain (e.g., 'Polygon', 'Ethereum'): ")
	active = input("Active? (1 for True, 0 for False): ")
	poolId = int(input("Pool ID: "))
	centerPosBotId = int(input("Center Position Bot ID: "))
	fundingUSD = float(input("Funding (USD): "))
	spread = float(input("Spread (float): "))
	fallingSub = float(input("Falling Subsequent Trigger (e.g., 0.005): "))
	risingSub = float(input("Rising Subsequent Trigger (e.g., 0.005): "))
	fallingRebal = float(input("Falling Rebalance Trigger (e.g., 0.010): "))
	risingRebal = float(input("Rising Rebalance Trigger (e.g., 0.010): "))
	triggerType = input("Trigger Type (e.g., 'volume', 'price'): ")

	# Insert into table
	query = """
		INSERT INTO Droids (
			blockChain, active, poolId, centerPosBotId,
			fundingUSD, spread,
			fallingSubSequentTrigger, risingSubSequentTrigger,
			fallingRebalanceTrigger, risingRebalanceTrigger,
			triggerType
		) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
	"""

	values = (
		blockChain, int(active), poolId, centerPosBotId,
		fundingUSD, spread,
		fallingSub, risingSub,
		fallingRebal, risingRebal,
		triggerType
	)

	cursor.execute(query, values)
	db.commit()
	print(f"Droid inserted with ID: {cursor.lastrowid}")

	cursor.close()
	db.close()

if __name__ == "__main__":
	insert_droid()

