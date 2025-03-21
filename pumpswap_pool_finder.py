from solders.pubkey import Pubkey  # type: ignore
from solana.rpc.api import Client
from solana.rpc.types import MemcmpOpts

# Initialize the Solana client with your Helius API key
client = Client("rpc_link_here")
pumpswap_program_id = Pubkey.from_string("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA")


def get_pool_by_token_pair(base_token: Pubkey, quote_token: Pubkey) -> str | None:
    """
    Find the pool with the highest liquidity for a specific token pair.
    
    Parameters:
        base_token (Pubkey): The base token public key.
        quote_token (Pubkey): The quote token public key.
    
    Returns:
        str | None: The pool address as a string or None if no pool is found.
    """
    base_str = str(base_token)
    quote_str = str(quote_token)

    # Build filters for pools:
    # Orientation 1: base_mint == base_token and quote_mint == quote_token
    filter1 = [
        MemcmpOpts(offset=43, bytes=base_str),  # base_mint offset
        MemcmpOpts(offset=75, bytes=quote_str),  # quote_mint offset
    ]
    # Orientation 2: base_mint == quote_token and quote_mint == base_token
    filter2 = [
        MemcmpOpts(offset=43, bytes=quote_str),
        MemcmpOpts(offset=75, bytes=base_str),
    ]

    # Fetch pools for both filter orientations
    resp1 = client.get_program_accounts(pumpswap_program_id, filters=filter1)
    resp2 = client.get_program_accounts(pumpswap_program_id, filters=filter2)
    pools = resp1.value + resp2.value

    if not pools:
        return None

    max_liquidity = 0
    best_pool_addr = None

    # Iterate over pools to find the one with maximum liquidity
    for pool in pools:
        pool_data = pool.account.data
        
        # Extract token account pubkeys from Pool struct based on IDL offsets
        base_token_account = Pubkey.from_bytes(pool_data[139:171])
        quote_token_account = Pubkey.from_bytes(pool_data[171:203])

        # Fetch token account balances
        base_resp = client.get_token_account_balance(base_token_account)
        quote_resp = client.get_token_account_balance(quote_token_account)

        if base_resp.value is None or quote_resp.value is None:
            continue  # Skip if balance fetch fails

        # Convert raw balances (u64) to integers for computation
        base_balance = int(base_resp.value.amount)
        quote_balance = int(quote_resp.value.amount)

        # Calculate liquidity as the product of the two reserves
        liquidity = base_balance * quote_balance

        if liquidity > max_liquidity:
            max_liquidity = liquidity
            best_pool_addr = str(pool.pubkey)

    return best_pool_addr


if __name__ == "__main__":
    # Example: Finding the best pool for a token pair
    token_a = Pubkey.from_string("EmrvNp9LfmgUgXM4NM9GkXDLPrhNMR3qddQP7vYzpump")  # Your token
    token_b = Pubkey.from_string("So11111111111111111111111111111111111111112")    # SOL
    
    pool_addr = get_pool_by_token_pair(token_a, token_b)

    if pool_addr:
        print(f"Best pool for {token_a} and {token_b}: {pool_addr}")
    else:
        print(f"No pools found for pair {token_a} and {token_b}")
