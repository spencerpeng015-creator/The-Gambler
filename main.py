import time

from config import config
from kalshi_client import KalshiClient
from risk import RiskManager
from strategy import StrategyEngine
from execution import ExecutionEngine
from notifier import notify


def find_btc_market(markets_payload):
    markets = markets_payload.get("markets", [])

    candidates = []
    for market in markets:
        ticker = str(market.get("ticker", "")).upper()
        event_ticker = str(market.get("event_ticker", "")).upper()
        title = str(market.get("title", "")).upper()
        status = str(market.get("status", "")).lower()

        if "KXBTC15M" not in ticker and "KXBTC15M" not in event_ticker and "BITCOIN" not in title:
            continue

        if status not in {"active", "open", "initialized"}:
            continue

        candidates.append(market)

    if not candidates:
        return None

    active_first = sorted(
        candidates,
        key=lambda m: (
            0 if str(m.get("status", "")).lower() == "active" else 1,
            str(m.get("ticker", "")),
        ),
    )

    return active_first[0]


def run_once():
    client = KalshiClient(
        base_url=config.KALSHI_BASE_URL,
        api_key_id=config.KALSHI_API_KEY_ID,
        private_key_pem=config.KALSHI_PRIVATE_KEY,
    )

    risk = RiskManager(max_portfolio_risk_pct=config.MAX_PORTFOLIO_RISK_PCT)
    strategy = StrategyEngine()
    execution = ExecutionEngine(client=client, bot_mode=config.BOT_MODE)

    print("=== Starting bot cycle ===")
    print("Mode:", config.BOT_MODE)

    balance = client.get_balance()
    positions = client.get_positions()

    equity = risk.portfolio_equity(balance)
    open_position = risk.has_open_position(positions)

    print("Balance payload:", balance)
    print("Positions payload:", positions)
    print("Computed equity:", equity)
    print("Open position exists:", open_position)

    markets = client.get_markets(limit=500)

    print("Total markets returned:", len(markets.get("markets", [])))

    btc_candidates = []
    for m in markets.get("markets", []):
        ticker = str(m.get("ticker", "")).upper()
        event_ticker = str(m.get("event_ticker", "")).upper()
        title = str(m.get("title", "")).upper()
        if "KXBTC15M" in ticker or "KXBTC15M" in event_ticker or "BITCOIN" in title:
            btc_candidates.append({
                "ticker": m.get("ticker"),
                "title": m.get("title"),
                "event_ticker": m.get("event_ticker"),
                "status": m.get("status"),
            })

    print("BTC candidates found:", len(btc_candidates))
    for candidate in btc_candidates[:20]:
        print(candidate)

    btc_market = find_btc_market(markets)

    if not btc_market:
        notify("No BTC 15-minute market found.")
        print("No BTC 15-minute market found.")
        return

    ticker = btc_market["ticker"]
    print("Selected market:", ticker)

    orderbook = client.get_orderbook(ticker)
    print("Orderbook payload:", orderbook)

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
    entry_price = (
        strategy_decision.best_yes_ask
        if side == "yes"
        else (1.0 - strategy_decision.best_yes_bid)
    )

    contracts = execution.contracts_for_dollars(
        trade_dollars=risk_decision.suggested_trade_dollars,
        price_dollars=entry_price,
    )

    result = execution.submit_limit_buy(
        ticker=ticker,
        side=side,
        count=contracts,
        price_dollars=entry_price,
    )

    notify(f"{result.mode.upper()} result on {ticker}: {result.message}")
    print("Execution result:", result)


def main():
    while True:
        try:
            run_once()
        except Exception as e:
            print("Cycle error:", repr(e))
            notify(f"Cycle error: {repr(e)}")

        print(f"Sleeping {config.LOOP_SECONDS} seconds...")
        time.sleep(config.LOOP_SECONDS)


if __name__ == "__main__":
    main()
