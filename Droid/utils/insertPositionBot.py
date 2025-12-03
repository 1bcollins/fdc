import pymysql

def get_connection():
	return pymysql.connect(
		host='localhost',
		user='username',
		password='password',
		database='helix',
		cursorclass=pymysql.cursors.DictCursor
	)

def get_pools():
	"""Fetch available pools from the LpPools table."""
	connection = get_connection()
	try:
		with connection.cursor() as cursor:
			cursor.execute("SELECT id, blockChain, poolAddress FROM LpPools")
			return cursor.fetchall()
	finally:
		connection.close()


def insertDroidPosBot(blockChain, poolId, lpPositionId, droidId):
	"""Insert a new record into the PositionBots table and return the inserted id."""
	connection = get_connection()
	try:
		with connection.cursor() as cursor:
			sql = """
					INSERT INTO PositionBots (blockChain, lpPositionId, active, readyTo, poolId, droidId)
					VALUES (%s, %s, 1, 'monitor', %s, %s)
			"""
			cursor.execute(sql, (blockChain, lpPositionId, poolId, droidId))
			connection.commit()
			inserted_id = cursor.lastrowid
			print(f"New PositionBot record inserted successfully with id {inserted_id}.")
			return inserted_id
	finally:
		connection.close()


def insertPloPosBot(blockChain, poolId, lpPositionId):
	"""Insert a new record into the PositionBots table and return the inserted id."""
	connection = get_connection()
	try:
		with connection.cursor() as cursor:
			sql = """
					INSERT INTO PositionBots (blockChain, lpPositionId, active, readyTo, poolId)
					VALUES (%s, %s, 1, 'monitor', %s)
			"""
			cursor.execute(sql, (blockChain, lpPositionId, poolId))
			connection.commit()
			inserted_id = cursor.lastrowid
			print(f"New PositionBot record inserted successfully with id {inserted_id}.")
			return inserted_id
	finally:
		connection.close()


def insert_position_bot(blockChain, poolId):
	"""Insert a new record into the PositionBots table."""
	connection = get_connection()
	try:
		with connection.cursor() as cursor:
			sql = """
				INSERT INTO PositionBots (blockChain, lpPositionId, active, readyTo, poolId)
				VALUES (%s, NULL, 1, 'enterPosition', %s)
			"""
			cursor.execute(sql, (blockChain, poolId))
			connection.commit()
			print("New PositionBot record inserted successfully.")
	finally:
		connection.close()

def main():
	# Step 1: Choose Blockchain
	blockchains = ["Polygon", "Ethereum"]
	print("Select a blockchain:")
	for i, bc in enumerate(blockchains, 1):
		print(f"{i}. {bc}")
	choice = int(input("Enter choice (1-2): "))
	blockChain = blockchains[choice - 1]

	# Step 2: Fetch and Choose a Pool
	pools = get_pools()
	if not pools:
		print("No pools found. Please add pools first.")
		return

	print("\nAvailable Pools:")
	for pool in pools:
		print(f"ID: {pool['id']}, Blockchain: {pool['blockChain']}, Address: {pool['poolAddress']}")

	poolId = int(input("\nEnter the pool ID to associate: "))

	# Step 3: Insert PositionBot record
	insert_position_bot(blockChain, poolId)

if __name__ == "__main__":
	main()

