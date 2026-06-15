import pytest
from datetime import date, datetime, timezone


# ── Portfolio Model Tests ───────────────────────────────────────

class TestPortfolioModel:
    @pytest.mark.asyncio
    async def test_create_portfolio(self, db_session):
        from app.modules.portfolio.models import Portfolio
        p = Portfolio(name="Main", description="Primary portfolio", budget=100000)
        db_session.add(p)
        await db_session.flush()
        assert p.id is not None
        assert p.name == "Main"
        assert float(p.budget) == 100000

    @pytest.mark.asyncio
    async def test_create_position(self, db_session):
        from app.modules.portfolio.models import Portfolio, Position
        from app.modules.options_data.models import Ticker, OptionsContract
        from datetime import date as d

        ticker = Ticker(symbol="AAPL", type="equity")
        db_session.add(ticker)
        await db_session.flush()

        contract = OptionsContract(
            ticker_id=ticker.id, occ_symbol="AAPL250321C190",
            expiration_date=d(2025, 3, 21), strike=190, option_type="call",
        )
        db_session.add(contract)
        await db_session.flush()

        portfolio = Portfolio(name="Main", budget=100000)
        db_session.add(portfolio)
        await db_session.flush()

        pos = Position(
            portfolio_id=portfolio.id,
            contract_id=contract.id,
            quantity=10,
            entry_price=2.15,
            entry_date=d(2025, 1, 15),
            current_price=2.80,
            unrealized_pnl=650.0,
        )
        db_session.add(pos)
        await db_session.flush()

        assert pos.id is not None
        assert pos.quantity == 10
        assert float(pos.unrealized_pnl) == 650.0

    @pytest.mark.asyncio
    async def test_create_portfolio_greeks(self, db_session):
        from app.modules.portfolio.models import Portfolio, PortfolioGreeks

        portfolio = Portfolio(name="Main", budget=100000)
        db_session.add(portfolio)
        await db_session.flush()

        greeks = PortfolioGreeks(
            portfolio_id=portfolio.id,
            timestamp=datetime.now(timezone.utc),
            net_delta=0.31,
            net_gamma=-0.02,
            net_theta=-45.0,
            net_vega=1.2,
        )
        db_session.add(greeks)
        await db_session.flush()

        assert greeks.id is not None
        assert float(greeks.net_delta) == 0.31


# ── Portfolio Service Tests ─────────────────────────────────────

class TestPortfolioService:
    @pytest.mark.asyncio
    async def test_aggregate_greeks(self, db_session):
        from app.modules.portfolio.models import Portfolio, Position
        from app.modules.portfolio.service import aggregate_greeks
        from app.modules.options_data.models import Ticker, OptionsContract
        from app.modules.pricing.models import GreeksSnapshot
        from datetime import date as d, datetime, timezone

        ticker = Ticker(symbol="AAPL", type="equity")
        db_session.add(ticker)
        await db_session.flush()

        c1 = OptionsContract(
            ticker_id=ticker.id, occ_symbol="C1",
            expiration_date=d(2025, 3, 21), strike=190, option_type="call",
        )
        c2 = OptionsContract(
            ticker_id=ticker.id, occ_symbol="C2",
            expiration_date=d(2025, 3, 21), strike=200, option_type="put",
        )
        db_session.add_all([c1, c2])
        await db_session.flush()

        portfolio = Portfolio(name="Main", budget=100000)
        db_session.add(portfolio)
        await db_session.flush()

        db_session.add_all([
            Position(portfolio_id=portfolio.id, contract_id=c1.id, quantity=10, entry_price=2.0, entry_date=d(2025, 1, 15)),
            Position(portfolio_id=portfolio.id, contract_id=c2.id, quantity=-5, entry_price=3.0, entry_date=d(2025, 1, 15)),
        ])
        await db_session.flush()

        now = datetime.now(timezone.utc)
        db_session.add_all([
            GreeksSnapshot(
                contract_id=c1.id, timestamp=now, source="calculated",
                delta=0.54, gamma=0.03, theta=-0.05, vega=0.15,
            ),
            GreeksSnapshot(
                contract_id=c2.id, timestamp=now, source="calculated",
                delta=-0.46, gamma=0.02, theta=-0.04, vega=0.12,
            ),
        ])
        await db_session.commit()

        result = await aggregate_greeks(db_session, portfolio.id)
        # net_delta = 10*0.54*100 + (-5)*(-0.46)*100 = 540 + 230 = 770
        assert result is not None
        assert abs(float(result.net_delta) - 770.0) < 1.0

    @pytest.mark.asyncio
    async def test_get_portfolio_positions(self, db_session):
        from app.modules.portfolio.models import Portfolio, Position
        from app.modules.portfolio.service import get_portfolio_positions
        from app.modules.options_data.models import Ticker, OptionsContract
        from datetime import date as d

        ticker = Ticker(symbol="AAPL", type="equity")
        db_session.add(ticker)
        await db_session.flush()

        c1 = OptionsContract(
            ticker_id=ticker.id, occ_symbol="P1",
            expiration_date=d(2025, 3, 21), strike=190, option_type="call",
        )
        db_session.add(c1)
        await db_session.flush()

        portfolio = Portfolio(name="Main", budget=100000)
        db_session.add(portfolio)
        await db_session.flush()

        db_session.add(Position(
            portfolio_id=portfolio.id, contract_id=c1.id,
            quantity=10, entry_price=2.0, entry_date=d(2025, 1, 15),
        ))
        await db_session.commit()

        positions = await get_portfolio_positions(db_session, portfolio.id)
        assert len(positions) == 1
        assert positions[0].quantity == 10


# ── Rules Engine Tests ──────────────────────────────────────────

class TestActionType:
    def test_action_types(self):
        from app.modules.rules.base import ActionType
        assert ActionType.BUY.value == "buy"
        assert ActionType.SELL.value == "sell"
        assert ActionType.ALERT.value == "alert"
        assert ActionType.REBALANCE.value == "rebalance"
        assert ActionType.HEDGE.value == "hedger"


class TestRuleResult:
    def test_create_rule_result(self):
        from app.modules.rules.base import RuleResult, ActionType
        r = RuleResult(
            triggered=True,
            action=ActionType.BUY,
            confidence=0.85,
            details={"reason": "high convexity"},
            suggested_trades=[{"symbol": "AAPL", "qty": 5}],
        )
        assert r.triggered is True
        assert r.confidence == 0.85

    def test_not_triggered_result(self):
        from app.modules.rules.base import RuleResult, ActionType
        r = RuleResult(
            triggered=False,
            action=ActionType.ALERT,
            confidence=0.0,
            details={},
            suggested_trades=[],
        )
        assert r.triggered is False


class TestRuleRegistry:
    def test_register_and_discover(self):
        from app.modules.rules.base import BaseRule, RuleResult, ActionType, RuleContext
        from app.modules.rules.registry import register_rule, get_rule, _registry

        @register_rule
        class TestRule(BaseRule):
            name = "test_rule"
            description = "test"

            def evaluate(self, ctx):
                return RuleResult(triggered=False, action=ActionType.ALERT, confidence=0, details={}, suggested_trades=[])

            def describe(self):
                return {"name": self.name}

        assert "test_rule" in _registry
        assert get_rule("test_rule") is TestRule

        # Cleanup
        del _registry["test_rule"]

    def test_get_unknown_rule_returns_none(self):
        from app.modules.rules.registry import get_rule
        assert get_rule("nonexistent") is None


class TestDeltaHedgeRule:
    def test_triggers_when_delta_exceeds_threshold(self):
        from app.modules.rules.rules.delta_hedge import DeltaHedgeRule
        from app.modules.rules.base import RuleContext
        from dataclasses import dataclass

        @dataclass
        class MockPortfolio:
            net_delta: float

        rule = DeltaHedgeRule()
        rule.config = {"delta_threshold": 0.15}
        ctx = RuleContext(portfolio=MockPortfolio(net_delta=0.20))

        result = rule.evaluate(ctx)
        assert result.triggered is True
        assert result.action.value == "rebalance"

    def test_does_not_trigger_below_threshold(self):
        from app.modules.rules.rules.delta_hedge import DeltaHedgeRule
        from app.modules.rules.base import RuleContext
        from dataclasses import dataclass

        @dataclass
        class MockPortfolio:
            net_delta: float

        rule = DeltaHedgeRule()
        rule.config = {"delta_threshold": 0.15}
        ctx = RuleContext(portfolio=MockPortfolio(net_delta=0.10))

        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_negative_delta_triggers(self):
        from app.modules.rules.rules.delta_hedge import DeltaHedgeRule
        from app.modules.rules.base import RuleContext
        from dataclasses import dataclass

        @dataclass
        class MockPortfolio:
            net_delta: float

        rule = DeltaHedgeRule()
        rule.config = {"delta_threshold": 0.15}
        ctx = RuleContext(portfolio=MockPortfolio(net_delta=-0.25))

        result = rule.evaluate(ctx)
        assert result.triggered is True


class TestConvexityBargainRule:
    def test_triggers_on_high_score(self):
        from app.modules.rules.rules.convexity_bargain import ConvexityBargainRule
        from app.modules.rules.base import RuleContext, ConvexityScoreSnapshot
        from dataclasses import dataclass

        @dataclass
        class MockPortfolio:
            delta_budget_remaining: float

        rule = ConvexityBargainRule()
        rule.config = {"min_convexity_score": 70, "max_iv_percentile": 50}

        ctx = RuleContext(
            portfolio=MockPortfolio(delta_budget_remaining=0.5),
            convexity_scores=[
                ConvexityScoreSnapshot(score=82.5, iv_percentile=35, occ_symbol="AAPL250321C190"),
            ],
        )

        result = rule.evaluate(ctx)
        assert result.triggered is True
        assert result.confidence > 0.7

    def test_does_not_trigger_low_score(self):
        from app.modules.rules.rules.convexity_bargain import ConvexityBargainRule
        from app.modules.rules.base import RuleContext, ConvexityScoreSnapshot
        from dataclasses import dataclass

        @dataclass
        class MockPortfolio:
            delta_budget_remaining: float

        rule = ConvexityBargainRule()
        rule.config = {"min_convexity_score": 70, "max_iv_percentile": 50}

        ctx = RuleContext(
            portfolio=MockPortfolio(delta_budget_remaining=0.5),
            convexity_scores=[
                ConvexityScoreSnapshot(score=50.0, iv_percentile=35, occ_symbol="X"),
            ],
        )

        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_does_not_trigger_high_iv(self):
        from app.modules.rules.rules.convexity_bargain import ConvexityBargainRule
        from app.modules.rules.base import RuleContext, ConvexityScoreSnapshot
        from dataclasses import dataclass

        @dataclass
        class MockPortfolio:
            delta_budget_remaining: float

        rule = ConvexityBargainRule()
        rule.config = {"min_convexity_score": 70, "max_iv_percentile": 50}

        ctx = RuleContext(
            portfolio=MockPortfolio(delta_budget_remaining=0.5),
            convexity_scores=[
                ConvexityScoreSnapshot(score=82.5, iv_percentile=60, occ_symbol="X"),
            ],
        )

        result = rule.evaluate(ctx)
        assert result.triggered is False


# ── Rules Model Tests ───────────────────────────────────────────

class TestRuleModels:
    @pytest.mark.asyncio
    async def test_create_rule_definition(self, db_session):
        from app.modules.rules.models import RuleDefinition
        rd = RuleDefinition(
            name="delta_hedge",
            rule_type="code",
            module_path="delta_hedge",
            config={"delta_threshold": 0.15},
            active=True,
            priority=5,
        )
        db_session.add(rd)
        await db_session.flush()
        assert rd.id is not None
        assert rd.active is True

    @pytest.mark.asyncio
    async def test_create_rule_trigger(self, db_session):
        from app.modules.rules.models import RuleDefinition, RuleTrigger
        rd = RuleDefinition(
            name="test", rule_type="code", module_path="test",
            active=True, priority=10,
        )
        db_session.add(rd)
        await db_session.flush()

        trigger = RuleTrigger(
            rule_id=rd.id,
            triggered_at=datetime.now(timezone.utc),
            context={"net_delta": 0.20},
            action_taken="rebalance",
        )
        db_session.add(trigger)
        await db_session.flush()
        assert trigger.id is not None

    @pytest.mark.asyncio
    async def test_create_audit_log(self, db_session):
        from app.modules.rules.models import RuleDefinition, RuleAuditLog
        rd = RuleDefinition(
            name="test", rule_type="code", module_path="test",
            active=True, priority=10,
        )
        db_session.add(rd)
        await db_session.flush()

        log = RuleAuditLog(
            rule_id=rd.id,
            action="triggered",
            details={"reason": "delta exceeded"},
        )
        db_session.add(log)
        await db_session.flush()
        assert log.id is not None
