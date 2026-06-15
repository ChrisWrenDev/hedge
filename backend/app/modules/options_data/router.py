from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.modules.options_data.models import OptionsContract, Ticker
from app.modules.options_data.schemas import ChainQuery, ContractResponse, TickerResponse

router = APIRouter(prefix="/options", tags=["options"])


@router.get("/tickers", response_model=list[TickerResponse])
async def list_tickers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticker).order_by(Ticker.symbol))
    return list(result.scalars().all())


@router.get("/tickers/{symbol}", response_model=TickerResponse)
async def get_ticker(symbol: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticker).where(Ticker.symbol == symbol.upper()))
    ticker = result.scalar_one_or_none()
    if not ticker:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return ticker


@router.get("/chain/{symbol}", response_model=list[ContractResponse])
async def get_chain(
    symbol: str,
    expiration: date | None = None,
    option_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    ticker_result = await db.execute(
        select(Ticker).where(Ticker.symbol == symbol.upper())
    )
    ticker = ticker_result.scalar_one_or_none()
    if not ticker:
        raise HTTPException(status_code=404, detail="Ticker not found")

    query = (
        select(OptionsContract)
        .where(
            OptionsContract.ticker_id == ticker.id,
            OptionsContract.active == True,
        )
        .options(selectinload(OptionsContract.snapshots))
    )

    if expiration:
        query = query.where(OptionsContract.expiration_date == expiration)
    if option_type:
        query = query.where(OptionsContract.option_type == option_type)

    query = query.order_by(OptionsContract.strike)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/contracts/{occ_symbol}", response_model=ContractResponse)
async def get_contract(occ_symbol: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(OptionsContract).where(OptionsContract.occ_symbol == occ_symbol)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract
