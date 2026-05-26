import uuid
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    attempted: bool
    submitted: bool
    mode: str
    message: str
    payload: dict | None = None


class ExecutionEngine:
    def __init__(self, client, bot_mode: str = "dry_run"):
        self.client = client
        self.bot_mode = bot_mode

    def contracts_for_dollars(self, trade_dollars: float, price_dollars: float) -> int:
        if price_dollars <= 0 or price_dollars >= 1:
            return 0
        return int(trade_dollars / price_dollars)

    def submit_limit_buy(self, ticker: str, side: str, count: int, price_dollars: float) -> ExecutionResult:
        if count <= 0:
            return ExecutionResult(
                attempted=False,
                submitted=False,
                mode=self.bot_mode,
                message="Count was zero; no order attempted.",
            )

        order_data = {
            "ticker": ticker,
            "action": "buy",
            "side": side,
            "count": count,
            "type": "limit",
            "client_order_id": str(uuid.uuid4()),
        }

        if side == "yes":
            order_data["yes_price_dollars"] = f"{price_dollars:.4f}"
        else:
            order_data["no_price_dollars"] = f"{price_dollars:.4f}"

        if self.bot_mode != "live":
            return ExecutionResult(
                attempted=True,
                submitted=False,
                mode=self.bot_mode,
                message="Dry run only. Order not submitted.",
                payload=order_data,
            )

        response = self.client.create_order(order_data)
        return ExecutionResult(
            attempted=True,
            submitted=True,
            mode=self.bot_mode,
            message="Live order submitted.",
            payload=response,
        )
