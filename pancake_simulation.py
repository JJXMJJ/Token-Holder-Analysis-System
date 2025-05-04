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
            # Calculate token supply if market cap and price are available
            if token_address in token_data and 'usd_market_cap' in token_data[token_address] and 'usd' in token_data[token_address]:
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
        # Fetch pool data from the PancakeSwap API
        pool_data = self.get_pool_data(pool_address)
        if not pool_data:
            print("Error: Unable to fetch pool data.")
            return None

        # Extract initial reserves of the two tokens in the pool
        inital_reserve_0 = float(pool_data['tvlToken0'])  # Reserve of token0
        inital_reserve_1 = float(pool_data['tvlToken1'])  # Reserve of token1
        constant_product = inital_reserve_0 * inital_reserve_1  # Constant product for the pool (x * y = k)

        # Determine which token is being swapped and calculate the price impact
        if token_in == pool_data['token0']['id']:  # Token0 is being swapped
            token_in_symbol = pool_data['token0']['symbol']
            token_out_symbol = pool_data['token1']['symbol']
            initial_price = inital_reserve_1 / inital_reserve_0  # Price of token0 in terms of token1
            new_reserve_0 = inital_reserve_0 + amount_in * (1 - fee)  # Adjust reserve0 after swap
            new_reserve_1 = constant_product / new_reserve_0  # Adjust reserve1 to maintain constant product
            amount_out = inital_reserve_1 - new_reserve_1  # Amount of token1 received
            trade_price = amount_out / (amount_in * (1 - fee))  # Effective trade price (token1 per token0)
            price_impact = 1 - trade_price / initial_price  # Calculate price impact
        elif token_in == pool_data['token1']['id']:  # Token1 is being swapped
            token_in_symbol = pool_data['token1']['symbol']
            token_out_symbol = pool_data['token0']['symbol']
            initial_price = inital_reserve_0 / inital_reserve_1  # Price of token1 in terms of token0
            new_reserve_1 = inital_reserve_1 + amount_in * (1 - fee)  # Adjust reserve1 after swap
            new_reserve_0 = constant_product / new_reserve_1  # Adjust reserve0 to maintain constant product
            amount_out = inital_reserve_0 - new_reserve_0  # Amount of token0 received
            trade_price = amount_out / (amount_in * (1 - fee))  # Effective trade price (token0 per token1)
            price_impact = 1 - trade_price / initial_price  # Calculate price impact
        else:
            print("Error: Token address does not match pool tokens.")
            return None

        # Print detailed information about the swap
        print(f"Pool: {pool_data['token0']['symbol']}/{pool_data['token1']['symbol']}")
        print(f"Current Price: 1 {token_in_symbol} = {initial_price:.6f} {token_out_symbol}")
        print(f"TVL: ${float(pool_data['tvlUSD']):,.2f}")
        print(f"Initial Reserves: {inital_reserve_0:.6f} {pool_data['token0']['symbol']} / {inital_reserve_1:.6f} {pool_data['token1']['symbol']}")
        print(f"New Reserves After Swap: {new_reserve_0:.6f} {pool_data['token0']['symbol']} / {new_reserve_1:.6f} {pool_data['token1']['symbol']}")
        print(f"Amount In: {amount_in:.6f} {token_in_symbol}")
        print(f"Amount Out: {amount_out:.6f} {token_out_symbol}")
        print(f"Trade Price: 1 {token_in_symbol} = {trade_price:.6f} {token_out_symbol}")
        print(f"Price Impact: {price_impact * 100:.6f}%")

        return price_impact