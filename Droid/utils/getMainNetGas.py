import requests
import getGasBase
import time

def getGasData():
	api_key = "a45ead8-bef3-4e95-a036-190fb3313b27"
	url = "https://api.blocknative.com/gasprices/blockprices"

	headers = {"Authorization": api_key}
	response = requests.get(url, headers=headers)

	if response.status_code == 200:
		data = response.json()
		#print(data)  # This prints the full response
	else:
		data=(f"Error: {response.status_code}, {response.text}")
	return data


def getGasRange():
	data=getGasData()
	#print(data['currentBlockNumber'])
	#print(data['blockPrices'][0]['blockNumber'])
	#print(data['blockPrices'][0]['estimatedPrices'])
	res=[]
	res.append(data['blockPrices'][0]['blockNumber'])
	for item in data['blockPrices'][0]['estimatedPrices']:
		#print(item)
		#print(item['price'])
		res.append(item['price'])
	
	return res

def getGasMultiplier(gasPriceGwei, maxGasPrice):
    if gasPriceGwei <= 0 or maxGasPrice <= 0:
        return 1.0

    # Normalize price
    x = gasPriceGwei / maxGasPrice

    # If already at or above max, do nothing
    if x >= 1.0:
        return 1.0

    # Curve steepness (higher = faster decay to 1)
    alpha = 0.85

    # Power-law scaling
    gasMult = (1 / x) ** alpha

    # Clamp result
    return min(2.0, max(1.0, gasMult))


def getGasPrice(priority=3, maxGasPrice=40):
	'''
	PRIORITY LEVELS:
	1=HIGHEST
	2=HIGH
	3=MED (DEFAULT)
	4=LOW
	5=LOWEST
	6=high priority scaled to maxGasPrice
	'''
	gasRange=getGasRange()
	gasBaseWei, gasBaseGwei=getGasBase.getGasBase()
	print()
	print(f"Gas Price per BlockNative: {gasRange[priority]}")
	
	gasMultiplier=1
	
	if priority==6:
		print("scaling gas price to maxGasPrice for max priority!")
		gasPriceGwei=gasRange[3] if gasRange[3]>gasBaseGwei else float(gasBaseGwei)*1.05
		gasMultiplier=getGasMultiplier(gasPriceGwei, maxGasPrice)
	else:
	#	gasRange=getGasRange()
	#	gasBaseWei, gasBaseGwei=getGasBase.getGasBase()
	#	print()
	#	print(f"Gas Price per BlockNative: {gasRange[priority]}")
		gasPriceGwei=gasRange[priority] if gasRange[priority]>gasBaseGwei else float(gasBaseGwei)*1.05
	
	gasPriceGwei=gasMultiplier*gasPriceGwei
	print()
	print(f"Adjusted Gas Price: {gasPriceGwei}")
	return gasPriceGwei
	
if __name__ == "__main__":
	data=getGasRange()
	print(data)
	
