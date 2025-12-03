import requests

def get_pool_data(pool_address: str):
    API_KEY = "8df1823f88d5412e5be6e618817283aa" 
    SUBGRAPH_ID="5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
    subgraph_url = f"https://gateway.thegraph.com/api/{API_KEY}/subgraphs/id/{SUBGRAPH_ID}"
    query = {
        "query": f"""
        {{
            pools(where: {{id: "{pool_address.lower()}"}}) {{
                id
                token0 {{ symbol }}
                token1 {{ symbol }}
                feeTier
            }}
        }}
        """
    }
    
    response = requests.post(subgraph_url, json=query)
    
    if response.status_code == 200:
        data = response.json()
        pools = data.get("data", {}).get("pools", [])
        return pools[0] if pools else None
    else:
        raise Exception(f"Query failed with status code {response.status_code}: {response.text}")

# Example usage
if __name__ == "__main__":
    SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
    POOL_ADDRESS = "0x9b08288c3be4f62bbf8d1c20ac9c5e6f9467d8b7"
    
    try:
        pool_data = get_pool_data(POOL_ADDRESS)
        print(pool_data)
    except Exception as e:
        print(f"Error: {e}")

