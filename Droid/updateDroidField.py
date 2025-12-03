import pymysql

# Config — replace with your actual credentials
DB_CONFIG = {
	"host": "localhost",
	"user": "username",
	"password": "password",
	"database": "helix"
}

# Define allowed fields to prevent SQL injection
ALLOWED_FIELDS = {
	"maxPrice",
	"minPrice",
	"gasBudgetLimit",
	"actionTimeOut",
	"emaLength",
	"fundingUSD",
	"triggerType",
	"tickBuckets",
	"bucketOffset",
	"fundingCurveType",
	"maxBots",
	"hedgeAccount",
	"active",
	"fallingRebalanceTrigger",
	"risingRebalanceTrigger"
}

def update_droid_field(droid_id: int, field_name: str, new_value):
	"""Update a specific field for a given droid by ID."""
	if field_name not in ALLOWED_FIELDS:
		raise ValueError(f"❌ Invalid field: '{field_name}' is not updatable.")

	# Open database connection
	conn = pymysql.connect(**DB_CONFIG)
	cursor = conn.cursor()

	# Prepare and execute query
	sql = f"UPDATE Droids SET {field_name} = %s WHERE id = %s"
	try:
		cursor.execute(sql, (new_value, droid_id))
		conn.commit()
		print(f"✅ Updated droid ID {droid_id}: {field_name} = {new_value}")
	except Exception as e:
		conn.rollback()
		print(f"❌ Error updating field: {e}")
	finally:
		cursor.close()
		conn.close()

# Optional CLI entry point
if __name__ == "__main__":
	import sys
	if len(sys.argv) != 4:
		print("Usage: python updateDroidField.py <droidId> <field> <value>")
	else:
		droid_id = int(sys.argv[1])
		field = sys.argv[2]
		value = sys.argv[3]

		# Try to cast numeric values
		if value.replace('.', '', 1).isdigit():
			value = float(value) if '.' in value else int(value)

		update_droid_field(droid_id, field, value)

