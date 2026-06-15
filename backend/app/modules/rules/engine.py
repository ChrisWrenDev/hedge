from app.modules.rules.base import BaseRule, RuleContext, RuleResult
from app.modules.rules.registry import discover_rules


def evaluate_all(ctx: RuleContext) -> list[RuleResult]:
    results = []
    for name, rule_cls in discover_rules().items():
        rule = rule_cls()
        result = rule.evaluate(ctx)
        results.append(result)
    return results
