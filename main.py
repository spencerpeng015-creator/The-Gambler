from config import config
from kalshi_client import KalshiClient
from risk import RiskManager
from strategy import StrategyEngine
from execution import ExecutionEngine
from notifier import notify

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
    execution = ExecutionEngine(client=client, bot_mode=config.BOT_MODE)

    print("=== Starting bot ===")
    print("Mode:", config.BOT_MODE)

    balance = client.get_balance()
    positions = client.get_positions()

    equity = risk.portfolio_equity(balance)
    open_position = risk.has_open_position(positions)

    print("Balance payload:", balance)
    print("Positions payload:", positions)
    print("Computed equity:", equity)
    print("Open position exists:", open_position)

    markets = client.get_markets()
    btc_market = find_btc_market(markets, config.BTC_MARKET_TICKER_PREFIX)

    if not btc_market:
        notify("No BTC 15-minute market found.")
        print("No BTC 15-minute market found.")
        return

    ticker = btc_market["ticker"]
    print("Selected market:", ticker)

    orderbook = client.get_orderbook(ticker)
    strategy_decision = strategy.evaluate(orderbook)
    print("Strategy decision:", strategy_decision)

    proposed_trade_dollars = min(25.0, risk.max_trade_dollars(equity))

    risk_decision = risk.approve_trade(
        portfolio_equity=equity,
        proposed_trade_dollars=proposed_trade_dollars,
        has_open_position=open_position,
    )
    print("Risk decision:", risk_decision)

    if strategy_decision.action == "no_trade":
        notify(f"No trade on {ticker}: {strategy_decision.reason}")
        print("No trade: strategy veto.")
        return

    if not risk_decision.approved:
        notify(f"No trade on {ticker}: {risk_decision.reason}")
        print("No trade: risk veto.")
        return

    side = "yes" if strategy_decision.action == "buy_yes" else "no"
    entry_price = strategy_decision.best_yes_ask if side == "yes" else (1.0 - strategy_decision.best_yes_bid)

    contracts = execution.contracts_for_dollars(
        trade_dollars=risk_decision.suggested_trade_dollars,
        yes_price=entry_price,
    )

    result = execution.submit_limit_buy(
        ticker=ticker,
        side=side,
        count=contracts,
        yes_price=entry_price,
    )

    notify(f"{result.mode.upper()} result on {ticker}: {result.message}")
    print("Execution result:", result)

if __name__ == "__main__":
    main()
