import argparse  
import logging  
import time  
import uuid
import os
import requests
from dotenv import load_dotenv

#PORT = 8080
load_dotenv()
USER_API_TOKEN = os.getenv("FORDEFI_API_TOKEN")

logger = logging.getLogger(__name__)

def setup_logging() -> None:  
    handler = logging.StreamHandler()  
    handler.setFormatter(logging.Formatter("%(asctime)s:%(name)s:%(levelname)s:%(message)s"))  
    logger.setLevel(logging.INFO)  
    logger.addHandler(handler)

def getTransactionData(txId, access_token):
	transaction = requests.get(
		url=f"https://api.fordefi.com/api/v1/transactions/{txId}",headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json",},).json()
	return transaction

def monitor_transaction(  
    transaction_id: uuid.UUID,  
    polling_interval: int,  
) -> None:  
    
    print("monitor_transaction() called")
    print()
    setup_logging()

    #logger.info(f"Monitoring transaction: {transaction_id=}")
    print(f"Monitoring transaction: {transaction_id=}")

    current_state = None

    print("starting while loop")
    print()
    while True:
        print("calling 'requests...' ")
        print()
        transaction = requests.get(
            url=f"https://api.fordefi.com/api/v1/transactions/{transaction_id}",
            headers={
                "Authorization": f"Bearer {USER_API_TOKEN}",
                "Content-Type": "application/json",
            },
        ).json()
        new_state = transaction["state"]
        if new_state != current_state:
            #logger.info(f"Transaction {transaction_id=} changed state from {current_state=} to {new_state=}")
            print(f"Transaction {transaction_id=} changed state from {current_state=} to {new_state=}")
            
            current_state = new_state
            if new_state == "completed":
                break
            elif new_state == "completed_reverted":
                break    
            elif new_state == "cancelled":
                break    
        else:
            logger.debug(f"Transaction {transaction_id=} is still in state {current_state=}")
        
        logger.debug(f"Sleeping for {polling_interval=} seconds")
        time.sleep(polling_interval)
    return transaction	#['hash']

def parse_args() -> argparse.Namespace:  
    parser = argparse.ArgumentParser()  
    parser.add_argument("--transaction-id", type=uuid.UUID, required=True, help="Transaction ID to monitor")  
    parser.add_argument("--access-token", type=str, required=True, help="Access token for Fordefi API")  
    parser.add_argument("--polling-interval", type=int, default=5, help="Polling interval in seconds")  
    return parser.parse_args()

if __name__ == "__main__":  
    '''
    args = parse_args()  
    monitor_transaction(  
        access_token=args.access_token,  
        transaction_id=args.transaction_id,  
        polling_interval=args.polling_interval,  
    )
    '''
    txIdData=monitor_transaction("ffc4650a-e280-4eb5-94ea-4d32a98437d7", 5,)
    #txIdData=getTransactionData("72e2bb11-8f1e-421f-81cb-4e31d3f75b68", USER_API_TOKEN)
    for thing in txIdData:
        print(thing)
    
    print()
    print("txIdData['state']: ", txIdData['state'])
    print(txIdData['hash'])
    
    
    
    
    
    
