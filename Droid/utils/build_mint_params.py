import time
import getErc20Balance
import os
load_dotenv()

OWNER  = os.getenv("ADDRESS")	#"0x7BF2bd6B212Ad91A5B4686fC1e504CC708461C0e"	
#OWNER = "0x7BF2bd6B212Ad91A5B4686fC1e504CC708461C0e"	

def checkForSwap(amount0_desired, amount1_desired):
	amount0_avail=getErc20Balance.get_erc20_balance_wei(LpPositionsStat['poolStatus']['token0'], OWNER)
	amount1_avail=getErc20Balance.get_erc20_balance_wei(LpPositionsStat['poolStatus']['token1'], OWNER)
	print("amount0_avail, amount0_desired: ", amount0_avail, ", ", amount0_desired)
	print("amount1_avail, amount1_desired: ", amount1_avail, ", ", amount1_desired)
	print()
	if(amount0_avail<amount0_desired): 
		print("   ⚠️  Token0 funding is LOW!")
		print()
		#amount0_desired=int(.75*amount0_avail)
		amountNeeded=amount0_desired-amount0_avail
		print("   ⚠️  Token0 funding is LOW!")
		print("amountNeeded: ", amountNeeded)
		print()		
		return amountNeeded, "token0"
	if(amount1_avail<amount1_desired): 
		amountNeeded=amount1_desired-amount1_avail
		print("   ⚠️  Token1 funding is LOW!")
		print("amountNeeded: ", amountNeeded)
		print()		
		return amountNeeded, "token1"
	return 0, "na"

def buildMintParams(poolId, tick_lower, tick_upper, liquUSD, cursor, lp_pool_stat, lp_positions_stat):
	currTick = int(lp_pool_stat['tick'])  # From injected pool status

	# Token metadata
	stable_pos = lp_positions_stat['lpPool']['stableCoinPosition']	
	token0 = lp_positions_stat['poolStatus']['token0']
	token1 = lp_positions_stat['poolStatus']['token1']

	stable_dec = int(lp_pool_stat['token0']['decimals'] if stable_pos == 0 else lp_pool_stat['token1']['decimals'])
	watch_dec = int(lp_pool_stat['token1']['decimals'] if stable_pos == 0 else lp_pool_stat['token0']['decimals'])
	watch_price = float(lp_pool_stat['token0']['tokenDayData'][0]['priceUSD']) if stable_pos == 1 else float(lp_pool_stat['token1']['tokenDayData'][0]['priceUSD'])

	# Determine allocation based on current tick
	if currTick <= tick_lower:
		stableUSD = 0
		watchUSD = liquUSD
	elif currTick >= tick_upper:
		stableUSD = liquUSD
		watchUSD = 0		
	else:
		ratio = (currTick - tick_lower) / (tick_upper - tick_lower)
		stableUSD = liquUSD * ratio
		watchUSD = liquUSD * (1 - ratio)

	# Convert to token amounts
	stable_amt = int(stableUSD * 10 ** stable_dec)
	watch_amt = int((watchUSD / watch_price) * 10 ** watch_dec)

	if stable_pos == 0:
		amount0_desired = stable_amt
		amount1_desired = watch_amt
	else:
		amount0_desired = watch_amt
		amount1_desired = stable_amt

	# Swap check
	amountNeeded, tokenNeeded = checkForSwap(amount0_desired, amount1_desired)
	if tokenNeeded != "na": 
		swapRoutine(amountNeeded, tokenNeeded)
		return "fail"

	# Final mint parameters
	mintParams = {
		"token0": token0,
		"token1": token1,
		"fee": lp_positions_stat['lpPool']['feeTier'],
		"tickLower": tick_lower,
		"tickUpper": tick_upper,
		"amount0Desired": amount0_desired,
		"amount1Desired": amount1_desired,
		"amount0Min": int(amount0_desired * 0.75),
		"amount1Min": int(amount1_desired * 0.75),
		"recipient": OWNER,
		"deadline": int(time.time()) + 300
	}

	return mintParams

