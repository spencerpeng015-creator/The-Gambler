from config import config
from kalshi_client import KalshiClient

def find_btc_market(markets_payload, prefix):
    markets = markets_payload.get("markets", [])
    for market in markets:
        ticker = market.get("ticker", "")
        if ticker.startswith(prefix):
            return market
    return None

def main():
    client = KalshiClient(
        base_url=config.KALSHI_BASE_URL,
        api_key_id=config.KALSHI_API_KEY_ID,
        private_key_pem=config.KALSHI_PRIVATE_KEY,
    )

    print("Bot mode:", config.BOT_MODE)
    print("Fetching balance...")
    balance = client.get_balance()
    print(balance)

    print("Fetching markets...")
    markets = client.get_markets()
    btc_market = find_btc_market(markets, config.BTC_MARKET_TICKER_PREFIX)

    if not btc_market:
        print("No BTC 15m market found.")
        return

    ticker = btc_market["ticker"]
    print("Selected market:", ticker)

    print("Fetching orderbook...")
    orderbook = client.get_orderbook(ticker)
    print(orderbook)

    print("Dry run complete. No orders placed.")

if __name__ == "__main__":
    main()
