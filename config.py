import os
from dataclasses import dataclass


@dataclass
class Config:
    KALSHI_API_KEY_ID: str = os.getenv("KALSHI_API_KEY_ID", "")
    KALSHI_PRIVATE_KEY: str = os.getenv("KALSHI_PRIVATE_KEY", "")
    KALSHI_BASE_URL: str = os.getenv(
        "KALSHI_BASE_URL",
        "https://external-api.demo.kalshi.co/trade-api/v2",
    )
    BOT_MODE: str = os.getenv("BOT_MODE", "dry_run")
    STARTING_CAPITAL: float = float(os.getenv("STARTING_CAPITAL", "200"))
    MAX_PORTFOLIO_RISK_PCT: float = float(os.getenv("MAX_PORTFOLIO_RISK_PCT", "0.5"))
    BTC_MARKET_TICKER_PREFIX: str = os.getenv("BTC_MARKET_TICKER_PREFIX", "KXBTC15M")
    BTC_TARGET_TICKER: str = os.getenv("BTC_TARGET_TICKER", "")
    LOOP_SECONDS: int = int(os.getenv("LOOP_SECONDS", "20"))


config = Config()
