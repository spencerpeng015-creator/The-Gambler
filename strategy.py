from dataclasses import dataclass


@dataclass
class StrategyDecision:
    action: str
    confidence: float
    fair_yes_price: float
    best_yes_bid: float
    best_yes_ask: float
    spread: float
    reason: str


class StrategyEngine:
    def __init__(self, min_edge_cents: float = 0.03, max_spread_cents: float = 0.08):
        self.min_edge = min_edge_cents
        self.max_spread = max_spread_cents

    def _best_yes_bid(self, orderbook: dict) -> float:
        yes = orderbook.get("orderbook", {}).get("yes", [])
        if not yes:
            yes = orderbook.get("yes", [])
        if not yes:
            return 0.0
        return max(float(level[0]) for level in yes) / 100.0

    def _best_no_bid(self, orderbook: dict) -> float:
        no = orderbook.get("orderbook", {}).get("no", [])
        if not no:
            no = orderbook.get("no", [])
        if not no:
            return 0.0
        return max(float(level[0]) for level in no) / 100.0

    def _best_yes_ask(self, orderbook: dict) -> float:
        best_no_bid = self._best_no_bid(orderbook)
        if best_no_bid <= 0:
            return 1.0
        return 1.0 - best_no_bid

    def _spread(self, orderbook: dict) -> float:
        best_yes_bid = self._best_yes_bid(orderbook)
        best_yes_ask = self._best_yes_ask(orderbook)
        if best_yes_bid <= 0 or best_yes_ask <= 0:
            return 1.0
        return max(0.0, best_yes_ask - best_yes_bid)

    def _simple_orderbook_imbalance(self, orderbook: dict) -> float:
        yes = orderbook.get("orderbook", {}).get("yes", [])
        if not yes:
            yes = orderbook.get("yes", [])
        no = orderbook.get("orderbook", {}).get("no", [])
        if not no:
            no = orderbook.get("no", [])

        yes_size = sum(float(level[1]) for level in yes[:3]) if yes else 0.0
        no_size = sum(float(level[1]) for level in no[:3]) if no else 0.0

        total = yes_size + no_size
        if total == 0:
            return 0.0

        return (yes_size - no_size) / total

    def estimate_fair_yes_price(self, orderbook: dict) -> float:
        best_yes_bid = self._best_yes_bid(orderbook)
        best_yes_ask = self._best_yes_ask(orderbook)
        midpoint = (best_yes_bid + best_yes_ask) / 2.0

        imbalance = self._simple_orderbook_imbalance(orderbook)
        adjustment = 0.02 * imbalance
        fair_price = midpoint + adjustment

        return max(0.01, min(0.99, fair_price))

    def evaluate(self, orderbook: dict) -> StrategyDecision:
        best_yes_bid = self._best_yes_bid(orderbook)
        best_yes_ask = self._best_yes_ask(orderbook)
        spread = self._spread(orderbook)
        fair_yes = self.estimate_fair_yes_price(orderbook)

        if best_yes_bid <= 0 or best_yes_ask >= 1.0:
            return StrategyDecision(
                action="no_trade",
                confidence=0.0,
                fair_yes_price=fair_yes,
                best_yes_bid=best_yes_bid,
                best_yes_ask=best_yes_ask,
                spread=spread,
                reason="Incomplete orderbook.",
            )

        if spread > self.max_spread:
            return StrategyDecision(
                action="no_trade",
                confidence=0.0,
                fair_yes_price=fair_yes,
                best_yes_bid=best_yes_bid,
                best_yes_ask=best_yes_ask,
                spread=spread,
                reason="Spread too wide.",
            )

        yes_edge = fair_yes - best_yes_ask
        no_edge = best_yes_bid - fair_yes

        if yes_edge >= self.min_edge:
            return StrategyDecision(
                action="buy_yes",
                confidence=min(1.0, yes_edge / max(self.min_edge, 0.0001)),
                fair_yes_price=fair_yes,
                best_yes_bid=best_yes_bid,
                best_yes_ask=best_yes_ask,
                spread=spread,
                reason="YES appears underpriced.",
            )

        if no_edge >= self.min_edge:
            return StrategyDecision(
                action="buy_no",
                confidence=min(1.0, no_edge / max(self.min_edge, 0.0001)),
                fair_yes_price=fair_yes,
                best_yes_bid=best_yes_bid,
                best_yes_ask=best_yes_ask,
                spread=spread,
                reason="NO appears underpriced.",
            )

        return StrategyDecision(
            action="no_trade",
            confidence=0.0,
            fair_yes_price=fair_yes,
            best_yes_bid=best_yes_bid,
            best_yes_ask=best_yes_ask,
            spread=spread,
            reason="No edge above threshold.",
        )
