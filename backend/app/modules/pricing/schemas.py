from pydantic import BaseModel


class GreeksRequest(BaseModel):
    spot: float
    strike: float
    rate: float
    time_to_expiry: float
    iv: float
    option_type: str


class GreeksResponse(BaseModel):
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


class IVRequest(BaseModel):
    market_price: float
    spot: float
    strike: float
    rate: float
    time_to_expiry: float
    option_type: str


class IVResponse(BaseModel):
    implied_volatility: float


class PriceRequest(BaseModel):
    spot: float
    strike: float
    rate: float
    time_to_expiry: float
    iv: float
    option_type: str


class PriceResponse(BaseModel):
    price: float
