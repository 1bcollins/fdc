# fordefi_api.py
#import os
import requests
#from dotenv import load_dotenv

# Load JWT token from .env file (recommended) 
# .env should contain: FORDEFI_JWT=your_token_here
#load_dotenv()
FORDEFI_BASE_URL = "https://api.fordefi.com/api/v1"
FORDEFI_JWT = "eyJhbGciOiJFZERTQSIsImtpZCI6ImZ3MFc3aVpocUc0SUEzaXV4ZmhQIiwidHlwIjoiSldUIn0.eyJpc3MiOiJodHRwczovL2FwaS5mb3JkZWZpLmNvbS8iLCJzdWIiOiI0NTI1NjY0ZS01NjI2LTQ1YTktYTVjMi1jMDRhY2ZlNjM1ZDFAZm9yZGVmaSIsImF1ZCI6WyJodHRwczovL2FwaS5mb3JkZWZpLmNvbS9hcGkvIl0sImV4cCI6MjA2OTg0Nzc2MiwiaWF0IjoxNzU0NDg3NzYyLCJqdGkiOiJlMGFjOGRjYi02YzA2LTQ5ZmItOTRjNy0zNmM0MjkyNWQxYmYifQ.8RENZzODRNNC2PKBqLro6Q3qx5h0hese3JaUOSrxs-3Cs1Gc4eGK6g7U_KJR6zUSr2yXb98Cqj-flXfTtUMPCQ"	#os.getenv("FORDEFI_JWT")

if not FORDEFI_JWT:
    raise ValueError("Missing FORDEFI_JWT. Please set it in your environment or .env file.")

HEADERS = {
    "Authorization": f"Bearer {FORDEFI_JWT}",
    "Content-Type": "application/json"
}


def get_fordefi(endpoint: str) -> dict:
    """
    Generic function to perform a GET request to Fordefi API.
    
    Args:
        endpoint (str): API endpoint (e.g., 'vaults/<id>' or 'transactions')
    
    Returns:
        dict: Parsed JSON response
    """
    url = f"{FORDEFI_BASE_URL}/{endpoint}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()  # Raise error for bad HTTP codes
    return response.json()


# Example convenience wrapper
def get_vault(vault_id: str) -> dict:
    """Fetch a single vault by ID."""
    return get_fordefi(f"vaults/{vault_id}")

def getVaultId(evmAddress):
	vaults=get_fordefi("vaults")
	for vault in vaults['vaults']:
		if vault['address'].lower()==evmAddress.lower(): return vault['id']
	
	return "error"

if __name__ == "__main__":
    # Example usage (replace with a real vault ID)
    vault_id = "026ebba9-50b3-4802-8098-c36994713421"
    vault_info = get_vault(vault_id)
    print(vault_info)
    print()
    print(vault_info['address'])
    

