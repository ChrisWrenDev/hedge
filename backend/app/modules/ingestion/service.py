import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.data_sources.base import (
    BaseDataAdapter,
    FetchResult,
    NormalizedContract,
    NormalizedSnapshot,
    NormalizedUnderlyingBar,
)
from app.modules.data_sources.cboe import CBOEAdapter
from app.modules.data_sources.ibkr import IBKRAdapter
from app.modules.data_sources.polygon import PolygonAdapter
from app.modules.data_sources.yahoo import YahooAdapter
from app.modules.ingestion.models import IngestionJob
from app.modules.options_data.models import (
    OptionsContract,
    OptionsSnapshot,
    Ticker,
    UnderlyingBar,
)
from app.modules.options_data.service import get_ticker_by_symbol

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    job_id: str | None = None
    source: str = ""
    contracts_upserted: int = 0
    snapshots_upserted: int = 0
    bars_upserted: int = 0
    errors: list[str] | None = None


def get_all_adapters() -> list[BaseDataAdapter]:
    return [PolygonAdapter(), IBKRAdapter(), YahooAdapter(), CBOEAdapter()]


async def run_ingestion(
    db: AsyncSession,
    symbols: list[str],
    sources: list[str] | None = None,
) -> list[IngestionResult]:
    adapters = get_all_adapters()
    if sources:
        adapters = [a for a in adapters if a.name in sources]

    results = []
    for adapter in adapters:
        result = await _ingest_source(db, adapter, symbols)
        results.append(result)

    return results


async def _ingest_source(
    db: AsyncSession,
    adapter: BaseDataAdapter,
    symbols: list[str],
) -> IngestionResult:
    job = IngestionJob(
        source=adapter.name,
        status="running",
        symbols_requested=len(symbols),
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.flush()

    result = IngestionResult(job_id=str(job.id), source=adapter.name)

    try:
        for symbol in symbols:
            try:
                await _ingest_symbol(db, adapter, symbol, result)
            except Exception as e:
                error_msg = f"{adapter.name}:{symbol} — {e}"
                logger.error(error_msg)
                if result.errors is None:
                    result.errors = []
                result.errors.append(error_msg)

        job.status = "completed"
        job.contracts_upserted = result.contracts_upserted
        job.snapshots_upserted = result.snapshots_upserted
        job.bars_upserted = result.bars_upserted
        job.errors = result.errors
        job.completed_at = datetime.now(timezone.utc)
        await db.commit()

    except Exception as e:
        job.status = "failed"
        job.errors = [str(e)]
        job.completed_at = datetime.now(timezone.utc)
        await db.commit()
        result.errors = [str(e)]

    return result


async def _ingest_symbol(
    db: AsyncSession,
    adapter: BaseDataAdapter,
    symbol: str,
    result: IngestionResult,
) -> None:
    symbol = symbol.upper()

    # Fetch contracts
    try:
        contracts = await adapter.fetch_options_chain(symbol)
    except Exception:
        contracts = []

    # Fetch snapshots
    try:
        snapshots = await adapter.fetch_snapshots(symbol)
    except Exception:
        snapshots = []

    # Fetch underlying bar
    try:
        underlying = await adapter.fetch_underlying_bar(symbol)
    except Exception:
        underlying = None

    # Upsert contracts
    snapshot_map = {s.occ_symbol: s for s in snapshots}
    for contract_data in contracts:
        await _upsert_contract(db, contract_data, snapshot_map, result)

    # Upsert underlying bar
    if underlying:
        await _upsert_underlying_bar(db, symbol, underlying, result)


async def _upsert_contract(
    db: AsyncSession,
    contract_data: NormalizedContract,
    snapshot_map: dict[str, NormalizedSnapshot],
    result: IngestionResult,
) -> None:
    # Find or create ticker
    ticker = await get_ticker_by_symbol(db, contract_data.underlying_symbol)
    if not ticker:
        ticker = Ticker(
            symbol=contract_data.underlying_symbol,
            type="equity",
        )
        db.add(ticker)
        await db.flush()

    # Find existing contract
    existing = await db.execute(
        select(OptionsContract).where(
            OptionsContract.occ_symbol == contract_data.occ_symbol
        )
    )
    contract = existing.scalar_one_or_none()

    if not contract:
        contract = OptionsContract(
            ticker_id=ticker.id,
            occ_symbol=contract_data.occ_symbol,
            expiration_date=contract_data.expiration_date,
            strike=contract_data.strike,
            option_type=contract_data.option_type.value,
            multiplier=contract_data.multiplier,
        )
        db.add(contract)
        await db.flush()
        result.contracts_upserted += 1

    # Upsert snapshot if available
    snapshot_data = snapshot_map.get(contract_data.occ_symbol)
    if snapshot_data:
        await _upsert_snapshot(db, contract.id, snapshot_data, result)


async def _upsert_snapshot(
    db: AsyncSession,
    contract_id,
    snapshot_data: NormalizedSnapshot,
    result: IngestionResult,
) -> None:
    # Check if recent snapshot exists (within 5 minutes)
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    existing = await db.execute(
        select(OptionsSnapshot).where(
            OptionsSnapshot.contract_id == contract_id,
            OptionsSnapshot.timestamp >= cutoff,
        )
    )
    if existing.scalar_one_or_none():
        return

    snapshot = OptionsSnapshot(
        contract_id=contract_id,
        timestamp=snapshot_data.timestamp,
        bid=snapshot_data.bid,
        ask=snapshot_data.ask,
        last=snapshot_data.last,
        volume=snapshot_data.volume,
        open_interest=snapshot_data.open_interest,
        implied_volatility=snapshot_data.implied_volatility,
        delta=snapshot_data.delta,
        gamma=snapshot_data.gamma,
        theta=snapshot_data.theta,
        vega=snapshot_data.vega,
        rho=snapshot_data.rho,
    )
    db.add(snapshot)
    result.snapshots_upserted += 1


async def _upsert_underlying_bar(
    db: AsyncSession,
    symbol: str,
    bar_data: NormalizedUnderlyingBar,
    result: IngestionResult,
) -> None:
    ticker = await get_ticker_by_symbol(db, symbol)
    if not ticker:
        ticker = Ticker(symbol=symbol, type="equity")
        db.add(ticker)
        await db.flush()

    # Check if bar already exists for this timestamp
    existing = await db.execute(
        select(UnderlyingBar).where(
            UnderlyingBar.ticker_id == ticker.id,
            UnderlyingBar.timestamp == bar_data.timestamp,
            UnderlyingBar.interval == bar_data.interval,
        )
    )
    if existing.scalar_one_or_none():
        return

    bar = UnderlyingBar(
        ticker_id=ticker.id,
        timestamp=bar_data.timestamp,
        interval=bar_data.interval,
        open=bar_data.open,
        high=bar_data.high,
        low=bar_data.low,
        close=bar_data.close,
        volume=bar_data.volume,
    )
    db.add(bar)
    result.bars_upserted += 1
