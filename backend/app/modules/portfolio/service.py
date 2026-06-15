import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.options_data.models import OptionsContract
from app.modules.pricing.models import GreeksSnapshot
from app.modules.portfolio.models import Portfolio, PortfolioGreeks, Position


async def aggregate_greeks(
    db: AsyncSession, portfolio_id: str | uuid.UUID
) -> PortfolioGreeks | None:
    if isinstance(portfolio_id, str):
        portfolio_id = uuid.UUID(portfolio_id)

    stmt = (
        select(Position)
        .where(Position.portfolio_id == portfolio_id)
    )
    result = await db.execute(stmt)
    positions = result.scalars().all()

    if not positions:
        return None

    net_delta = 0.0
    net_gamma = 0.0
    net_theta = 0.0
    net_vega = 0.0

    for pos in positions:
        greeks_stmt = (
            select(GreeksSnapshot)
            .where(GreeksSnapshot.contract_id == pos.contract_id)
            .order_by(GreeksSnapshot.timestamp.desc())
            .limit(1)
        )
        greeks_result = await db.execute(greeks_stmt)
        greeks = greeks_result.scalar_one_or_none()

        if greeks is None:
            continue

        multiplier = 100
        qty = pos.quantity
        net_delta += qty * (float(greeks.delta or 0)) * multiplier
        net_gamma += qty * (float(greeks.gamma or 0)) * multiplier
        net_theta += qty * (float(greeks.theta or 0)) * multiplier
        net_vega += qty * (float(greeks.vega or 0)) * multiplier

    greeks_record = PortfolioGreeks(
        portfolio_id=portfolio_id,
        timestamp=datetime.now(timezone.utc),
        net_delta=net_delta,
        net_gamma=net_gamma,
        net_theta=net_theta,
        net_vega=net_vega,
    )
    db.add(greeks_record)
    await db.flush()
    return greeks_record


async def get_portfolio_positions(
    db: AsyncSession, portfolio_id: str | uuid.UUID
) -> list[Position]:
    if isinstance(portfolio_id, str):
        portfolio_id = uuid.UUID(portfolio_id)

    stmt = (
        select(Position)
        .where(Position.portfolio_id == portfolio_id)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
