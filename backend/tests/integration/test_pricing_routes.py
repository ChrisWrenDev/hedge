import pytest
from datetime import date, datetime, timezone


@pytest.mark.asyncio
async def test_pricing_health(client):
    resp = await client.get("/api/pricing/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_pricing_greeks_endpoint(client):
    resp = await client.get("/api/pricing/greeks", params={
        "spot": 100, "strike": 100, "rate": 0.05,
        "time_to_expiry": 0.25, "iv": 0.30, "option_type": "call",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "delta" in data
    assert "gamma" in data
    assert "theta" in data
    assert "vega" in data
    assert "rho" in data
    assert 0.45 < data["delta"] < 0.60


@pytest.mark.asyncio
async def test_pricing_iv_endpoint(client):
    resp = await client.get("/api/pricing/iv", params={
        "market_price": 5.0, "spot": 100, "strike": 100,
        "rate": 0.05, "time_to_expiry": 0.25, "option_type": "call",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "implied_volatility" in data
    assert 0.20 < data["implied_volatility"] < 0.40


@pytest.mark.asyncio
async def test_pricing_price_endpoint(client):
    resp = await client.get("/api/pricing/price", params={
        "spot": 100, "strike": 100, "rate": 0.05,
        "time_to_expiry": 0.25, "iv": 0.30, "option_type": "call",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "price" in data
    assert 4.0 < data["price"] < 8.0


@pytest.mark.asyncio
async def test_convexity_top_scores_empty(client):
    resp = await client.get("/api/convexity/top")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_convexity_score_endpoint(client):
    resp = await client.get("/api/convexity/score", params={
        "gamma_per_theta": 4.0,
        "vega_normalized": 0.02,
        "iv_rank": 35,
        "volume_oi_ratio": 0.15,
        "dte": 45,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "score" in data
    assert 0 <= data["score"] <= 100


@pytest.mark.asyncio
async def test_convexity_top_scores_with_data(client, db_session):
    from app.modules.options_data.models import Ticker, OptionsContract
    from app.modules.convexity.models import ConvexityScore

    ticker = Ticker(symbol="AAPL", type="equity")
    db_session.add(ticker)
    await db_session.flush()

    for strike, sc in [(180, 60.0), (190, 85.0), (200, 45.0)]:
        contract = OptionsContract(
            ticker_id=ticker.id, occ_symbol=f"AAPL250321C{strike}",
            expiration_date=date(2025, 3, 21), strike=strike, option_type="call",
        )
        db_session.add(contract)
        await db_session.flush()
        db_session.add(ConvexityScore(
            contract_id=contract.id, score_date=date.today(), score=sc,
            gamma_per_theta=3.0, vega_normalized=0.02, iv_rank=40.0, iv_percentile=45.0,
        ))
    await db_session.commit()

    resp = await client.get("/api/convexity/top", params={"limit": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["score"] == 85.0
