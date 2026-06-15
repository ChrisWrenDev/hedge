import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.rules.models import RuleAuditLog, RuleDefinition, RuleTrigger
from app.modules.rules.schemas import (
    RuleAuditLogResponse,
    RuleDefinitionCreate,
    RuleDefinitionResponse,
    RuleTriggerResponse,
)

router = APIRouter(prefix="/api/rules", tags=["rules"])


@router.post("/", response_model=RuleDefinitionResponse, status_code=201)
async def create_rule(payload: RuleDefinitionCreate, db: AsyncSession = Depends(get_db)):
    rd = RuleDefinition(
        name=payload.name,
        rule_type=payload.rule_type,
        module_path=payload.module_path,
        config=payload.config,
        active=payload.active,
        priority=payload.priority,
    )
    db.add(rd)
    await db.commit()
    await db.refresh(rd)
    return rd


@router.get("/", response_model=list[RuleDefinitionResponse])
async def list_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RuleDefinition))
    return list(result.scalars().all())


@router.patch("/{rule_id}/toggle", response_model=RuleDefinitionResponse)
async def toggle_rule(rule_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RuleDefinition).where(RuleDefinition.id == rule_id))
    rd = result.scalar_one_or_none()
    if not rd:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Rule not found")
    rd.active = not rd.active
    await db.commit()
    await db.refresh(rd)
    return rd


@router.get("/triggers", response_model=list[RuleTriggerResponse])
async def list_triggers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RuleTrigger))
    return list(result.scalars().all())


@router.get("/audit", response_model=list[RuleAuditLogResponse])
async def list_audit_log(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RuleAuditLog))
    return list(result.scalars().all())
