import requests
import json
from getV3Events import findAnyNftId
import time
import pymysql

API_KEY = "8df1823f88d5412e5be6e618817283aa"
SUBGRAPH_ID = "5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
SUBGRAPH_URL = f"https://gateway.thegraph.com/api/{API_KEY}/subgraphs/id/{SUBGRAPH_ID}"

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'username',
    'password': 'password',
    'database': 'helix',
    'cursorclass': pymysql.cursors.DictCursor
}

'''
def get_latest_timestamp(conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT MAX(timestamp) AS latest FROM LpAddLiquTxs")
        row = cursor.fetchone()
        return int(row["latest"]) if row and row["latest"] else 0
'''

def get_latest_add_timestamp_noDroidId(conn):
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT MAX(timestamp) AS latest FROM LpAddLiquTxs")
        row = cursor.fetchone()
        return int(row["latest"]) if row and row["latest"] else 0

def get_latest_remove_add_noDroidId(conn):
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT MAX(timestamp) AS latest FROM LpAddLiquTxs")
        row = cursor.fetchone()
        return int(row["latest"]) if row and row["latest"] else 0

def get_latest_timestamp(conn, droidId):
    last=get_latest_remove_add_noDroidId(conn)
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT MAX(timestamp) AS latest FROM LpAddLiquTxs WHERE droidId={droidId}")
        row = cursor.fetchone()
        return int(row["latest"]) if row and row["latest"] else last

'''
def get_latest_timestamp(conn, droidId):
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT MAX(timestamp) AS latest FROM LpAddLiquTxs WHERE droidId={droidId}")
        row = cursor.fetchone()
        return int(row["latest"]) if row and row["latest"] else 0
'''

def insert_lp_add_liquidity_tx(conn, mints_with_nft, droidId):
    print()
    print("Calling insert_lp_add_liquidity_tx !")
    with conn.cursor() as cursor:
        for mint in mints_with_nft:
            nft_number = mint.get("tokenId")
            if nft_number is None:
                print(f"Missing tokenId for tx {mint['id']}, skipping.")
                continue

            cursor.execute("SELECT id FROM Assets WHERE nftNumber = %s", (nft_number,))
            asset = cursor.fetchone()
            if not asset:
                print(f"Asset with NFT {nft_number} not found. Skipping.")
                continue

            asset_id = asset["id"]
            tx_hash = mint["id"].split("#")[0]

            # Prevent duplicate insertions
            cursor.execute("SELECT 1 FROM LpAddLiquTxs WHERE tx_hash = %s", (tx_hash,))
            if cursor.fetchone():
                print(f"Transaction {tx_hash} already exists. Skipping.")
                continue

            sql = """
                INSERT INTO LpAddLiquTxs (amount0, amount1, amountUSD, timestamp, tx_hash, asset_id, droidId)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            #print()
            #print("mint: ", mint)
            cursor.execute(sql, (
                round(float(mint["amount0"]),6),
                round(float(mint["amount1"]),3),
                round(float(mint["amountUSD"]),2),
                int(mint["timestamp"]),
                tx_hash,
                asset_id,
                droidId
            ))

        conn.commit()

def fetch_all_mints(pool_address, origin_address, since_timestamp=0):
    mints = []
    has_more = True
    skip = 0
    page_size = 1000

    while has_more:
        where_filter = f'pool: "{pool_address}", origin: "{origin_address}"'
        if since_timestamp > 0:
            where_filter += f', timestamp_gt: {since_timestamp}'

        query = f"""
        {{
          mints(
            where: {{{where_filter}}},
            first: {page_size},
            skip: {skip},
            orderBy: timestamp,
            orderDirection: asc
          ) {{
            amount0
            amount1
            amountUSD
            id
            timestamp
          }}
        }}
        """

        response = requests.post(SUBGRAPH_URL, json={'query': query})
        data = response.json()

        new_mints = data.get("data", {}).get("mints", [])
        if not new_mints:
            break

        mints.extend(new_mints)
        skip += page_size
        time.sleep(0.2)

        if len(new_mints) < page_size:
            has_more = False

    return mints

def process_mints_with_nft_ids(mints, debug=False):
    print()
    print("Calling process_mints_with_nft_ids !")
    results = []
    for mint in mints:
        tx_hash = mint["id"].split("#")[0]
        try:
            token_id = findAnyNftId(tx_hash)
            if debug:
                print("\nToken id:", token_id)
                print("Mint data:", mint)
                input("Next item? ")
        except Exception as e:
            print(f"Error getting token ID for tx {tx_hash}: {e}")
            token_id = None
        
        enriched = {
            **mint,
            "tokenId": token_id
        }
        results.append(enriched)
    return results

#if __name__ == "__main__":
def run(POOL, WALLET, droid_id):
    #POOL = "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36"
    #WALLET = "0xec92fdc275b81165317a58ad50d5d134828c2f67"
    POOL = POOL.lower()	#"0x4e68ccd3e89f51c3074ca5072bbac773960dfa36"
    WALLET = WALLET.lower()
    
    conn = pymysql.connect(**db_config)
    try:
        latest_ts = get_latest_timestamp(conn, droid_id)
        print(f"Last synced timestamp: {latest_ts}")
        mints = fetch_all_mints(POOL, WALLET, since_timestamp=latest_ts)
        print(f"Found {len(mints)} new mint events.")
        enriched_data = process_mints_with_nft_ids(mints, debug=False)
        insert_lp_add_liquidity_tx(conn, enriched_data, droid_id)
    finally:
        conn.close()

if __name__ == "__main__":
	POOL = "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36"
	WALLET = "0xec92fdc275b81165317a58ad50d5d134828c2f67"
	droid_id=int(input("input droid ID: "))
	run(POOL, WALLET, droid_id)

