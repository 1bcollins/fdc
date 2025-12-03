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

def getGasPrice(priority=3):
	'''
	PRIORITY LEVELS:
	1=HIGHEST
	2=HIGH
	3=MED (DEFAULT)
	4=LOW
	5=LOWEST
	'''
	gasRange=getGasRange()
	gasBaseWei, gasBaseGwei=getGasBase.getGasBase()
	print()
	print(f"Gas Price per BlockNative: {gasRange[priority]}")
	gasPriceGwei=gasRange[priority] if gasRange[priority]>gasBaseGwei else float(gasBaseGwei)*1.05
	
	return gasPriceGwei
	
if __name__ == "__main__":
	data=getGasRange()
	print(data)
	
