import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.options_data.models import (
    OptionsContract,
    OptionsSnapshot,
    Ticker,
    UnderlyingBar,
)


async def get_or_create_ticker(
    db: AsyncSession, symbol: str, ticker_type: str, name: str | None = None
) -> Ticker:
    result = await db.execute(select(Ticker).where(Ticker.symbol == symbol))
    ticker = result.scalar_one_or_none()
    if ticker:
        return ticker

    ticker = Ticker(symbol=symbol, type=ticker_type, name=name)
    db.add(ticker)
    await db.flush()
    return ticker


async def get_ticker_by_symbol(db: AsyncSession, symbol: str) -> Ticker | None:
    result = await db.execute(select(Ticker).where(Ticker.symbol == symbol))
    return result.scalar_one_or_none()


async def get_options_chain(
    db: AsyncSession,
    symbol: str,
    expiration_date: date | None = None,
    option_type: str | None = None,
) -> list[OptionsContract]:
    ticker = await get_ticker_by_symbol(db, symbol)
    if not ticker:
        return []

    query = (
        select(OptionsContract)
        .where(OptionsContract.ticker_id == ticker.id, OptionsContract.active == True)
        .options(selectinload(OptionsContract.snapshots))
    )

    if expiration_date:
        query = query.where(OptionsContract.expiration_date == expiration_date)
    if option_type:
        query = query.where(OptionsContract.option_type == option_type)

    query = query.order_by(OptionsContract.strike)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_contract_by_occ(db: AsyncSession, occ_symbol: str) -> OptionsContract | None:
    result = await db.execute(
        select(OptionsContract).where(OptionsContract.occ_symbol == occ_symbol)
    )
    return result.scalar_one_or_none()


async def get_latest_snapshot(db: AsyncSession, contract_id: uuid.UUID) -> OptionsSnapshot | None:
    result = await db.execute(
        select(OptionsSnapshot)
        .where(OptionsSnapshot.contract_id == contract_id)
        .order_by(OptionsSnapshot.timestamp.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_latest_underlying_bar(
    db: AsyncSession, ticker_id: uuid.UUID
) -> UnderlyingBar | None:
    result = await db.execute(
        select(UnderlyingBar)
        .where(UnderlyingBar.ticker_id == ticker_id)
        .order_by(UnderlyingBar.timestamp.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def upsert_ticker(
    db: AsyncSession,
    symbol: str,
    ticker_type: str,
    name: str | None = None,
) -> Ticker:
    ticker = await get_ticker_by_symbol(db, symbol)
    if ticker:
        return ticker
    return await get_or_create_ticker(db, symbol, ticker_type, name)
