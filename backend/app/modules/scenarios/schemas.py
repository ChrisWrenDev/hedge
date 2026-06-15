import uuid
from datetime import datetime

from pydantic import BaseModel


class ScenarioTemplateCreate(BaseModel):
    name: str
    description: str | None = None
    parameters: dict | None = None


class ScenarioTemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    parameters: dict | None
    active: bool

    model_config = {"from_attributes": True}


class ScenarioRunResponse(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID
    status: str
    results: dict | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}
