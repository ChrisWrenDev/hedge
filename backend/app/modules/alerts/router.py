import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.alerts.models import AlertChannel, AlertHistory, AlertSubscription
from app.modules.alerts.schemas import (
    AlertChannelCreate,
    AlertChannelResponse,
    AlertHistoryResponse,
    AlertSubscriptionCreate,
    AlertSubscriptionResponse,
)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.post("/channels", response_model=AlertChannelResponse, status_code=201)
async def create_channel(payload: AlertChannelCreate, db: AsyncSession = Depends(get_db)):
    ch = AlertChannel(
        name=payload.name,
        type=payload.type,
        config=payload.config,
    )
    db.add(ch)
    await db.commit()
    await db.refresh(ch)
    return ch


@router.get("/channels", response_model=list[AlertChannelResponse])
async def list_channels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertChannel))
    return list(result.scalars().all())


@router.post("/subscriptions", response_model=AlertSubscriptionResponse, status_code=201)
async def create_subscription(payload: AlertSubscriptionCreate, db: AsyncSession = Depends(get_db)):
    sub = AlertSubscription(
        channel_id=payload.channel_id,
        rule_id=payload.rule_id,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


@router.get("/subscriptions", response_model=list[AlertSubscriptionResponse])
async def list_subscriptions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertSubscription))
    return list(result.scalars().all())


@router.get("/history", response_model=list[AlertHistoryResponse])
async def list_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertHistory))
    return list(result.scalars().all())
