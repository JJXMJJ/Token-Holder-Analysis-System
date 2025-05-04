import requests
import pandas as pd
from typing import List, Optional


class TokenHolderAnalyzer:
    """
    A class to fetch, filter, and analyze token holder data from the Arkham API.
    """

    def __init__(self, total_supply: float, locked_supply: float, locked_addresses: List[str], token: str):
        """
        Initialize the TokenHolderAnalyzer with token supply details.

        Args:
            total_supply (float): The total supply of the token.
            locked_supply (float): The total supply locked in specific addresses.
            locked_addresses (List[str]): A list of addresses holding locked tokens.
            token (str): The token identifier (e.g., 'bedrock-token').
        """
        self.total_supply = total_supply
        self.locked_supply = locked_supply
        self.locked_addresses = locked_addresses
        self.token = token
        self.cookies = {
            '_gcl_au': '1.1.1612117149.1745482736',
            '_ga': 'GA1.1.184480857.1745482736',
            '_fbp': 'fb.1.1745482736681.312826742616629500',
            'arkham_is_authed': 'true',
            'arkham_platform_session': '12b068c4-05cf-42b7-9996-ea2a9f56d39b',
        }
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
            'x-payload': 'bbdffaa649192bd9ef8a9e02705587728c08da9af702992574494b1598a9b02e',
            'x-timestamp': '1746281179',
        }
        self.params = {'groupByEntity': 'false'}

    def fetch_token_holders(self) -> pd.DataFrame:
        """
        Fetch token holders from the Arkham API.

        Returns:
            pd.DataFrame: A DataFrame of raw token holder data.
        """
        try:
            # Fetch data from the API
            response = requests.get(
                f'https://api.arkm.com/token/holders/{self.token}',
                params=self.params,
                cookies=self.cookies,
                headers=self.headers,
            )
            response.raise_for_status()

            # Parse the response JSON and concatenate data from all keys in 'addressTopHolders'
            raw_data = response.json().get('addressTopHolders', {})
            all_data = pd.concat(
                [pd.DataFrame(raw_data[key]) for key in raw_data.keys()],
                ignore_index=True
            )
            return all_data

        except requests.exceptions.RequestException as e:
            print(f"Error fetching token holders: {e}")
            return pd.DataFrame()  # Return an empty DataFrame in case of an error

    def filter_and_analyze(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Filter token holders and analyze token distribution.

        Args:
            df (pd.DataFrame): The raw DataFrame of token holder data.

        Returns:
            Optional[pd.DataFrame]: A DataFrame with analysis results or None if the input is empty.
        """
        if df.empty:
            print("Warning: Received an empty DataFrame for analysis.")
            return None

        # Normalize the 'address' column and merge with the rest of the data
        df = pd.concat([pd.json_normalize(df['address']), df.drop('address', axis=1)], axis=1)

        output_file = f'{self.token}_100_token_holders.csv'
        df.to_csv(output_file, index=False)
        print(f"\nTop 100 token holder data saved to: {output_file}")

        # Filter out unwanted wallet types and labels
        filtered_cex_dex = df[df['arkhamEntity.type'].isin(['cex', 'dex', 'yield', 'misc'])]
        filtered_deposit = df[df['arkhamLabel.name'].str.contains('Deposit', na=False)]
        exchange_wallets = pd.concat([filtered_cex_dex, filtered_deposit], axis=0)

        print("\nFiltered Exchange Wallets:")
        print(exchange_wallets[['address', 'arkhamEntity.name', 'arkhamLabel.name']].to_string(index=False))

        # Apply filters to exclude unwanted wallet types and labels
        df = df[~df['arkhamEntity.type'].isin(['cex', 'dex', 'yield', 'misc'])]
        df = df[~df['arkhamLabel.name'].str.contains('Deposit', na=False)]

        # Exclude locked addresses and the burn address
        df = df[~df['address'].isin(self.locked_addresses)]
        df = df[df['address'] != '0x0000000000000000000000000000000000000000']

        # Calculate circulating supply
        circulating_supply = self.total_supply - self.locked_supply

        # Recalculate pctOfCap based on circulating supply
        df['pctOfCap'] = df['balance'] / circulating_supply

        # Calculate combined share (%) for top 10, 20, and 50 addresses
        top_10_pct = df.nlargest(10, 'pctOfCap')['pctOfCap'].sum()
        top_20_pct = df.nlargest(20, 'pctOfCap')['pctOfCap'].sum()
        top_50_pct = df.nlargest(50, 'pctOfCap')['pctOfCap'].sum()

        # Calculate Herfindahl-Hirschman Index (HHI)
        hhi = ((df['pctOfCap'] * 100) ** 2).sum()

        # Flag addresses holding more than 5% of the supply
        df['flagged'] = df['pctOfCap'] > 0.05

        # Display results
        print(f"\nTop 10 combined share: {top_10_pct * 100:.2f}%")
        print(f"Top 20 combined share: {top_20_pct * 100:.2f}%")
        print(f"Top 50 combined share: {top_50_pct * 100:.2f}%\n")
        print(f"Herfindahl-Hirschman Index (HHI): {hhi:.2f}\n")

        flagged_df = df[df['flagged']]
        if flagged_df.empty:
            print("No addresses hold more than 5% of the supply.")
        else:
            print("Flagged addresses (holding >5% of supply):")
            print(flagged_df[['address']].to_string(index=False))

        # Save filtered results to a CSV file
        output_file = f'{self.token}_filtered_token_holders.csv'
        df[['address', 'balance', 'pctOfCap', 'flagged']].to_csv(output_file, index=False)
        print(f"\nFiltered token holder data saved to: {output_file}")

        return df[['address', 'balance', 'pctOfCap', 'flagged']]
