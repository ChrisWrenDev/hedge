from app.modules.rules.base import ActionType, BaseRule, RuleContext, RuleResult


class ConvexityBargainRule(BaseRule):
    name = "convexity_bargain"
    description = "Buys options with high convexity score and low IV percentile"

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        min_score = self.config.get("min_convexity_score", 70)
        max_iv_pctl = self.config.get("max_iv_percentile", 50)

        candidates = [
            s for s in ctx.convexity_scores
            if s.score >= min_score and s.iv_percentile <= max_iv_pctl
        ]

        if not candidates:
            return RuleResult(
                triggered=False,
                action=ActionType.BUY,
                confidence=0.0,
                details={"candidates_found": 0},
                suggested_trades=[],
            )

        best = max(candidates, key=lambda s: s.score)
        confidence = min(best.score / 100.0, 1.0)

        budget_remaining = getattr(ctx.portfolio, "delta_budget_remaining", 0.0)
        if budget_remaining <= 0:
            return RuleResult(
                triggered=False,
                action=ActionType.BUY,
                confidence=confidence,
                details={"candidates_found": len(candidates), "budget_exhausted": True},
                suggested_trades=[],
            )

        return RuleResult(
            triggered=True,
            action=ActionType.BUY,
            confidence=confidence,
            details={
                "candidates_found": len(candidates),
                "best_occ": best.occ_symbol,
                "best_score": best.score,
                "best_iv_pctl": best.iv_percentile,
            },
            suggested_trades=[
                {
                    "action": "buy",
                    "occ_symbol": best.occ_symbol,
                    "convexity_score": best.score,
                }
            ],
        )

    def describe(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "config": self.config,
        }
