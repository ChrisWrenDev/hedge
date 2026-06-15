from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.convexity.engine import compute_score
from app.modules.convexity.schemas import ConvexityScoreResponse
from app.modules.convexity.service import get_top_convexity_scores

router = APIRouter(prefix="/convexity", tags=["convexity"])


@router.get("/score", response_model=ConvexityScoreResponse)
async def score(
    gamma_per_theta: float = Query(...),
    vega_normalized: float = Query(...),
    iv_rank: float = Query(...),
    volume_oi_ratio: float = Query(...),
    dte: float = Query(...),
):
    score = compute_score(
        gamma_per_theta=gamma_per_theta,
        vega_normalized=vega_normalized,
        iv_rank=iv_rank,
        volume_oi_ratio=volume_oi_ratio,
        dte=dte,
    )
    return ConvexityScoreResponse(score=score)


@router.get("/top")
async def top_scores(
    limit: int = Query(20, ge=1, le=100),
    scoring_date: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    if scoring_date is None:
        scoring_date = date.today()

    scores = await get_top_convexity_scores(db, scoring_date, limit=limit)
    return [
        {
            "contract_id": str(s.contract_id),
            "occ_symbol": s.contract.occ_symbol if s.contract else None,
            "score": float(s.score),
            "gamma_per_theta": float(s.gamma_per_theta),
            "iv_rank": float(s.iv_rank),
        }
        for s in scores
    ]
