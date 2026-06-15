import uuid
from datetime import date, datetime, timezone

import pytest


# ── Scenario Model Tests ────────────────────────────────────────

class TestScenarioTemplateModel:
    @pytest.mark.asyncio
    async def test_create_template(self, db_session):
        from app.modules.scenarios.models import ScenarioTemplate
        t = ScenarioTemplate(
            name="Standard Price Shock",
            description="Test price shocks from -20% to +20%",
            parameters={
                "type": "price_shock",
                "shocks": [-0.20, -0.10, -0.05, 0, 0.05, 0.10, 0.20],
            },
            active=True,
        )
        db_session.add(t)
        await db_session.flush()
        assert t.id is not None
        assert t.name == "Standard Price Shock"
        assert t.active is True

    @pytest.mark.asyncio
    async def test_create_scenario_run(self, db_session):
        from app.modules.scenarios.models import ScenarioTemplate, ScenarioRun
        t = ScenarioTemplate(
            name="Test", description="x",
            parameters={"type": "price_shock", "shocks": [-0.10, 0.10]},
            active=True,
        )
        db_session.add(t)
        await db_session.flush()

        run = ScenarioRun(
            template_id=t.id,
            status="pending",
            results=None,
        )
        db_session.add(run)
        await db_session.flush()
        assert run.id is not None
        assert run.status == "pending"


# ── Scenario Engine Tests ───────────────────────────────────────

class TestScenarioEngine:
    def test_price_shock_increases_price(self):
        from app.modules.scenarios.engine import run_price_shock
        result = run_price_shock(spot=100.0, shock=0.10, iv=0.30, strike=100.0,
                                  rate=0.05, time_to_expiry=0.25, option_type="call",
                                  quantity=10)
        assert result["shocked_spot"] == pytest.approx(110.0)
        assert result["pnl"] != 0
        assert "new_greeks" in result

    def test_price_shock_decreases_price(self):
        from app.modules.scenarios.engine import run_price_shock
        result = run_price_shock(spot=100.0, shock=-0.10, iv=0.30, strike=100.0,
                                  rate=0.05, time_to_expiry=0.25, option_type="call",
                                  quantity=10)
        assert result["shocked_spot"] == 90.0

    def test_vol_shock(self):
        from app.modules.scenarios.engine import run_vol_shock
        result = run_vol_shock(spot=100.0, strike=100.0, rate=0.05,
                                time_to_expiry=0.25, iv=0.30, vol_shock=0.05,
                                option_type="call", quantity=10)
        assert result["shocked_iv"] == 0.35
        assert result["new_price"] > 0

    def test_time_decay(self):
        from app.modules.scenarios.engine import run_time_decay
        result = run_time_decay(spot=100.0, strike=100.0, rate=0.05,
                                 time_to_expiry=0.25, iv=0.30,
                                 decay_days=7, option_type="call", quantity=10)
        assert result["days_decayed"] == 7
        assert result["new_time_to_expiry"] < 0.25

    def test_combined_scenario(self):
        from app.modules.scenarios.engine import run_combined
        result = run_combined(
            spot=100.0, strike=100.0, rate=0.05,
            time_to_expiry=0.25, iv=0.30,
            price_shock=0.05, vol_shock=-0.05, decay_days=3,
            option_type="call", quantity=10,
        )
        assert result["shocked_spot"] == 105.0
        assert result["shocked_iv"] == 0.25


# ── Scenario Service Tests ──────────────────────────────────────

class TestScenarioService:
    @pytest.mark.asyncio
    async def test_run_scenario_template(self, db_session):
        from app.modules.scenarios.models import ScenarioTemplate
        from app.modules.scenarios.service import run_scenario
        t = ScenarioTemplate(
            name="Price Shock Test",
            description="test",
            parameters={
                "type": "price_shock",
                "shocks": [-0.10, 0.10],
                "spot": 100.0, "strike": 100.0, "iv": 0.30,
                "rate": 0.05, "time_to_expiry": 0.25,
                "option_type": "call", "quantity": 10,
            },
            active=True,
        )
        db_session.add(t)
        await db_session.commit()

        run = await run_scenario(db_session, t.id)
        assert run.status == "complete"
        assert run.results is not None

    @pytest.mark.asyncio
    async def test_run_nonexistent_template_returns_none(self, db_session):
        from app.modules.scenarios.service import run_scenario
        result = await run_scenario(db_session, uuid.uuid4())
        assert result is None


# ── Scenario API Tests ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_scenario_template(client):
    resp = await client.post("/api/scenarios/templates", json={
        "name": "Standard",
        "description": "test",
        "parameters": {"type": "price_shock", "shocks": [-0.10, 0.10]},
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "Standard"


@pytest.mark.asyncio
async def test_list_scenario_templates(client):
    await client.post("/api/scenarios/templates", json={
        "name": "A", "description": "x", "parameters": {},
    })
    resp = await client.get("/api/scenarios/templates")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_get_scenario_template(client):
    create = await client.post("/api/scenarios/templates", json={
        "name": "B", "description": "y", "parameters": {},
    })
    tid = create.json()["id"]
    resp = await client.get(f"/api/scenarios/templates/{tid}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "B"


@pytest.mark.asyncio
async def test_create_scenario_run(client):
    create = await client.post("/api/scenarios/templates", json={
        "name": "Run Test",
        "description": "x",
        "parameters": {
            "type": "price_shock", "shocks": [-0.10, 0.10],
            "spot": 100.0, "strike": 100.0, "iv": 0.30,
            "rate": 0.05, "time_to_expiry": 0.25,
            "option_type": "call", "quantity": 10,
        },
    })
    tid = create.json()["id"]
    resp = await client.post(f"/api/scenarios/templates/{tid}/run")
    assert resp.status_code in (200, 201)


@pytest.mark.asyncio
async def test_list_scenario_runs(client):
    resp = await client.get("/api/scenarios/runs")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
