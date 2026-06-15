import pytest
from datetime import date, datetime, timezone

from app.modules.options_data.models import (
    OptionsContract,
    OptionsSnapshot,
    Ticker,
    UnderlyingBar,
)
from app.modules.options_data.service import (
    get_or_create_ticker,
    get_ticker_by_symbol,
    get_options_chain,
    get_contract_by_occ,
    get_latest_snapshot,
    get_latest_underlying_bar,
    upsert_ticker,
)


@pytest.mark.asyncio
async def test_create_ticker(db_session):
    ticker = await get_or_create_ticker(db_session, "AAPL", "equity", "Apple Inc.")
    assert ticker.symbol == "AAPL"
    assert ticker.type == "equity"
    assert ticker.name == "Apple Inc."
    assert ticker.id is not None


@pytest.mark.asyncio
async def test_get_existing_ticker(db_session):
    await get_or_create_ticker(db_session, "AAPL", "equity")
    found = await get_ticker_by_symbol(db_session, "AAPL")
    assert found is not None
    assert found.symbol == "AAPL"


@pytest.mark.asyncio
async def test_get_nonexistent_ticker(db_session):
    result = await get_ticker_by_symbol(db_session, "NONEXISTENT")
    assert result is None


@pytest.mark.asyncio
async def test_get_or_create_does_not_duplicate(db_session):
    t1 = await get_or_create_ticker(db_session, "AAPL", "equity")
    t2 = await get_or_create_ticker(db_session, "AAPL", "equity")
    assert t1.id == t2.id


@pytest.mark.asyncio
async def test_upsert_ticker_creates_new(db_session):
    ticker = await upsert_ticker(db_session, "TSLA", "equity", "Tesla")
    assert ticker.symbol == "TSLA"


@pytest.mark.asyncio
async def test_upsert_ticker_returns_existing(db_session):
    t1 = await upsert_ticker(db_session, "TSLA", "equity", "Tesla")
    t2 = await upsert_ticker(db_session, "TSLA", "equity", "Tesla Inc.")
    assert t1.id == t2.id
    assert t2.name == "Tesla"  # original name preserved (not updated)


@pytest.mark.asyncio
async def test_create_contract(db_session):
    ticker = await get_or_create_ticker(db_session, "AAPL", "equity")
    contract = OptionsContract(
        ticker_id=ticker.id,
        occ_symbol="AAPL250321C00190000",
        expiration_date=date(2025, 3, 21),
        strike=190.0,
        option_type="call",
    )
    db_session.add(contract)
    await db_session.flush()

    assert contract.id is not None
    assert contract.ticker_id == ticker.id


@pytest.mark.asyncio
async def test_get_options_chain(db_session):
    ticker = await get_or_create_ticker(db_session, "AAPL", "equity")

    for strike, opt_type in [(180, "call"), (190, "call"), (190, "put"), (200, "call")]:
        db_session.add(OptionsContract(
            ticker_id=ticker.id,
            occ_symbol=f"AAPL250321{opt_type[0].upper()}{strike:08d}",
            expiration_date=date(2025, 3, 21),
            strike=strike,
            option_type=opt_type,
        ))
    await db_session.flush()

    chain = await get_options_chain(db_session, "AAPL")
    assert len(chain) == 4
    # Should be ordered by strike
    assert chain[0].strike == 180


@pytest.mark.asyncio
async def test_get_options_chain_filters_by_type(db_session):
    ticker = await get_or_create_ticker(db_session, "AAPL", "equity")
    db_session.add(OptionsContract(
        ticker_id=ticker.id, occ_symbol="AAPL250321C00190000",
        expiration_date=date(2025, 3, 21), strike=190, option_type="call",
    ))
    db_session.add(OptionsContract(
        ticker_id=ticker.id, occ_symbol="AAPL250321P00190000",
        expiration_date=date(2025, 3, 21), strike=190, option_type="put",
    ))
    await db_session.flush()

    calls = await get_options_chain(db_session, "AAPL", option_type="call")
    assert len(calls) == 1
    assert calls[0].option_type == "call"

    puts = await get_options_chain(db_session, "AAPL", option_type="put")
    assert len(puts) == 1
    assert puts[0].option_type == "put"


@pytest.mark.asyncio
async def test_get_options_chain_filters_by_expiration(db_session):
    ticker = await get_or_create_ticker(db_session, "AAPL", "equity")
    db_session.add(OptionsContract(
        ticker_id=ticker.id, occ_symbol="AAPL250321C00190000",
        expiration_date=date(2025, 3, 21), strike=190, option_type="call",
    ))
    db_session.add(OptionsContract(
        ticker_id=ticker.id, occ_symbol="AAPL250620C00190000",
        expiration_date=date(2025, 6, 20), strike=190, option_type="call",
    ))
    await db_session.flush()

    mar = await get_options_chain(db_session, "AAPL", expiration_date=date(2025, 3, 21))
    assert len(mar) == 1
    assert mar[0].expiration_date == date(2025, 3, 21)


@pytest.mark.asyncio
async def test_get_options_chain_nonexistent_ticker(db_session):
    chain = await get_options_chain(db_session, "NONEXISTENT")
    assert chain == []


@pytest.mark.asyncio
async def test_get_contract_by_occ(db_session):
    ticker = await get_or_create_ticker(db_session, "AAPL", "equity")
    contract = OptionsContract(
        ticker_id=ticker.id,
        occ_symbol="AAPL250321C00190000",
        expiration_date=date(2025, 3, 21),
        strike=190.0,
        option_type="call",
    )
    db_session.add(contract)
    await db_session.flush()

    found = await get_contract_by_occ(db_session, "AAPL250321C00190000")
    assert found is not None
    assert found.strike == 190.0


@pytest.mark.asyncio
async def test_get_contract_by_occ_not_found(db_session):
    result = await get_contract_by_occ(db_session, "NONEXISTENT")
    assert result is None


@pytest.mark.asyncio
async def test_get_latest_snapshot(db_session):
    ticker = await get_or_create_ticker(db_session, "AAPL", "equity")
    contract = OptionsContract(
        ticker_id=ticker.id,
        occ_symbol="AAPL250321C00190000",
        expiration_date=date(2025, 3, 21),
        strike=190.0,
        option_type="call",
    )
    db_session.add(contract)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    for i, price in enumerate([1.0, 2.0, 3.0]):
        snap = OptionsSnapshot(
            contract_id=contract.id,
            timestamp=now,
            bid=price,
            ask=price + 0.05,
            last=price,
        )
        snap.timestamp = datetime(
            now.year, now.month, now.day,
            now.hour, now.minute, now.second,
            tzinfo=timezone.utc,
        )
        # Make each snapshot slightly later
        from datetime import timedelta
        snap.timestamp = now + timedelta(seconds=i * 60)
        db_session.add(snap)
    await db_session.flush()

    latest = await get_latest_snapshot(db_session, contract.id)
    assert latest is not None
    assert latest.bid == 3.0


@pytest.mark.asyncio
async def test_get_latest_underlying_bar(db_session):
    ticker = await get_or_create_ticker(db_session, "AAPL", "equity")
    now = datetime.now(timezone.utc)

    from datetime import timedelta
    for i, close in enumerate([180.0, 185.0]):
        bar = UnderlyingBar(
            ticker_id=ticker.id,
            timestamp=now + timedelta(days=i),
            interval="1d",
            open=close - 1, high=close + 2, low=close - 2, close=close,
            volume=50_000_000,
        )
        db_session.add(bar)
    await db_session.flush()

    latest = await get_latest_underlying_bar(db_session, ticker.id)
    assert latest is not None
    assert latest.close == 185.0


@pytest.mark.asyncio
async def test_snapshot_stored_with_greeks(db_session):
    ticker = await get_or_create_ticker(db_session, "AAPL", "equity")
    contract = OptionsContract(
        ticker_id=ticker.id,
        occ_symbol="AAPL250321C00190000",
        expiration_date=date(2025, 3, 21),
        strike=190.0,
        option_type="call",
    )
    db_session.add(contract)
    await db_session.flush()

    snap = OptionsSnapshot(
        contract_id=contract.id,
        timestamp=datetime.now(timezone.utc),
        bid=2.10,
        ask=2.20,
        last=2.15,
        volume=1500,
        open_interest=5000,
        implied_volatility=0.32,
        delta=0.54,
        gamma=0.03,
        theta=-0.05,
        vega=0.15,
        rho=0.02,
    )
    db_session.add(snap)
    await db_session.flush()

    latest = await get_latest_snapshot(db_session, contract.id)
    assert latest is not None
    assert latest.delta == 0.54
    assert latest.gamma == 0.03
    assert latest.implied_volatility == 0.32
