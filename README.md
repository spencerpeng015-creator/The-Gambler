# The-Gambler

A Render-hosted Kalshi BTC 15-minute market bot prototype.

## Current status
- Demo environment only
- Dry-run by default
- Reads balance, positions, markets, and order books
- Evaluates simple orderbook-based strategy
- Applies portfolio risk checks
- Can prepare limit orders but does not submit unless BOT_MODE=live

## Render
Build command:
pip install -r requirements.txt

Start command:
python main.py
