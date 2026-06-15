import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_list_tickers_empty(client):
    resp = await client.get("/api/options/tickers")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_ticker_not_found(client):
    resp = await client.get("/api/options/tickers/NONEXISTENT")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Ticker not found"


@pytest.mark.asyncio
async def test_get_ticker_after_insert(client, db_session):
    from app.modules.options_data.models import Ticker
    ticker = Ticker(symbol="AAPL", type="equity", name="Apple Inc.")
    db_session.add(ticker)
    await db_session.commit()

    resp = await client.get("/api/options/tickers/AAPL")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["type"] == "equity"
    assert data["name"] == "Apple Inc."


@pytest.mark.asyncio
async def test_list_tickers_after_insert(client, db_session):
    from app.modules.options_data.models import Ticker
    for sym in ["AAPL", "MSFT", "TSLA"]:
        db_session.add(Ticker(symbol=sym, type="equity"))
    await db_session.commit()

    resp = await client.get("/api/options/tickers")
    assert resp.status_code == 200
    tickers = resp.json()
    assert len(tickers) == 3
    # Should be sorted by symbol
    assert [t["symbol"] for t in tickers] == ["AAPL", "MSFT", "TSLA"]


@pytest.mark.asyncio
async def test_get_chain_not_found(client):
    resp = await client.get("/api/options/chain/NONEXISTENT")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_chain_empty(client, db_session):
    from app.modules.options_data.models import Ticker
    db_session.add(Ticker(symbol="AAPL", type="equity"))
    await db_session.commit()

    resp = await client.get("/api/options/chain/AAPL")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_chain_with_contracts(client, db_session):
    from app.modules.options_data.models import Ticker, OptionsContract
    from datetime import date

    ticker = Ticker(symbol="AAPL", type="equity")
    db_session.add(ticker)
    await db_session.flush()

    for strike, opt_type in [(180, "call"), (190, "call"), (190, "put")]:
        db_session.add(OptionsContract(
            ticker_id=ticker.id,
            occ_symbol=f"AAPL250321{opt_type[0].upper()}{strike:08d}",
            expiration_date=date(2025, 3, 21),
            strike=strike,
            option_type=opt_type,
        ))
    await db_session.commit()

    resp = await client.get("/api/options/chain/AAPL")
    assert resp.status_code == 200
    contracts = resp.json()
    assert len(contracts) == 3


@pytest.mark.asyncio
async def test_get_chain_filters_by_type(client, db_session):
    from app.modules.options_data.models import Ticker, OptionsContract
    from datetime import date

    ticker = Ticker(symbol="AAPL", type="equity")
    db_session.add(ticker)
    await db_session.flush()

    db_session.add(OptionsContract(
        ticker_id=ticker.id, occ_symbol="AAPL250321C00190000",
        expiration_date=date(2025, 3, 21), strike=190, option_type="call",
    ))
    db_session.add(OptionsContract(
        ticker_id=ticker.id, occ_symbol="AAPL250321P00190000",
        expiration_date=date(2025, 3, 21), strike=190, option_type="put",
    ))
    await db_session.commit()

    resp = await client.get("/api/options/chain/AAPL?option_type=call")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["option_type"] == "call"


@pytest.mark.asyncio
async def test_get_contract_not_found(client):
    resp = await client.get("/api/options/contracts/NONEXISTENT")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_contract_found(client, db_session):
    from app.modules.options_data.models import Ticker, OptionsContract
    from datetime import date

    ticker = Ticker(symbol="AAPL", type="equity")
    db_session.add(ticker)
    await db_session.flush()

    db_session.add(OptionsContract(
        ticker_id=ticker.id,
        occ_symbol="AAPL250321C00190000",
        expiration_date=date(2025, 3, 21),
        strike=190.0,
        option_type="call",
    ))
    await db_session.commit()

    resp = await client.get("/api/options/contracts/AAPL250321C00190000")
    assert resp.status_code == 200
    assert resp.json()["occ_symbol"] == "AAPL250321C00190000"
    assert resp.json()["strike"] == 190.0


@pytest.mark.asyncio
async def test_data_sources_list(client):
    resp = await client.get("/api/data-sources/")
    assert resp.status_code == 200
    sources = resp.json()
    assert len(sources) == 4
    names = {s["name"] for s in sources}
    assert names == {"polygon", "ibkr", "yahoo", "cboe"}


@pytest.mark.asyncio
async def test_ingestion_jobs_empty(client):
    resp = await client.get("/api/ingestion/jobs")
    assert resp.status_code == 200
    assert resp.json() == []
