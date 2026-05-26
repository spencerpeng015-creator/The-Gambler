from dataclasses import dataclass

@dataclass
class RiskDecision:
    approved: bool
    reason: str
    max_trade_dollars: float
    suggested_trade_dollars: float

class RiskManager:
    def __init__(self, max_portfolio_risk_pct: float = 0.5, one_position_at_a_time: bool = True):
        self.max_portfolio_risk_pct = max_portfolio_risk_pct
        self.one_position_at_a_time = one_position_at_a_time

    def portfolio_equity(self, balance_payload: dict) -> float:
        if not balance_payload:
            return 0.0

        preferred_keys = [
            "balance_dollars",
            "portfolio_value_dollars",
            "portfolio_value",
            "equity",
            "balance",
            "cash_balance",
        ]

        for key in preferred_keys:
            value = balance_payload.get(key)
            if value is not None:
                try:
                    value = float(value)
                    if value > 0:
                        return value
                except (TypeError, ValueError):
                    pass

        return 0.0

    def max_trade_dollars(self, portfolio_equity: float) -> float:
        return max(0.0, portfolio_equity * self.max_portfolio_risk_pct)

    def has_open_position(self, positions_payload: dict) -> bool:
        if not positions_payload:
            return False

        positions = positions_payload.get("positions", [])
        market_positions = positions_payload.get("market_positions", [])
        event_positions = positions_payload.get("event_positions", [])

        for bucket in [positions, market_positions, event_positions]:
            for position in bucket:
                for key in ["position", "count", "net_position"]:
                    if key in position:
                        try:
                            if abs(float(position.get(key, 0))) > 0:
                                return True
                        except (TypeError, ValueError):
                            pass
        return False

    def approve_trade(
        self,
        portfolio_equity: float,
        proposed_trade_dollars: float,
        has_open_position: bool = False,
    ) -> RiskDecision:
        max_allowed = self.max_trade_dollars(portfolio_equity)

        if portfolio_equity <= 0:
            return RiskDecision(False, "Portfolio equity is zero or unavailable.", max_allowed, 0.0)

        if self.one_position_at_a_time and has_open_position:
            return RiskDecision(False, "Open position already exists.", max_allowed, 0.0)

        if proposed_trade_dollars <= 0:
            return RiskDecision(False, "Proposed trade dollars must be positive.", max_allowed, 0.0)

        if proposed_trade_dollars > max_allowed:
            return RiskDecision(
                False,
                "Proposed trade exceeds max portfolio risk cap.",
                max_allowed,
                max_allowed,
            )

        return RiskDecision(True, "Trade approved.", max_allowed, proposed_trade_dollars)
