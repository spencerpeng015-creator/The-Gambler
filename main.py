import time

from config import config
from kalshi_client import KalshiClient
from risk import RiskManager
from strategy import StrategyEngine
from execution import ExecutionEngine
from notifier import notify


def choose_active_market(markets_payload):
    markets = markets_payload.get("markets", [])

    candidates = []
    for market in markets:
        status = str(market.get("status", "")).lower()
        ticker = str(market.get("ticker", "")).upper()

        if status not in {"active", "open", "initialized"}:
            continue

        if not ticker.startswith(config.BTC_SERIES_TICKER):
            continue

        candidates.append(market)

    if not candidates:
        return None

    candidates = sorted(
        candidates,
        key=lambda m: (
            0 if str(m.get("status", "")).lower() == "active" else 1,
            str(m.get("ticker", "")),
        ),
    )
    return candidates[0]


def run_once():
    client = KalshiClient(
        base_url=config.KALSHI_BASE_URL,
        api_key_id=config.KALSHI_API_KEY_ID,
        private_key_pem=config.KALSHI_PRIVATE_KEY,
    )

    risk = RiskManager(max_portfolio_risk_pct=config.MAX_PORTFOLIO_RISK_PCT)
    strategy = StrategyEngine()
    execution = ExecutionEngine(client=client, bot_mode=config.BOT_MODE)

    print("=== Starting bot cycle ===", flush=True)
    print("Mode:", config.BOT_MODE, flush=True)

    balance = client.get_balance()
    positions = client.get_positions()

    equity = risk.portfolio_equity(balance)
    open_position = risk.has_open_position(positions)

    print("Balance payload:", balance, flush=True)
    print("Positions payload:", positions, flush=True)
    print("Computed equity:", equity, flush=True)
    print("Open position exists:", open_position, flush=True)

    markets = client.get_markets(
        limit=200,
        status="open",
        series_ticker=config.BTC_SERIES_TICKER,
    )

    print("Series ticker used:", config.BTC_SERIES_TICKER, flush=True)
    print("Markets returned for series:", len(markets.get("markets", [])), flush=True)

    for m in markets.get("markets", [])[:20]:
        print(
            {
                "ticker": m.get("ticker"),
                "title": m.get("title"),
                "event_ticker": m.get("event_ticker"),
                "status": m.get("status"),
            },
            flush=True,
        )

    btc_market = choose_active_market(markets)

    if not btc_market:
        notify("No open BTC 15-minute market found for the series.")
        print("No open BTC 15-minute market found for the series.", flush=True)
        return

    ticker = btc_market["ticker"]
    print("Selected market:", ticker, flush=True)

    orderbook = client.get_orderbook(ticker)
    print("Orderbook payload:", orderbook, flush=True)

    strategy_decision = strategy.evaluate(orderbook)
    print("Strategy decision:", strategy_decision, flush=True)

    proposed_trade_dollars = min(25.0, risk.max_trade_dollars(equity))

    risk_decision = risk.approve_trade(
        portfolio_equity=equity,
        proposed_trade_dollars=proposed_trade_dollars,
        has_open_position=open_position,
    )
    print("Risk decision:", risk_decision, flush=True)

    if strategy_decision.action == "no_trade":
        notify(f"No trade on {ticker}: {strategy_decision.reason}")
        print("No trade: strategy veto.", flush=True)
        return

    if not risk_decision.approved:
        notify(f"No trade on {ticker}: {risk_decision.reason}")
        print("No trade: risk veto.", flush=True)
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
    print("Execution result:", result, flush=True)


def main():
    while True:
        try:
            run_once()
        except Exception as e:
            print("Cycle error:", repr(e), flush=True)
            notify(f"Cycle error: {repr(e)}")

        print(f"Sleeping {config.LOOP_SECONDS} seconds...", flush=True)
        time.sleep(config.LOOP_SECONDS)


if __name__ == "__main__":
    main()
