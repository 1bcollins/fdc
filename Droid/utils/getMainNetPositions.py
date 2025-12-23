import requests

API_KEY = "8df1823f88d5412e5be6e618817283aa"  # TODO change to .env var
SUBGRAPH_ID = "5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"	#TODO change to dynamic with pool changes
# Function to query pool status


# Function to query all positions for a given pool and owner with batching
def query_subgraph(pool_id, owner, batch_size=1000):
    api_url = f"https://gateway.thegraph.com/api/{API_KEY}/subgraphs/id/{SUBGRAPH_ID}"
    all_positions = []
    skip = 0

    while True:
        query = f"""
        {{
            positions(
                first: {batch_size},
                skip: {skip},
                where: {{pool_: {{id: "{pool_id.lower()}"}}, owner: "{owner.lower()}"}}
            ) {{
                id
                owner
                tickLower {{
                    id
                }}
                tickUpper {{
                    id
                }}
                liquidity
            }}
        }}
        """

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(api_url, json={"query": query}, headers=headers)

        if response.status_code != 200:
            response.raise_for_status()

        data = response.json()
        positions = data["data"]["positions"]

        if not positions:
            break  # No more results to fetch

        all_positions.extend(positions)
        skip += batch_size

    return all_positions


def query_pool_status(pool_id):#, api_key):
    api_url = f"https://gateway.thegraph.com/api/{API_KEY}/subgraphs/id/{SUBGRAPH_ID}"
    
    query = f"""
    {{
       pools(where: {{id: "{pool_id.lower()}"}}) {{
           id
           totalValueLockedUSD
           liquidity
           token0Price
           token1Price
           volumeUSD
           tick
           sqrtPrice
           token0 {{
               decimals
               tokenDayData(first: 1, orderBy: id, orderDirection: desc) {{
                   priceUSD
               }}
           }}
           token1 {{
               decimals
               tokenDayData(first: 1, orderBy: id, orderDirection: desc) {{
                   priceUSD
               }}               
           }}
       }}
    }}
    """
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(api_url, json={"query": query}, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

# Function to query positions for a pool and owner
def query_subgraphOLD(pool_id, owner):#, api_key):
    api_url = f"https://gateway.thegraph.com/api/{API_KEY}/subgraphs/id/{SUBGRAPH_ID}"
    
    query = f"""
    {{
        positions(
            where: {{pool_: {{id: "{pool_id.lower()}"}}, owner: "{owner.lower()}"}}
        ) {{
            id
            owner
            tickLower {{
                id
            }}
            tickUpper {{
                id
            }}
            liquidity
        }}
    }}
    """
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(api_url, json={"query": query}, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def getPosition(posId):
    api_url = f"https://gateway.thegraph.com/api/{API_KEY}/subgraphs/id/{SUBGRAPH_ID}"
    
    query = f"""
    {{
        positions(
            where: {{id: "{posId}"}}
        ) {{
            id
            owner
            tickLower {{
                id
            }}
            tickUpper {{
                id
            }}
            liquidity
        }}
    }}
    """
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(api_url, json={"query": query}, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()



# Example usage
if __name__ == "__main__":
    #API_KEY = "8df1823f88d5412e5be6e618817283aa"  # Replace with your actual API key
    POOL_ID = "0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36"	#"0x9b08288c3be4f62bbf8d1c20ac9c5e6f9467d8b7"
    #OWNER = "0x7BF2bd6B212Ad91A5B4686fC1e504CC708461C0e"
    OWNER = "0xec92fdC275B81165317a58Ad50D5D134828c2f67"

    try:
        # Query pool status
        pool_status = query_pool_status(POOL_ID)#, API_KEY)
        print("Pool Status:")
        print(pool_status['data']['pools'])

        # Query subgraph for owner positions
        owner_positions = query_subgraph(POOL_ID, OWNER)#, API_KEY)
        print("\nOwner Positions:")
        print(owner_positions)	#['data']['positions'])
        print(len(owner_positions))
    except Exception as e:
        print(f"Error: {e}")

