import pytest
from datetime import date, datetime, timezone


# ── Portfolio API Routes ────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_portfolio(client):
    resp = await client.post("/api/portfolio/", json={
        "name": "Main",
        "description": "Primary",
        "budget": 100000,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Main"
    assert data["budget"] == 100000


@pytest.mark.asyncio
async def test_list_portfolios_empty(client):
    resp = await client.get("/api/portfolio/")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_portfolios_after_create(client):
    await client.post("/api/portfolio/", json={"name": "A", "budget": 50000})
    await client.post("/api/portfolio/", json={"name": "B", "budget": 75000})

    resp = await client.get("/api/portfolio/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_portfolio(client):
    create = await client.post("/api/portfolio/", json={"name": "Main", "budget": 100000})
    pid = create.json()["id"]

    resp = await client.get(f"/api/portfolio/{pid}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Main"


@pytest.mark.asyncio
async def test_get_portfolio_not_found(client):
    import uuid
    resp = await client.get(f"/api/portfolio/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_position(client, db_session):
    from app.modules.options_data.models import Ticker, OptionsContract
    ticker = Ticker(symbol="AAPL", type="equity")
    db_session.add(ticker)
    await db_session.flush()
    contract = OptionsContract(
        ticker_id=ticker.id, occ_symbol="AAPL250321C190",
        expiration_date=date(2025, 3, 21), strike=190, option_type="call",
    )
    db_session.add(contract)
    await db_session.commit()

    create_p = await client.post("/api/portfolio/", json={"name": "Main", "budget": 100000})
    pid = create_p.json()["id"]

    resp = await client.post(f"/api/portfolio/{pid}/positions", json={
        "contract_occ": "AAPL250321C190",
        "quantity": 10,
        "entry_price": 2.15,
        "entry_date": "2025-01-15",
    })
    assert resp.status_code == 201
    assert resp.json()["quantity"] == 10


@pytest.mark.asyncio
async def test_list_positions(client, db_session):
    from app.modules.options_data.models import Ticker, OptionsContract
    ticker = Ticker(symbol="AAPL", type="equity")
    db_session.add(ticker)
    await db_session.flush()
    contract = OptionsContract(
        ticker_id=ticker.id, occ_symbol="AAPL250321C190",
        expiration_date=date(2025, 3, 21), strike=190, option_type="call",
    )
    db_session.add(contract)
    await db_session.commit()

    create_p = await client.post("/api/portfolio/", json={"name": "Main", "budget": 100000})
    pid = create_p.json()["id"]

    await client.post(f"/api/portfolio/{pid}/positions", json={
        "contract_occ": "AAPL250321C190", "quantity": 10, "entry_price": 2.15, "entry_date": "2025-01-15",
    })

    resp = await client.get(f"/api/portfolio/{pid}/positions")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_portfolio_greeks(client, db_session):
    from app.modules.options_data.models import Ticker, OptionsContract
    ticker = Ticker(symbol="AAPL", type="equity")
    db_session.add(ticker)
    await db_session.flush()
    contract = OptionsContract(
        ticker_id=ticker.id, occ_symbol="AAPL250321C190",
        expiration_date=date(2025, 3, 21), strike=190, option_type="call",
    )
    db_session.add(contract)
    await db_session.commit()

    create_p = await client.post("/api/portfolio/", json={"name": "Main", "budget": 100000})
    pid = create_p.json()["id"]

    resp = await client.get(f"/api/portfolio/{pid}/greeks")
    assert resp.status_code == 404


# ── Rules API Routes ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_rule(client):
    resp = await client.post("/api/rules/", json={
        "name": "delta_hedge",
        "rule_type": "code",
        "module_path": "delta_hedge",
        "config": {"delta_threshold": 0.15},
        "active": True,
        "priority": 5,
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "delta_hedge"


@pytest.mark.asyncio
async def test_list_rules(client):
    await client.post("/api/rules/", json={
        "name": "rule_a", "rule_type": "code", "module_path": "a", "active": True, "priority": 10,
    })
    resp = await client.get("/api/rules/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_toggle_rule(client):
    create = await client.post("/api/rules/", json={
        "name": "toggle_test", "rule_type": "code", "module_path": "t", "active": True, "priority": 10,
    })
    rid = create.json()["id"]

    resp = await client.patch(f"/api/rules/{rid}/toggle")
    assert resp.status_code == 200
    assert resp.json()["active"] is False


@pytest.mark.asyncio
async def test_list_triggers_empty(client):
    resp = await client.get("/api/rules/triggers")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_audit_log_empty(client):
    resp = await client.get("/api/rules/audit")
    assert resp.status_code == 200
    assert resp.json() == []
