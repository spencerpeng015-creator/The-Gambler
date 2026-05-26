import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    KALSHI_API_KEY_ID = os.getenv("KALSHI_API_KEY_ID", "")
    KALSHI_PRIVATE_KEY = os.getenv("KALSHI_PRIVATE_KEY", "")
    KALSHI_BASE_URL = os.getenv("KALSHI_BASE_URL", "https://external-api.demo.kalshi.co/trade-api/v2")
    BOT_MODE = os.getenv("BOT_MODE", "dry_run")
    STARTING_CAPITAL = float(os.getenv("STARTING_CAPITAL", "100"))
    MAX_PORTFOLIO_RISK_PCT = float(os.getenv("MAX_PORTFOLIO_RISK_PCT", "0.5"))
    BTC_MARKET_TICKER_PREFIX = os.getenv("BTC_MARKET_TICKER_PREFIX", "KXBTC15M")

config = Config()
