from dbFetch import get_position_bots_for_droid


def getTickRange(nftNumber, LpPositionsStat):
	for pos in LpPositionsStat['rawPositions']:
		if(int(nftNumber)==int(pos["id"])):
			tick_lower = int(pos["tickLower"]["id"].split("#")[1])
			tick_upper = int(pos["tickUpper"]["id"].split("#")[1])	
			return tick_lower, tick_upper
	return None, None

def get_ladder_structure(droid, cursor, LpPositionsStat):
    """
    Given a droid record, build the ladder structure of positions
    relative to the center position, sorted by liquidity.
    """
    print("calling get_ladder_structure")
    print("droid['centerPosBotId']: ", droid['centerPosBotId'])
    if droid['centerPosBotId'] == 0:
        print()
        print("Droid found to be new with centerPosBotId=0")
        return [0]

    tick_size = droid.get("tickBuckets", 0)
    position_bots = get_position_bots_for_droid(droid["id"], cursor)

    def get_position_data(nftNumber):
        record = next((r for r in LpPositionsStat['positions'] if r['nftNumber'] == str(nftNumber)), None)
        if record:
            return record['watchCoinPriceCenter'], record['valueUSD']
        else:
            return None, None

    positions = []
    for pb in position_bots:
        lp_position_id = pb["lpPositionId"]
        cursor.execute("SELECT nftNumber FROM LpPositions WHERE id = %s", (lp_position_id,))
        result = cursor.fetchone()
        if not result:
            continue
        nft_number = result["nftNumber"]
        price_center, liquidity = get_position_data(nft_number)
        positions.append({
            "nftNumber": nft_number,
            "price_center": price_center,
            "liquidity": liquidity,
            "bot_id": pb["id"]
        })

    center_pos_bot_id = droid["centerPosBotId"]
    cursor.execute("SELECT lpPositionId FROM PositionBots WHERE id = %s", (center_pos_bot_id,))
    result = cursor.fetchone()
    if not result:
        raise ValueError("Center Position Bot ID not found.")
    lp_position_id = result["lpPositionId"]
    cursor.execute("SELECT nftNumber FROM LpPositions WHERE id = %s", (lp_position_id,))
    result = cursor.fetchone()
    if not result:
        #raise ValueError("LpPosition ID for center not found.")
        print(" ❌ LpPosition ID for center not found.")
        return [0]
    center_nft = result["nftNumber"]
    center_price, center_liquidity = get_position_data(center_nft)

    positions = [p for p in positions if p["nftNumber"] != center_nft]
    sorted_positions = sorted(positions, key=lambda x: x["liquidity"], reverse=True)

    ladder = [0]
    centerTickLower, centerTickUpper = getTickRange(center_nft, LpPositionsStat)
    for pos in sorted_positions:
        xTickLower, xTickUpper = getTickRange(pos['nftNumber'], LpPositionsStat)
        offset_multiplier = droid.get("bucketOffset", 1)
        tickSpacing = LpPositionsStat['poolStatus']['tick_spacing']
        if xTickLower > centerTickLower:
            relative_tick = int((xTickLower - centerTickLower) / (offset_multiplier * tickSpacing))
        else:
            relative_tick = int((xTickUpper - centerTickUpper) / (offset_multiplier * tickSpacing))
        ladder.append(relative_tick)

    return ladder

