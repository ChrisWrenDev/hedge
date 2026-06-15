from app.modules.rules.base import ActionType, BaseRule, RuleContext, RuleResult


class DeltaHedgeRule(BaseRule):
    name = "delta_hedge"
    description = "Triggers rebalance when net portfolio delta exceeds threshold"

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        threshold = self.config.get("delta_threshold", 0.15)
        net_delta = ctx.portfolio.net_delta if ctx.portfolio else 0.0

        if abs(net_delta) > threshold:
            direction = "sell" if net_delta > 0 else "buy"
            return RuleResult(
                triggered=True,
                action=ActionType.REBALANCE,
                confidence=min(abs(net_delta) / threshold, 1.0),
                details={
                    "net_delta": net_delta,
                    "threshold": threshold,
                    "direction": direction,
                },
                suggested_trades=[
                    {
                        "action": direction,
                        "underlying": "portfolio_hedge",
                        "notional_delta": abs(net_delta),
                    }
                ],
            )
        return RuleResult(
            triggered=False,
            action=ActionType.REBALANCE,
            confidence=0.0,
            details={"net_delta": net_delta, "threshold": threshold},
            suggested_trades=[],
        )

    def describe(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "config": self.config,
        }
