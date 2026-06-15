from datetime import date

from pydantic import BaseModel


class ConvexityScoreRequest(BaseModel):
    gamma_per_theta: float
    vega_normalized: float
    iv_rank: float
    volume_oi_ratio: float
    dte: float


class ConvexityScoreResponse(BaseModel):
    score: float


class ConvexityRankingResponse(BaseModel):
    rank: int
    contract_id: str
    occ_symbol: str
    score: float
    gamma_per_theta: float
    iv_rank: float

    model_config = {"from_attributes": True}
