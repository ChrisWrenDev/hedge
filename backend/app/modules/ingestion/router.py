import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.ingestion.models import IngestionJob
from app.modules.ingestion.service import run_ingestion

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


class IngestionRequest(BaseModel):
    symbols: list[str]
    sources: list[str] | None = None


class IngestionJobResponse(BaseModel):
    id: uuid.UUID
    source: str
    status: str
    symbols_requested: int
    contracts_upserted: int
    snapshots_upserted: int
    bars_upserted: int

    model_config = {"from_attributes": True}


@router.post("/run")
async def trigger_ingestion(
    request: IngestionRequest,
    db: AsyncSession = Depends(get_db),
):
    results = await run_ingestion(
        db,
        symbols=request.symbols,
        sources=request.sources,
    )
    return {
        "results": [
            {
                "source": r.source,
                "contracts_upserted": r.contracts_upserted,
                "snapshots_upserted": r.snapshots_upserted,
                "bars_upserted": r.bars_upserted,
                "errors": r.errors,
            }
            for r in results
        ]
    }


@router.get("/jobs", response_model=list[IngestionJobResponse])
async def list_jobs(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())
