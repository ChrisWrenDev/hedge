import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.scenarios.models import ScenarioRun, ScenarioTemplate
from app.modules.scenarios.schemas import (
    ScenarioTemplateCreate,
    ScenarioTemplateResponse,
    ScenarioRunResponse,
)
from app.modules.scenarios.service import run_scenario

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.post("/templates", response_model=ScenarioTemplateResponse, status_code=201)
async def create_template(payload: ScenarioTemplateCreate, db: AsyncSession = Depends(get_db)):
    t = ScenarioTemplate(
        name=payload.name,
        description=payload.description,
        parameters=payload.parameters,
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t


@router.get("/templates", response_model=list[ScenarioTemplateResponse])
async def list_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScenarioTemplate))
    return list(result.scalars().all())


@router.get("/templates/{template_id}", response_model=ScenarioTemplateResponse)
async def get_template(template_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ScenarioTemplate).where(ScenarioTemplate.id == template_id)
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return t


@router.post("/templates/{template_id}/run", response_model=ScenarioRunResponse)
async def create_run(template_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    run = await run_scenario(db, template_id)
    if not run:
        raise HTTPException(status_code=404, detail="Template not found")
    return run


@router.get("/runs", response_model=list[ScenarioRunResponse])
async def list_runs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScenarioRun))
    return list(result.scalars().all())
