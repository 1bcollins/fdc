import getMainNetPriceFromPool  # or adjust import path

def getTriggerStat(droid, cursor, LpPositionsStat, LpPoolStat, DROID_SESSION, previous_values, OWNER):
    print()
    print("🧠 Calculating Rebalance Trigger Points!")
    droid_id = droid['id']
    center_pos_bot_id = droid["centerPosBotId"]
    
    # Step 1: Get lpPositionId from PositionBots
    cursor.execute("SELECT lpPositionId FROM PositionBots WHERE id = %s", (center_pos_bot_id,))
    result = cursor.fetchone()
    if not result:
        print("centerPosBotId not found in PositionBots")
        return None
    lp_position_id = result["lpPositionId"]

    # Step 2: Get nftNumber from LpPositions
    cursor.execute("SELECT nftNumber FROM LpPositions WHERE id = %s", (lp_position_id,))
    result = cursor.fetchone()
    if not result:
        print("lpPositionId not found in LpPositions")
        return None
    nft_number = result["nftNumber"]
    
    # Helper to get low/high range
    def get_lp_range(nftNumber):
        record = next((r for r in LpPositionsStat['positions'] if r['nftNumber'] == str(nftNumber)), None)
        if record:
            return record['watchCoinPriceLow'], record['watchCoinPriceHigh']
        else:
            return None, None
    
    low_usd, high_usd = get_lp_range(nft_number)
    if low_usd is None or high_usd is None:
        print(f"Invalid range returned for nft #{nft_number}")
        print("Re-Setting LpPositions")
        print()
        setPositions(droid['poolId'], OWNER)
        return None

    def calculate_trigger(trigger_ratio):
        return (high_usd - low_usd) * float(trigger_ratio) + low_usd

    
    if(droid['fallingRebalanceTrigger']>=0):
        print("Manual trigger found!")
        fallingRebalTriggRatio=droid['fallingRebalanceTrigger']
        risingRebalTriggRatio=droid['risingRebalanceTrigger']
    
    else:
        print("Automatic Trigger found!")
        if (droid['tickBuckets'] % 2 == 0):
            risingRebalTriggRatio = .75
        else:
            risingRebalTriggRatio = .5 - (droid['tickBuckets'] - 1) / (2 * droid['tickBuckets']) + (droid['tickBuckets'] - 1) / droid['tickBuckets']
        fallingRebalTriggRatio = 1 - risingRebalTriggRatio
    
    
    
    print(f"Note calced' trigg' ratios: {fallingRebalTriggRatio} and {risingRebalTriggRatio}")
    #print("droid: ", droid)

    triggers = {
        "fallingRebalanceTrigger": calculate_trigger(fallingRebalTriggRatio),
        "risingRebalanceTrigger": calculate_trigger(risingRebalTriggRatio),
        "fallingSubsequentTrigger": 1,
        "risingSubsequentTrigger": 1
    }

    DROID_SESSION[droid['id']]['fallingRebalanceTrigger'] = triggers['fallingRebalanceTrigger']
    DROID_SESSION[droid['id']]['risingRebalanceTrigger'] = triggers['risingRebalanceTrigger']

    trigger_type = droid["triggerType"].lower()
    if trigger_type == "price":
        stableCoinPos = LpPositionsStat['lpPool']['stableCoinPosition']
        if stableCoinPos == 1:
            erc20Addr = LpPositionsStat['lpPool']['token0Address']
        else:
            erc20Addr = LpPositionsStat['lpPool']['token1Address']
        current_value1 = getMainNetPriceFromPool.get_token_price(erc20Addr)
        print("current_value1: ", current_value1)
        print()
        current_value = float(LpPoolStat['token0']['tokenDayData'][0]['priceUSD'])
    elif trigger_type == "ema":
        current_value = LpPoolStat['ema']
    else:
        print(f"Unknown trigger type: {trigger_type}")
        return None

    key = (droid_id, trigger_type)
    previous_value = previous_values.get(key)
    print("current_value: ", current_value)
    print("previous_value: ", previous_value)
    print()

    for name, trigger_usd in triggers.items():
        print(name, ": ", trigger_usd)
        if previous_value is not None:
            if "fallingRebalanceTrigger" in name and current_value < triggers['fallingRebalanceTrigger']:
                previous_values[key] = current_value
                return name
            elif "risingRebalanceTrigger" in name and current_value > triggers['risingRebalanceTrigger']:
                previous_values[key] = current_value
                return name
            elif "fallingSubsequentTrigger" in name and LpPoolStat['ema_derivative'] < 0:
                previous_values[key] = current_value
                return name
            elif "risingSubsequentTrigger" in name and LpPoolStat['ema_derivative'] > 0:
                previous_values[key] = current_value
                return name

    previous_values[key] = current_value
    return None

