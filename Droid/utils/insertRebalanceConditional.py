import pymysql

# Database connection
def get_db_connection():
	return pymysql.connect(
		host='localhost',
		user='username',
		password='password',
		database='helix',
		cursorclass=pymysql.cursors.DictCursor
	)

def get_position_bots():
	"""Fetch available PositionBots from the database."""
	connection = get_db_connection()
	try:
		with connection.cursor() as cursor:
			cursor.execute("SELECT id, blockChain, poolId, active FROM PositionBots")
			return cursor.fetchall()
	finally:
		connection.close()

def insert_rebalance_conditional(botId, rebalanceType):
	"""Insert a new record into the RebalanceConditionals table."""
	connection = get_db_connection()
	try:
		with connection.cursor() as cursor:
			sql = """
				INSERT INTO RebalanceConditionals (botId, rebalanceType)
				VALUES (%s, %s)
			"""
			cursor.execute(sql, (botId, rebalanceType))
			connection.commit()
			inserted_id = cursor.lastrowid
			print("New RebalanceConditional record inserted successfully.")
			return inserted_id
	finally:
		connection.close()

def main():
	# Step 1: Fetch and choose a PositionBot
	position_bots = get_position_bots()
	if not position_bots:
		print("No PositionBots found. Please add PositionBots first.")
		return

	print("\nAvailable PositionBots:")
	for bot in position_bots:
		status = "Active" if bot['active'] else "Inactive"
		print(f"ID: {bot['id']}, Blockchain: {bot['blockChain']}, Pool ID: {bot['poolId']}, Status: {status}")

	botId = int(input("\nEnter the PositionBot ID to associate: "))

	# Step 2: Get rebalanceType with validation
	allowed_rebalance_types = ["all", "hold"]
	while True:
		rebalanceType = input("Enter rebalance type (all/hold): ").strip().lower()
		if rebalanceType in allowed_rebalance_types:
			break
		print(f"Invalid input. Choose from: {', '.join(allowed_rebalance_types)}.")

	# Step 3: Insert record into RebalanceConditionals
	insert_rebalance_conditional(botId, rebalanceType)

if __name__ == "__main__":
	main()

