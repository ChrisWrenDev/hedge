# Rules Engine

## Design Principles

1. **Code-based core** — Python classes for complex logic, maximum flexibility
2. **YAML strategy params** — Thresholds and filters editable without deploys
3. **Database runtime state** — Enable/disable rules, audit trail, trigger history
4. **Composable** — Rules can reference each other's outputs

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  RULES ENGINE                        │
│                                                     │
│  ┌───────────┐  ┌───────────┐  ┌────────────────┐  │
│  │  Code     │  │  YAML     │  │  Database       │  │
│  │  Rules    │  │  Params   │  │  State          │  │
│  │           │  │           │  │                 │  │
│  │  Python   │  │  Strategy │  │  enable/disable │  │
│  │  classes  │  │  config   │  │  audit log      │  │
│  │  in       │  │  loaded   │  │  trigger        │  │
│  │  rules/   │  │  at start │  │  history        │  │
│  └─────┬─────┘  └─────┬─────┘  └────────┬───────┘  │
│        │              │                  │          │
│        └──────────────┴──────────────────┘          │
│                       │                             │
│                       ▼                             │
│              ┌────────────────┐                     │
│              │  Rule Engine   │                     │
│              │  evaluator     │                     │
│              └────────┬───────┘                     │
│                       │                             │
│                       ▼                             │
│              ┌────────────────┐                     │
│              │  RuleResult    │                     │
│              │  triggered?    │                     │
│              │  action        │                     │
│              │  confidence    │                     │
│              └────────────────┘                     │
└─────────────────────────────────────────────────────┘
```

## Core Types

```python
# rules/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class ActionType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    ALERT = "alert"
    REBALANCE = "rebalance"
    HEDGE = "hedge"

@dataclass
class RuleResult:
    triggered: bool
    action: ActionType
    confidence: float          # 0.0 - 1.0
    details: dict              # Human-readable explanation
    suggested_trades: list     # Optional specific trade suggestions

@dataclass
class RuleContext:
    portfolio: PortfolioSnapshot
    market_data: MarketDataSnapshot
    positions: list[Position]
    convexity_scores: list[ConvexityScore]
    vol_surface: VolatilitySurface
    historical_vol: HistoricalVolatility
    config: dict               # Merged YAML + DB config

class BaseRule(ABC):
    name: str
    description: str

    @abstractmethod
    def evaluate(self, ctx: RuleContext) -> RuleResult:
        """Evaluate rule against current state."""
        pass

    @abstractmethod
    def describe(self) -> dict:
        """Return rule metadata for API/dashboard."""
        pass
```

## Rule Registry

```python
# rules/registry.py
import importlib
import pkgutil
from pathlib import Path

_registry: dict[str, type[BaseRule]] = {}

def register_rule(cls: type[BaseRule]) -> type[BaseRule]:
    """Decorator to register a rule class."""
    _registry[cls.name] = cls
    return cls

def discover_rules():
    """Auto-import all modules in rules/rules/ to trigger registration."""
    package_dir = Path(__file__).parent / "rules"
    for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
        importlib.import_module(f"app.modules.rules.rules.{module_name}")
```

## Concrete Rules

### Convexity Bargain

```python
# rules/rules/convexity_bargain.py
@register_rule
class ConvexityBargainRule(BaseRule):
    name = "convexity_bargain"
    description = "Buy options with high convexity relative to theta cost"

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        config = ctx.config
        candidates = [
            s for s in ctx.convexity_scores
            if s.score >= config["min_convexity_score"]
            and s.iv_percentile <= config["max_iv_percentile"]
        ]

        # Filter by available delta budget
        delta_budget = ctx.portfolio.delta_budget_remaining
        viable = [
            c for c in candidates
            if abs(c.contract.delta) <= delta_budget
        ]

        if not viable:
            return RuleResult(triggered=False, ...)

        best = sorted(viable, key=lambda x: x.score, reverse=True)[0]
        return RuleResult(
            triggered=True,
            action=ActionType.BUY,
            confidence=min(best.score / 100, 0.95),
            details={"reason": f"Convexity score {best.score:.1f}", ...},
            suggested_trades=[{...}]
        )
```

### Delta Hedge

```python
@register_rule
class DeltaHedgeRule(BaseRule):
    name = "delta_hedge"
    description = "Rebalance when net delta exceeds threshold"

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        net_delta = ctx.portfolio.net_delta
        threshold = ctx.config["delta_threshold"]

        if abs(net_delta) < threshold:
            return RuleResult(triggered=False, ...)

        direction = "reduce" if net_delta > 0 else "increase"
        return RuleResult(
            triggered=True,
            action=ActionType.REBALANCE,
            confidence=0.9,
            details={"net_delta": net_delta, "action": direction},
        )
```

### Vol Skew

```python
@register_rule
class VolSkewRule(BaseRule):
    name = "vol_skew"
    description = "Alert on unusual volatility skew changes"

    def evaluate(self, ctx: RuleContext) -> RuleResult:
        skew = ctx.vol_surface.skew_metric
        historical_avg = ctx.historical_vol.avg_skew
        threshold = ctx.config["skew_change_threshold"]

        if abs(skew - historical_avg) < threshold:
            return RuleResult(triggered=False, ...)

        return RuleResult(
            triggered=True,
            action=ActionType.ALERT,
            confidence=0.7,
            details={"current_skew": skew, "avg_skew": historical_avg},
        )
```

## YAML Strategy Configs

```yaml
# strategies/convexity_bargain.yaml
name: convexity_bargain
description: "Buy options with high convexity relative to theta cost"
active: true
priority: 10

parameters:
  min_convexity_score: 70
  max_theta_per_day: 0.05
  min_gamma: 0.02
  min_volume: 100
  max_iv_percentile: 50
  min_dte: 14
  max_dte: 90

filters:
  asset_types: [equity, index]
  option_types: [call, put]
  exchanges: [NYSE, NASDAQ, CBOE]

sizing:
  max_position_pct: 5        # Max 5% of portfolio per trade
  max_delta_per_trade: 0.10  # Max delta exposure per trade
```

```yaml
# strategies/delta_hedge.yaml
name: delta_hedge
description: "Rebalance when net delta exceeds threshold"
active: true
priority: 5

parameters:
  delta_threshold: 0.15      # Rebalance when |net_delta| > 0.15
  target_delta: 0.0          # Target neutral delta
  hedge_instruments: [underlying, ATM_options]
```

## Database State

### rule_definitions

Loaded at startup. YAML configs merged with DB overrides.

```python
# rules/engine.py
async def load_rules(db: AsyncSession) -> list[BaseRule]:
    """Load active rules from DB, merge with YAML configs."""
    db_rules = await db.execute(
        select(RuleDefinition).where(RuleDefinition.active == True)
    )

    rules = []
    for db_rule in db_rules.scalars():
        # Load YAML config
        yaml_config = load_yaml_config(db_rule.name)

        # Merge: DB config overrides YAML
        merged_config = {**yaml_config, **(db_rule.config or {})}

        # Instantiate code-based rule
        rule_cls = _registry.get(db_rule.module_path)
        if rule_cls:
            rule = rule_cls()
            rule.config = merged_config
            rules.append(rule)

    return sorted(rules, key=lambda r: r.priority)
```

### rule_triggers

Every time a rule fires, a trigger record is created:

```json
{
  "rule_id": "uuid",
  "triggered_at": "2025-01-15T14:30:00Z",
  "context": {
    "portfolio_delta": 0.18,
    "convexity_score": 82.5,
    "iv_percentile": 35,
    "underlying_price": 185.50
  },
  "action_taken": "buy",
  "details": {
    "contract": "AAPL 2025-02-21 190C",
    "suggested_quantity": 5,
    "estimated_cost": 2350.00
  }
}
```

### rule_audit_log

Tracks all state changes:

| action | When |
|---|---|
| enabled | User activates rule |
| disabled | User deactivates rule |
| modified | Config parameters changed |
| triggered | Rule evaluated and fired |
| dismissed | User dismissed a trigger |

## Evaluation Flow

```python
# rules/engine.py
async def evaluate_all(db: AsyncSession) -> list[RuleTrigger]:
    """Evaluate all active rules, return triggers."""
    rules = await load_rules(db)
    context = await build_context(db)
    triggers = []

    for rule in rules:
        try:
            result = rule.evaluate(context)

            if result.triggered:
                trigger = await record_trigger(db, rule, result)
                triggers.append(trigger)

                await audit_log(db, rule, "triggered", result.details)

        except Exception as e:
            logger.error(f"Rule {rule.name} failed: {e}")
            await audit_log(db, rule, "error", {"error": str(e)})

    return triggers
```
