from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActionType(Enum):
    BUY = "buy"
    SELL = "sell"
    ALERT = "alert"
    REBALANCE = "rebalance"
    HEDGE = "hedger"


@dataclass
class ConvexityScoreSnapshot:
    score: float
    iv_percentile: float
    occ_symbol: str


@dataclass
class RuleResult:
    triggered: bool
    action: ActionType
    confidence: float
    details: dict[str, Any]
    suggested_trades: list[dict[str, Any]]


@dataclass
class RuleContext:
    portfolio: Any = None
    convexity_scores: list[ConvexityScoreSnapshot] = field(default_factory=list)


class BaseRule(ABC):
    name: str = ""
    description: str = ""
    config: dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    def evaluate(self, ctx: RuleContext) -> RuleResult:
        ...

    @abstractmethod
    def describe(self) -> dict[str, Any]:
        ...
