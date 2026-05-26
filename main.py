from config import config
from kalshi_client import KalshiClient
from risk import RiskManager
from strategy import StrategyEngine

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
    risk = RiskManager(max_portfolio_risk_pct=config.MAX_PORTFOLIO_RISK_PCT)
    strategy = StrategyEngine()

    print("Bot mode:", config.BOT_MODE)

    balance = client.get_balance()
    equity = risk.portfolio_equity(balance)
    print("Equity:", equity)

    markets = client.get_markets()
    btc_market = find_btc_market(markets, config.BTC_MARKET_TICKER_PREFIX)

    if not btc_market:
        print("No BTC 15m market found.")
        return

    ticker = btc_market["ticker"]
    print("Selected market:", ticker)

    orderbook = client.get_orderbook(ticker)
    decision = strategy.evaluate(orderbook)

    print("Strategy decision:", decision)

    proposed_trade_dollars = min(25.0, risk.max_trade_dollars(equity))
    risk_decision = risk.approve_trade(
        portfolio_equity=equity,
        proposed_trade_dollars=proposed_trade_dollars,
        has_open_position=False,
    )

    print("Risk decision:", risk_decision)

    if decision.action != "no_trade" and risk_decision.approved:
        print(f"DRY RUN: would {decision.action} for ${risk_decision.suggested_trade_dollars:.2f}")
    else:
        print("No trade placed.")

if __name__ == "__main__":
    main()
