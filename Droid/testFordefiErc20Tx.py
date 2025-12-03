import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from utils import fordefiErc20Tx

def main():
    
    #WALLET DESTINIATION:
    destination = "0x8C05D61C5Ac6BCF4f617cEff8edC64f166a9CD0D"	#Fodefi Hedge Test
    #destination = 0x2200E85214C94Eb5cB4da4F4793C7beb7c867916" 	#Fordefi Vault 6 
    #destination = "0x3651a474027496aA25F8106eF3A8D6f1486A88A6"	#Fordefi Test (original)
    
    
    custom_note = "Payment test"
    
    #TOKEN and AMOUNT:
    token_contract_address = "0xdac17f958d2ee523a2206206994597c13d831ec7"  # USDT
    #token_contract_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"	# WETH = WETH9
    value = "5000000"  # 1 USDT (6 decimals)
    #value = "38000000000000000000"	# WETH (18 decimals)
    
    #VAULT ORIGIN:
    #vault = "026ebba9-50b3-4802-8098-c36994713421"	#Fordefi Test (original)
    #vault = "9d29feaa-44dd-4184-a42f-d09e455eb488"	#Fodefi Hedge Test
    vault = "b8aff4e0-9903-40ef-92a8-d306f7fe6164" 	#Fordefi Vault 6

    #result=await fordefiErc20Tx.send_token_tx(destination, custom_note, token_contract_address, value, vault)
    result=fordefiErc20Tx.sendTokenTx(destination, custom_note, token_contract_address, value, vault)
    #result=fordefiErc20Tx.sendTokenTx("0x3651a474027496aA25F8106eF3A8D6f1486A88A6", "test", "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "24160926100946137", "9d29feaa-44dd-4184-a42f-d09e455eb488")
    
    print("result: ", result)

if __name__ == "__main__":
    main()


