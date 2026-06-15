import uuid
from datetime import datetime

from pydantic import BaseModel


class AlertChannelCreate(BaseModel):
    name: str
    type: str
    config: dict | None = None


class AlertChannelResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    config: dict | None
    active: bool

    model_config = {"from_attributes": True}


class AlertSubscriptionCreate(BaseModel):
    channel_id: uuid.UUID
    rule_id: uuid.UUID


class AlertSubscriptionResponse(BaseModel):
    id: uuid.UUID
    channel_id: uuid.UUID
    rule_id: uuid.UUID
    active: bool

    model_config = {"from_attributes": True}


class AlertHistoryResponse(BaseModel):
    id: uuid.UUID
    channel_id: uuid.UUID
    rule_id: uuid.UUID
    subject: str | None
    body: str | None
    status: str
    sent_at: datetime | None = None

    model_config = {"from_attributes": True}
