import requests
from typing import Optional, Dict, List, Any

class PancakeSwapAnalyzer:
    """
    A class to analyze PancakeSwap pools and calculate price impacts for token swaps.
    """

    def __init__(self, coingecko_api_key: str):
        """
        Initialize the PancakeSwapAnalyzer with a Coingecko API key.

        Args:
            coingecko_api_key (str): API key for Coingecko.
        """
        self.coingecko_api_key = coingecko_api_key

    def get_pool_data(self, pool_address: str) -> Optional[Dict[str, Any]]:
        """
        Fetch pool data from the PancakeSwap Explorer API.

        Args:
            pool_address (str): The address of the pool.

        Returns:
            Optional[Dict[str, Any]]: Pool data as a dictionary, or None if an error occurs.
        """
        url = f"https://explorer.pancakeswap.com/api/cached/pools/v3/bsc/{pool_address}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching pool data: {e}")
            return None
        
    def get_available_chains(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch all available chains for the `get_token_data` function from the Coingecko API.

        Returns:
            Optional[List[Dict[str, Any]]]: A list of available chains as dictionaries, or None if an error occurs.
        """
        url = "https://api.coingecko.com/api/v3/asset_platforms"
        headers = {
            "accept": "application/json",
            "x-cg-api-key": self.coingecko_api_key
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching available chains: {e}")
            return None

    def get_token_data(self, token_address: str, chain: str = 'binance-smart-chain') -> Optional[Dict[str, Any]]:
        """
        Fetch token price and market cap from the Coingecko API.

        Args:
            token_address (str): The address of the token.
            chain (str): The blockchain network (default is 'binance-smart-chain').

        Returns:
            Optional[Dict[str, Any]]: Token data as a dictionary, or None if an error occurs.
        """
        url = f"https://api.coingecko.com/api/v3/simple/token_price/{chain}?contract_addresses={token_address}&vs_currencies=usd&include_market_cap=true"
        headers = {
            "accept": "application/json",
            "x-cg-api-key": self.coingecko_api_key
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            token_data = response.json()
            token_data[token_address]['supply'] = token_data[token_address]['usd_market_cap'] / token_data[token_address]['usd']
            return token_data[token_address]
        except requests.exceptions.RequestException as e:
            print(f"Error fetching token data: {e}")
            return None

    def calculate_price_impact(self, pool_address: str, token_in: str, amount_in: float, fee: float) -> Optional[float]:
        """
        Calculate the price impact for a swap in a PancakeSwap V3 pool.

        Args:
            pool_address (str): Pool smart contract address.
            token_in (str): Token smart contract address.
            amount_in (float): Amount of the token to swap.
            fee (float): Fee percentage (e.g., 0.003 for 0.3%).

        Returns:
            Optional[float]: The price impact as a percentage, or None if an error occurs.
        """
        pool_data = self.get_pool_data(pool_address)
        if not pool_data:
            return None

        inital_reserve_0 = float(pool_data['tvlToken0'])
        inital_reserve_1 = float(pool_data['tvlToken1'])
        constant_product = inital_reserve_0 * inital_reserve_1

        # Determine token in/out and adjust amounts accordingly
        if token_in == pool_data['token0']['id']:  # Token0 is being swapped
            token_in_symbol = pool_data['token1']['symbol']
            initial_price = inital_reserve_0 / inital_reserve_1  # Token1 per Token0
            new_reserve_0 = inital_reserve_0 + amount_in * (1 - fee)
            new_reserve_1 = constant_product / new_reserve_0
            amount_out = inital_reserve_1 - new_reserve_1
            trade_price = (amount_in * (1 - fee)) / amount_out
            price_impact = 1 - initial_price / trade_price
        elif token_in == pool_data['token1']['id']:  # Token1 is being swapped
            token_in_symbol = pool_data['token1']['symbol']
            initial_price = inital_reserve_1 / inital_reserve_0  # Token0 per Token1
            new_reserve_1 = inital_reserve_1 + amount_in * (1 - fee)
            new_reserve_0 = constant_product / new_reserve_1
            amount_out = inital_reserve_0 - new_reserve_0
            trade_price = (amount_in * (1 - fee)) / amount_out
            price_impact = 1 - initial_price / trade_price
        else:
            print('Please check pool and token addresses')
            return None

        print(f"Pool: {pool_data['token0']['symbol']}/{pool_data['token1']['symbol']}")
        print(f"Current Price: 1 {pool_data['token0']['symbol']} = {pool_data['token0Price']} {pool_data['token1']['symbol']}")
        print(f"TVL: ${float(pool_data['tvlUSD']):,.2f}")
        print(f"\nPrice impact for swapping {amount_in} {token_in_symbol}: {price_impact * 100:.6f}%")

        return price_impact