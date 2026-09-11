"""Pydantic models mirroring `POST /advisory-chat` in docs/api-contract.md."""

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatContext(BaseModel):
    business_id: Optional[str] = None
    conversation_id: Optional[str] = None


class AdvisoryChatRequest(BaseModel):
    message: str = Field(min_length=1)
    # ISO 639-1. Omitted means "detect it for me" — see app/language.py.
    language: Optional[str] = None
    context: Optional[ChatContext] = None


class CitedSource(BaseModel):
    scheme: str
    document: str
    url: Optional[str] = None


class AdvisoryChatResponse(BaseModel):
    request_id: str
    response_text: str
    # Required by the contract but may be empty — an ungrounded answer returns []
    # rather than dropping the key.
    cited_sources: List[CitedSource]
    detected_language: str


class SchemeMatchRequest(BaseModel):
    """Mirrors the profile fields app/scheme_match.py's trained classifier expects."""

    category: str
    is_new_business: bool
    years_operating: int = Field(ge=0)
    gender: str  # "male" | "female"
    is_sc_st: bool
    location_type: str  # "urban" | "rural" | "semi-urban"
    annual_family_income: int = Field(ge=0)
    monthly_revenue: int = Field(ge=0)
    requested_amount: int = Field(gt=0)
    margin_capital: int = Field(ge=0)


class MatchBreakdown(BaseModel):
    """Four deterministic, rule-based 0-1 sub-scores behind `confidence` --
    powers the "AI Insights" breakdown chart on the frontend. See
    app/scheme_match.py's _match_breakdown for how each is computed."""

    category_fit: float
    loan_amount_fit: float
    eligibility_fit: float
    priority_boost_fit: float


class SchemeMatchResult(BaseModel):
    scheme: str
    display_name: str
    confidence: float
    why: List[str]
    url: str
    match_breakdown: MatchBreakdown
    improvement_tips: List[str]
    documents: List[str]
    apply_process: str


class SchemeMatchResponse(BaseModel):
    request_id: str
    results: List[SchemeMatchResult]
    model_feature_importance: dict
