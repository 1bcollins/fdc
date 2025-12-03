import math


def price_to_valid_tick(tick_spacing: int, price: float, dec0, dec1) -> int:
	"""
	Converts a given price (token0 per token1) into the nearest valid Uniswap V3 tick.

	Args:
		  tick_spacing (int): The tick spacing of the pool.
		  price (float): The price (token0 per token1).

	Returns:
		  int: The nearest valid tick that aligns with tick_spacing.
	"""
	# Compute the raw tick value
	#tick = math.log(price/(10**dec1-dec0)) / math.log(1.0001)
	tick = math.log(price/(10**dec0-dec1)) / math.log(1.0001)
	print("tick: ", int(tick))
	# Round to the nearest valid tick based on tick spacing
	valid_tick = round(tick / tick_spacing) * tick_spacing
	#valid_tick = round(tick)	# / tick_spacing) * tick_spacing

	return int(valid_tick), int(tick)

def getBucketRange(tick, NVT, tickSpacing):
	#NOTE: NVT=Nearest Valid Tick
	print("NVT: ", NVT)
	if(NVT<=tick):
		currBucket=[NVT,tickSpacing+NVT]
	elif(NVT>tick):
		currBucket=[NVT-tickSpacing, NVT]
	else:
		print("unknown error")
	lowBucket=[currBucket[0]-tickSpacing, currBucket[0]]
	highBucket=[currBucket[1], currBucket[1]+tickSpacing]
	
	return lowBucket, currBucket, highBucket

def getPricePerTick(tick, dec0, dec1):
	priceWei=1.0001**tick
	price=priceWei*(10**(dec0-dec1))
	return (price)

def getPriceBucket(tickBucket, dec0, dec1):
	priceBucket=[0,0]
	priceBucket[0]=getPricePerTick(tickBucket[0], dec0, dec1)
	priceBucket[1]=getPricePerTick(tickBucket[1], dec0, dec1)
	
	return priceBucket

def getPloSpecs(price, dec0, dec1, tickSpacing):
	#price = float(input("Enter Price: "))
	#dec0=18
	#dec1=6
	#tickSpacing=60
	
	
	fixedPrice=price*10**dec1	#price must be in terms of tok1
	nvt, tick = price_to_valid_tick(tickSpacing, fixedPrice, dec0,dec1)	#6, 18)	#dec1,dec0  price*10**6, 18, 6)	# 18, 6)
	
	#print("nvt: ", nvt)
	#print("tick: ", tick)
	
	
	newPriceWei=1.0001**nvt
	newPrice=newPriceWei*(10**(dec0-dec1))
	#print(newPrice)
	
	lowBucket, currBucket, highBucket=getBucketRange(tick, nvt, tickSpacing)
	#print("lowBucket: ", lowBucket, ", <- 100% token1")
	#print("currBucket: ", currBucket, " <- mix token0 and token1")
	#print("highBucket: ", highBucket, ", <- 100% token0")
	
	priceBucketLow=getPriceBucket(lowBucket, dec0, dec1)
	priceBucketHigh=getPriceBucket(highBucket, dec0, dec1)
	#print("prieBucketLow: ", priceBucketLow)
	return {
		"lowBucket": lowBucket, 
		"highBucket": highBucket,
		"priceBucketLow": priceBucketLow,
		"priceBucketHigh": priceBucketHigh
	}

	
if __name__ == "__main__":
	price = float(input("Enter Price: "))
	dec0=18
	dec1=6
	tickSpacing=60
	
	r=getPloSpecs(price, dec0, dec1, tickSpacing)
	print(r)
	
	'''
	fixedPrice=price*10**dec1	#price must be in terms of tok1
	nvt, tick = price_to_valid_tick(tickSpacing, fixedPrice, dec0,dec1)	#6, 18)	#dec1,dec0  price*10**6, 18, 6)	# 18, 6)
	
	print("nvt: ", nvt)
	print("tick: ", tick)
	
	
	newPriceWei=1.0001**nvt
	newPrice=newPriceWei*(10**(dec0-dec1))
	print(newPrice)
	
	lowBucket, currBucket, highBucket=getBucketRange(tick, nvt, tickSpacing)
	print("lowBucket: ", lowBucket, ", <- 100% token1")
	print("currBucket: ", currBucket, " <- mix token0 and token1")
	print("highBucket: ", highBucket, ", <- 100% token0")
	
	priceBucketLow=getPriceBucket(lowBucket, dec0, dec1)
	print("prieBucketLow: ", priceBucketLow)
	'''
	
	
	
