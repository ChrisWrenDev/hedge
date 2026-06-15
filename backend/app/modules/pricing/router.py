from fastapi import APIRouter, HTTPException

from app.modules.pricing.engine import (
    Greeks,
    black_scholes_price,
    calculate_greeks,
    calculate_iv,
)
from app.modules.pricing.schemas import GreeksResponse, IVResponse, PriceResponse

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/greeks", response_model=GreeksResponse)
async def get_greeks(
    spot: float,
    strike: float,
    rate: float,
    time_to_expiry: float,
    iv: float,
    option_type: str,
):
    try:
        greeks = calculate_greeks(spot, strike, rate, time_to_expiry, iv, option_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return greeks


@router.get("/iv", response_model=IVResponse)
async def get_iv(
    market_price: float,
    spot: float,
    strike: float,
    rate: float,
    time_to_expiry: float,
    option_type: str,
):
    try:
        iv = calculate_iv(market_price, spot, strike, rate, time_to_expiry, option_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return IVResponse(implied_volatility=iv)


@router.get("/price", response_model=PriceResponse)
async def get_price(
    spot: float,
    strike: float,
    rate: float,
    time_to_expiry: float,
    iv: float,
    option_type: str,
):
    try:
        price = black_scholes_price(spot, strike, rate, time_to_expiry, iv, option_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return PriceResponse(price=price)
