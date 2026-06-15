import uuid
from datetime import date, datetime

from pydantic import BaseModel


class PortfolioCreate(BaseModel):
    name: str
    description: str | None = None
    budget: float = 0


class PortfolioResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    budget: float
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class PositionCreate(BaseModel):
    contract_occ: str
    quantity: int
    entry_price: float
    entry_date: date


class PositionResponse(BaseModel):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    contract_id: uuid.UUID
    quantity: int
    entry_price: float
    entry_date: date
    current_price: float | None = None
    unrealized_pnl: float | None = None

    model_config = {"from_attributes": True}


class PortfolioGreeksResponse(BaseModel):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    timestamp: datetime
    net_delta: float
    net_gamma: float
    net_theta: float
    net_vega: float

    model_config = {"from_attributes": True}
