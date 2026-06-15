from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.convexity.models import ConvexityScore
from app.modules.options_data.models import OptionsContract


async def get_top_convexity_scores(
    db: AsyncSession,
    score_date: date,
    limit: int = 20,
) -> list[ConvexityScore]:
    """Get top convexity scores for a given date."""
    result = await db.execute(
        select(ConvexityScore)
        .where(ConvexityScore.score_date == score_date)
        .options(selectinload(ConvexityScore.contract))
        .order_by(ConvexityScore.score.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
