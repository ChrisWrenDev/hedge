import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.options_data.models import OptionsContract
from app.modules.portfolio.models import Portfolio, PortfolioGreeks, Position
from app.modules.portfolio.schemas import (
    PortfolioCreate,
    PortfolioResponse,
    PositionCreate,
    PositionResponse,
    PortfolioGreeksResponse,
)
from app.modules.portfolio.service import aggregate_greeks, get_portfolio_positions

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.post("/", response_model=PortfolioResponse, status_code=201)
async def create_portfolio(payload: PortfolioCreate, db: AsyncSession = Depends(get_db)):
    p = Portfolio(
        name=payload.name,
        description=payload.description,
        budget=payload.budget,
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


@router.get("/", response_model=list[PortfolioResponse])
async def list_portfolios(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Portfolio))
    return list(result.scalars().all())


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(portfolio_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return p


@router.post("/{portfolio_id}/positions", response_model=PositionResponse, status_code=201)
async def create_position(
    portfolio_id: uuid.UUID,
    payload: PositionCreate,
    db: AsyncSession = Depends(get_db),
):
    # verify portfolio exists
    result = await db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # find contract by OCC symbol
    result = await db.execute(
        select(OptionsContract).where(OptionsContract.occ_symbol == payload.contract_occ)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    pos = Position(
        portfolio_id=portfolio_id,
        contract_id=contract.id,
        quantity=payload.quantity,
        entry_price=payload.entry_price,
        entry_date=payload.entry_date,
    )
    db.add(pos)
    await db.commit()
    await db.refresh(pos)
    return pos


@router.get("/{portfolio_id}/positions", response_model=list[PositionResponse])
async def list_positions(portfolio_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await get_portfolio_positions(db, portfolio_id)


@router.get("/{portfolio_id}/greeks", response_model=PortfolioGreeksResponse)
async def portfolio_greeks(portfolio_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    greeks = await aggregate_greeks(db, portfolio_id)
    if not greeks:
        raise HTTPException(status_code=404, detail="No greeks data for this portfolio")
    return greeks
