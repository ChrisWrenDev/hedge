import uuid
from datetime import date, datetime

from pydantic import BaseModel


class TickerCreate(BaseModel):
    symbol: str
    name: str | None = None
    type: str
    exchange: str | None = None
    sector: str | None = None


class TickerResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    name: str | None
    type: str
    exchange: str | None
    sector: str | None
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ContractCreate(BaseModel):
    occ_symbol: str
    underlying_symbol: str
    expiration_date: date
    strike: float
    option_type: str
    multiplier: int = 100


class ContractResponse(BaseModel):
    id: uuid.UUID
    ticker_id: uuid.UUID
    occ_symbol: str
    expiration_date: date
    strike: float
    option_type: str
    multiplier: int
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SnapshotResponse(BaseModel):
    id: uuid.UUID
    contract_id: uuid.UUID
    timestamp: datetime
    bid: float | None
    ask: float | None
    last: float | None
    volume: int | None
    open_interest: int | None
    implied_volatility: float | None
    delta: float | None
    gamma: float | None
    theta: float | None
    vega: float | None
    rho: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChainQuery(BaseModel):
    symbol: str
    expiration_date: date | None = None
    option_type: str | None = None
