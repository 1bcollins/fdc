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


def update_exit_conditional(botId, minWatchCoinPercent, maxWatchCoinPercent, exitType):
	"""Update an existing record in the ExitConditionals table. Insert if not found."""
	connection = get_db_connection()
	try:
		with connection.cursor() as cursor:
			# Try to update the existing record
			update_sql = """
				UPDATE ExitConditionals
				SET minWatchCoinPercent = %s,
					maxWatchCoinPercent = %s,
					exitType = %s
				WHERE botId = %s
			"""
			cursor.execute(update_sql, (minWatchCoinPercent, maxWatchCoinPercent, exitType, botId))
			affected_rows = cursor.rowcount

			if affected_rows == 0:
				# No existing record, insert a new one
				insert_sql = """
					INSERT INTO ExitConditionals (botId, minWatchCoinPercent, maxWatchCoinPercent, exitType)
					VALUES (%s, %s, %s, %s)
				"""
				cursor.execute(insert_sql, (botId, minWatchCoinPercent, maxWatchCoinPercent, exitType))
				connection.commit()
				print(f"ExitConditional record inserted successfully for botId {botId}.")
				return 1  # Treat insert as one affected row
			else:
				connection.commit()
				print(f"ExitConditional record updated successfully for botId {botId}. Rows affected: {affected_rows}")
				return affected_rows
	finally:
		connection.close()


def update_exit_conditional_OLD(botId, minWatchCoinPercent, maxWatchCoinPercent, exitType):
	"""Update an existing record in the ExitConditionals table."""
	connection = get_db_connection()
	try:
		with connection.cursor() as cursor:
			sql = """
				UPDATE ExitConditionals
				SET minWatchCoinPercent = %s,
					maxWatchCoinPercent = %s,
					exitType = %s
				WHERE botId = %s
			"""
			cursor.execute(sql, (minWatchCoinPercent, maxWatchCoinPercent, exitType, botId))
			connection.commit()
			affected_rows = cursor.rowcount
			print(f"ExitConditional record updated successfully for botId {botId}. Rows affected: {affected_rows}")
			return affected_rows
	finally:
		connection.close()


def insert_exit_conditional(botId, minWatchCoinPercent, maxWatchCoinPercent, exitType):
	"""Insert a new record into the ExitConditionals table."""
	connection = get_db_connection()
	try:
		with connection.cursor() as cursor:
			sql = """
				INSERT INTO ExitConditionals (botId, minWatchCoinPercent, maxWatchCoinPercent, exitType)
				VALUES (%s, %s, %s, %s)
			"""
			cursor.execute(sql, (botId, minWatchCoinPercent, maxWatchCoinPercent, exitType))
			connection.commit()
			inserted_id = cursor.lastrowid
			print("New ExitConditional record inserted successfully.")
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

	# Step 2: Get exit condition details with validation
	while True:
		try:
			minWatchCoinPercent = float(input("Enter minWatchCoinPercent (0 to 1): "))
			if not (0 <= minWatchCoinPercent <= 1):
				raise ValueError("Value must be between 0 and 1.")
			break
		except ValueError as e:
			print(f"Invalid input: {e}")

	while True:
		try:
			maxWatchCoinPercent = float(input("Enter maxWatchCoinPercent (0 to 1): "))
			if not (0 <= maxWatchCoinPercent <= 1):
				raise ValueError("Value must be between 0 and 1.")
			if maxWatchCoinPercent < minWatchCoinPercent:
				raise ValueError("maxWatchCoinPercent must be greater than or equal to minWatchCoinPercent.")
			break
		except ValueError as e:
			print(f"Invalid input: {e}")
	exitType="percents"
	# Step 3: Insert record into ExitConditionals
	insert_exit_conditional(botId, minWatchCoinPercent, maxWatchCoinPercent, exitType)

if __name__ == "__main__":
	main()

