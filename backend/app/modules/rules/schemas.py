import uuid
from datetime import datetime

from pydantic import BaseModel


class RuleDefinitionCreate(BaseModel):
    name: str
    rule_type: str
    module_path: str | None = None
    config: dict | None = None
    active: bool = True
    priority: int = 10


class RuleDefinitionResponse(BaseModel):
    id: uuid.UUID
    name: str
    rule_type: str
    module_path: str | None
    config: dict | None
    active: bool
    priority: int

    model_config = {"from_attributes": True}


class RuleTriggerResponse(BaseModel):
    id: uuid.UUID
    rule_id: uuid.UUID
    triggered_at: datetime
    context: dict | None
    action_taken: str | None

    model_config = {"from_attributes": True}


class RuleAuditLogResponse(BaseModel):
    id: uuid.UUID
    rule_id: uuid.UUID
    action: str
    details: dict | None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
