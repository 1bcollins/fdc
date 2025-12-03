def submit_quote(quote_id: str, vault_id: str, chain_type: str, network: str, sell_token_amount: str, buy_token_address: str, providers: list, slippage: str, sell_token_address: str) -> dict:
	submit_response = {
		"quote_id": quote_id,
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
			"type": chain_type,
			"details": {
				"type": "erc20",
				"token": {
					"chain": network,
					"hex_repr": buy_token_address
				}
			}
		},
		"amount": sell_token_amount,
		"slippage_bps": slippage,
		"fee": {
			"type": "evm",
			"details": {
				"gas_limit": "21000",
				"type": "priority",
				"priority_level": "medium"
			}
		},
		"signer_type": "api_signer"
	}

	return submit_response

