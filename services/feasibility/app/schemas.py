"""Pydantic models mirroring `POST /feasibility` in docs/api-contract.md."""

from typing import List

from pydantic import BaseModel, Field


class FeasibilityRequest(BaseModel):
    location: str
    category: str
    margin_capital: float = Field(ge=0)


class MarketReach(BaseModel):
    estimated_customers: int
    radius_km: float


class Competitor(BaseModel):
    name: str
    category: str
    distance_km: float


class SWOT(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]


class PricingBands(BaseModel):
    low: float
    median: float
    high: float


class ConfidenceRange(BaseModel):
    low: float
    high: float


class FeasibilityResponse(BaseModel):
    request_id: str
    market_reach: MarketReach
    competitor_list: List[Competitor]
    swot: SWOT
    pricing_bands: PricingBands
    feasibility_score: float
    confidence_range: ConfidenceRange
