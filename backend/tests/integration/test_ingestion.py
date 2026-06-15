import pytest
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch

from app.modules.data_sources.base import (
    NormalizedContract,
    NormalizedSnapshot,
    NormalizedUnderlyingBar,
    OptionType,
)
from app.modules.ingestion.service import run_ingestion, IngestionResult
from app.modules.ingestion.models import IngestionJob
from app.modules.options_data.models import OptionsContract, OptionsSnapshot, Ticker, UnderlyingBar
from sqlalchemy import select


def _mock_adapter(
    name="test_source",
    contracts=None,
    snapshots=None,
    underlying=None,
):
    adapter = AsyncMock()
    adapter.name = name
    adapter.fetch_options_chain.return_value = contracts or []
    adapter.fetch_snapshots.return_value = snapshots or []
    adapter.fetch_underlying_bar.return_value = underlying
    adapter.health_check.return_value = True
    return adapter


@pytest.mark.asyncio
async def test_ingestion_with_no_adapters(db_session):
    with patch("app.modules.ingestion.service.get_all_adapters", return_value=[]):
        results = await run_ingestion(db_session, symbols=["AAPL"])
    assert results == []


@pytest.mark.asyncio
async def test_ingestion_upserts_contracts(db_session):
    adapter = _mock_adapter(
        contracts=[
            NormalizedContract(
                occ_symbol="TEST250321C100",
                underlying_symbol="TEST",
                expiration_date=date(2025, 3, 21),
                strike=100.0,
                option_type=OptionType.CALL,
            ),
            NormalizedContract(
                occ_symbol="TEST250321P100",
                underlying_symbol="TEST",
                expiration_date=date(2025, 3, 21),
                strike=100.0,
                option_type=OptionType.PUT,
            ),
        ],
    )

    with patch("app.modules.ingestion.service.get_all_adapters", return_value=[adapter]):
        results = await run_ingestion(db_session, symbols=["TEST"])

    assert len(results) == 1
    assert results[0].contracts_upserted == 2

    # Verify ticker was created
    ticker = (await db_session.execute(
        select(Ticker).where(Ticker.symbol == "TEST")
    )).scalar_one_or_none()
    assert ticker is not None

    # Verify contracts were created
    contracts = (await db_session.execute(
        select(OptionsContract).where(OptionsContract.ticker_id == ticker.id)
    )).scalars().all()
    assert len(contracts) == 2


@pytest.mark.asyncio
async def test_ingestion_upserts_snapshots(db_session):
    adapter = _mock_adapter(
        contracts=[
            NormalizedContract(
                occ_symbol="TEST250321C100",
                underlying_symbol="TEST",
                expiration_date=date(2025, 3, 21),
                strike=100.0,
                option_type=OptionType.CALL,
            ),
        ],
        snapshots=[
            NormalizedSnapshot(
                occ_symbol="TEST250321C100",
                underlying_symbol="TEST",
                timestamp=datetime.now(timezone.utc),
                bid=2.10,
                ask=2.20,
                last=2.15,
                volume=1500,
                implied_volatility=0.32,
                delta=0.54,
                gamma=0.03,
                theta=-0.05,
                vega=0.15,
            ),
        ],
    )

    with patch("app.modules.ingestion.service.get_all_adapters", return_value=[adapter]):
        results = await run_ingestion(db_session, symbols=["TEST"])

    assert results[0].snapshots_upserted == 1

    # Verify snapshot was created
    snapshots = (await db_session.execute(
        select(OptionsSnapshot)
    )).scalars().all()
    assert len(snapshots) == 1
    assert float(snapshots[0].delta) == 0.54


@pytest.mark.asyncio
async def test_ingestion_upserts_underlying_bar(db_session):
    adapter = _mock_adapter(
        underlying=NormalizedUnderlyingBar(
            symbol="TEST",
            timestamp=datetime.now(timezone.utc),
            interval="1d",
            open=100.0, high=105.0, low=99.0, close=103.0,
            volume=1_000_000,
        ),
    )

    with patch("app.modules.ingestion.service.get_all_adapters", return_value=[adapter]):
        results = await run_ingestion(db_session, symbols=["TEST"])

    assert results[0].bars_upserted == 1

    bars = (await db_session.execute(
        select(UnderlyingBar)
    )).scalars().all()
    assert len(bars) == 1
    assert float(bars[0].close) == 103.0


@pytest.mark.asyncio
async def test_ingestion_creates_job_record(db_session):
    adapter = _mock_adapter()

    with patch("app.modules.ingestion.service.get_all_adapters", return_value=[adapter]):
        await run_ingestion(db_session, symbols=["TEST"])

    jobs = (await db_session.execute(
        select(IngestionJob)
    )).scalars().all()
    assert len(jobs) == 1
    assert jobs[0].source == "test_source"
    assert jobs[0].status == "completed"
    assert jobs[0].symbols_requested == 1


@pytest.mark.asyncio
async def test_ingestion_handles_adapter_failure(db_session):
    adapter = _mock_adapter()
    adapter.fetch_options_chain.side_effect = Exception("Connection refused")

    with patch("app.modules.ingestion.service.get_all_adapters", return_value=[adapter]):
        results = await run_ingestion(db_session, symbols=["TEST"])

    # Adapter errors are caught per-symbol in _ingest_symbol, so no contracts are upserted
    assert results[0].contracts_upserted == 0
    assert results[0].snapshots_upserted == 0

    # Job should still be completed (per-symbol errors are caught internally)
    jobs = (await db_session.execute(
        select(IngestionJob)
    )).scalars().all()
    assert jobs[0].status == "completed"


@pytest.mark.asyncio
async def test_ingestion_filters_by_source(db_session):
    adapter_a = _mock_adapter(name="source_a", contracts=[
        NormalizedContract(
            occ_symbol="A250321C100", underlying_symbol="A",
            expiration_date=date(2025, 3, 21), strike=100.0,
            option_type=OptionType.CALL,
        ),
    ])
    adapter_b = _mock_adapter(name="source_b", contracts=[
        NormalizedContract(
            occ_symbol="B250321C100", underlying_symbol="B",
            expiration_date=date(2025, 3, 21), strike=100.0,
            option_type=OptionType.CALL,
        ),
    ])

    with patch("app.modules.ingestion.service.get_all_adapters", return_value=[adapter_a, adapter_b]):
        results = await run_ingestion(db_session, symbols=["TEST"], sources=["source_a"])

    assert len(results) == 1
    assert results[0].source == "source_a"
    adapter_b.fetch_options_chain.assert_not_called()


@pytest.mark.asyncio
async def test_ingestion_idempotent_contracts(db_session):
    adapter = _mock_adapter(
        contracts=[
            NormalizedContract(
                occ_symbol="TEST250321C100",
                underlying_symbol="TEST",
                expiration_date=date(2025, 3, 21),
                strike=100.0,
                option_type=OptionType.CALL,
            ),
        ],
    )

    with patch("app.modules.ingestion.service.get_all_adapters", return_value=[adapter]):
        await run_ingestion(db_session, symbols=["TEST"])
        await run_ingestion(db_session, symbols=["TEST"])

    contracts = (await db_session.execute(
        select(OptionsContract)
    )).scalars().all()
    # Should only have 1 contract, not 2
    assert len(contracts) == 1


@pytest.mark.asyncio
async def test_ingestion_via_api(client, db_session):
    adapter = _mock_adapter(
        contracts=[
            NormalizedContract(
                occ_symbol="TEST250321C100",
                underlying_symbol="TEST",
                expiration_date=date(2025, 3, 21),
                strike=100.0,
                option_type=OptionType.CALL,
            ),
        ],
    )

    with patch("app.modules.ingestion.service.get_all_adapters", return_value=[adapter]):
        resp = await client.post("/api/ingestion/run", json={
            "symbols": ["TEST"],
            "sources": ["test_source"],
        })

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["contracts_upserted"] == 1


@pytest.mark.asyncio
async def test_ingestion_jobs_list_via_api(client, db_session):
    # Create a job record directly
    job = IngestionJob(
        source="polygon",
        status="completed",
        symbols_requested=5,
        contracts_upserted=10,
    )
    db_session.add(job)
    await db_session.commit()

    resp = await client.get("/api/ingestion/jobs")
    assert resp.status_code == 200
    jobs = resp.json()
    assert len(jobs) == 1
    assert jobs[0]["source"] == "polygon"
