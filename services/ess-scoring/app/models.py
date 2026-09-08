from typing import Optional

from pydantic import BaseModel, Field, model_validator


class ProfileData(BaseModel):
    category: str
    years_operating: float
    monthly_revenue: float
    employee_count: Optional[int] = None
    has_bank_account: bool


class ESSScoreRequest(BaseModel):
    business_id: Optional[str] = None
    profile_data: Optional[ProfileData] = None

    @model_validator(mode="after")
    def exactly_one_source(self) -> "ESSScoreRequest":
        if bool(self.business_id) == bool(self.profile_data):
            raise ValueError("Exactly one of business_id or profile_data is required")
        return self


class SubScores(BaseModel):
    financial_health: float = Field(ge=0, le=100)
    market_stability: float = Field(ge=0, le=100)
    operational_maturity: float = Field(ge=0, le=100)
    growth_potential: float = Field(ge=0, le=100)


class AttributionItem(BaseModel):
    feature: str
    impact: float


class TopImprovementAction(BaseModel):
    action: str
    expected_score_delta: float


class ESSScoreResponse(BaseModel):
    request_id: str
    ess_score: float = Field(ge=0, le=100)
    sub_scores: SubScores
    attribution: list[AttributionItem]
    top_improvement_action: TopImprovementAction


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody
