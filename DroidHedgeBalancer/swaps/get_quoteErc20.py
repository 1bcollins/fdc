import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import os
import get_provider_list

load_dotenv()

FORDEFI_API_TOKEN = os.getenv("FORDEFI_API_TOKEN")
EVM_VAULT_ID = os.getenv("EVM_VAULT_ID")

def remove_uniswap_x(providers):
    """
    Remove 'uniswap_x' from the providers list if present.
    
    Args:
        providers (list): List of provider names.
    
    Returns:
        list: New list without 'uniswap_x'.
    """
    return [p for p in providers if p != "uniswap_x"]


# Example usage:
#providers = ['cow_swap', 'uniswap_x', 'one_inch_fusion']
#filtered = remove_uniswap_x(providers)
#print(filtered)  # ['cow_swap', 'one_inch_fusion']



def get_best_quote(quotes_response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if "providers_with_quote" not in quotes_response:
        return None
    
    valid_quotes = []
    
    for provider in quotes_response["providers_with_quote"]:
        if provider.get("quote") is not None and provider.get("api_error") is None:
            valid_quotes.append(provider)
            provider_id = provider['provider_info']['provider_id']
            print(f"✅ {provider_id}: {provider['quote']['output_amount']} tokens")
        else:
            error_msg = provider.get("api_error", {}).get("description", "Unknown error")
            provider_id = provider['provider_info']['provider_id']
            print(f"❌ {provider_id}: {error_msg}")
    
    if not valid_quotes:
        print("No valid quotes found from any provider")
        return None
    
    best_quote = max(valid_quotes, key=lambda x: int(x["quote"]["output_amount"]))
    
    provider_id = best_quote['provider_info']['provider_id']
    print(f"🏆 Best quote from {provider_id}: {best_quote['quote']['output_amount']} tokens")
    
    # Return both quote and provider info
    return {
        **best_quote["quote"],
        "provider_info": best_quote["provider_info"]
    }

def get_quote(vault_id: str, chain_type: str, network: str,  sell_token_amount: str, buy_token_address: str, providers: list, slippage: str, access_token: str, sell_token_address: str) -> Dict[str, Any]:
    print(f"Getting quote from: {providers}")
    
    quote_data = {
      "vault_id": vault_id,
      "input_asset_identifier": {
        "type": "evm",
        "details": {
          "type": "erc20",
          "token": {
              "chain": "evm_ethereum_mainnet",
              "hex_repr": sell_token_address
          }
        }
      },
      "output_asset_identifier": {
        "type": "evm",
        "details": {
          "type": "erc20",
          "token": {
              "chain": "evm_ethereum_mainnet",
              "hex_repr": buy_token_address
          }
        }
      },
      "amount": sell_token_amount,
      "slippage_bps": slippage,
      "signer_type": "api_signer",
      "requested_provider_ids": providers
    }
    
    
    print("quote_data:")
    print(quote_data)
    print()


    try:
        quote = requests.post(
          "https://api.fordefi.com/api/v1/swaps/quotes",
          headers={
              "Authorization": f"Bearer {access_token}",
          },
          json=quote_data
        )

        #print("Request headers: ", quote.headers)
        if quote.status_code >= 400:
            try:
                error_response = quote.json()
                return {"error": True, "details": error_response}
            except ValueError:
                return {"error": True, "details": {"message": quote.text}}
        
        return quote.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error making quote request: {e}")
        raise
    except ValueError as e:
        print(f"Error parsing JSON response: {e}")
        raise

if __name__ == "__main__":
	
	providers=get_provider_list.getSwapProviders("evm", FORDEFI_API_TOKEN)
	buy_token_address="0xdAC17F958D2ee523a2206206994597C13D831ec7" #USDT
	sell_token_address="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"	#WETH
	sell_token_amount="10000000000000000"	# 10000000000000000 =.01 eth =~$40
	slippage="100"	#0000000000000"
	print("providers: ", providers)
	print("providers[1]: ", providers[1])
	filtered = remove_uniswap_x(providers)
	quotes=get_quote(EVM_VAULT_ID, "evm", "ethereum_mainnet",  sell_token_amount, buy_token_address, filtered, slippage, FORDEFI_API_TOKEN, sell_token_address)
	
	print("quotes: ", quotes)
	print()
	for q in quotes['providers_with_quote']:
		print(q['quote'])
		if (q['quote']): print("quote ID: ", q['quote']['quote_id'])	#<-isolated quote ID
		print()
	
	
	

