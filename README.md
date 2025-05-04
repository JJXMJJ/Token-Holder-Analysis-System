# Token-Holder-Analysis-System

## File Structure

- **`token_holder_pull_and_analysis`**: Combines results for Tasks 1, 2, and 3. Saves raw and filtered token holder data as CSV files
- **`pancake_simulation`**: A class implementation for Task 4
- **`Demo.ipynb`**: A Jupyter Notebook for testing and demonstration purposes

---

## Task 1

The goal is to automate the filtering process as much as possible. Using an API with address labeling is crucial for this purpose. Below are the APIs considered:

1. **Blockchain Explorer (BSC Scan)**  
   - **Feature**: Basic source with some address labeling
   - **Disadvantage**: BSC Scan does not offer a token holder API endpoint (Etherscan does, but requires a subscription)

2. **Nansen**  
   - **Feature**: Provides detailed holder information with labeling
   - **Disadvantage**: Cannot preview specific labels without a subscription

3. **Bubblemaps**  
   - **Feature**: Visualizes token distribution and transactions, useful for cluster-based analysis. Labels some exchanges and offers a free API for graph data
   - **Disadvantage**: Data refreshes only once a week (without premium), making it unsuitable for daily monitoring

4. **Arkham**  
   - **Feature**: Known for address labeling, including exchange deposit wallets not shown on other platforms. The API includes a `type` key (e.g., `cex`, `dex`) for filtering, eliminating the need to check exchange names manually. Supports multichain in a single call
   - **Disadvantage**: The official API requires an application. The current API used in this project is a simulation of its website and only returns the top 100 holders. Exchange wallets cannot be filtered by a single condition, requiring further exploration of the API schema for future use

### Conclusion:
Arkham API was chosen for this task due to its comprehensive labeling capabilities  

**Note: The API used in this project is not official. A proper application is required for business use**

---

### Circulating Supply

The process of identifying locked wallets is manual. For the Bedrock token case, information was cross-checked using Coingecko, Cryptorank, Bubblemaps, and BSC Scan. Only one active wallet was found to have transferred out BR tokens.  
In other cases, such as Chainlink, projects may disclose treasury wallets (also visible on Arkham).

---

## Task 2

Token holder share is calculated as:  
*Non-treasury or exchange wallet balance / Circulating supply (including exchange wallets)*  

**Note**: The sum of shares does not equal 100% due to the inclusion of exchange wallets in the circulating supply.

---

## Task 3

### Detection Methods:
1. **Team/Vesting**: Refer to the Circulating Supply section for details  
2. **Market Makers**: No market makers were identified through manual checks or Arkham labels  
   - **Note**: Not too familiar with this pattern, will try to come up with a automatic way to detect given more time 
3. **Exchange Wallets**: Identified using Arkham labels

---

## Task 4: Pancake Simulation

### Functions:
1. **`get_token_data`**:  
   Retrieves token price and market cap data from the Coingecko API. By default, it fetches data for tokens on the  BSC

2. **`get_available_chains`**:  
   Fetches a list of all available blockchain networks supported by the Coingecko API. Useful for querying token data on chains other than BSC

3. **`calculate_price_impact`**:  
   Assuming here slippage means price impact, which follows the formula *x * y = k* with fee for calculation  

