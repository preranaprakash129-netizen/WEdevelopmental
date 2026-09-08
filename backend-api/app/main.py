import os
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SIH26091 backend-api", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Downstream service base URLs. backend-api is the only service allowed to call
# these directly (see docs/api-contract.md > Orchestration). Not yet wired up —
# each route below returns a stub payload matching the contract until the
# corresponding service is ready to be proxied to.
FEASIBILITY_URL = os.getenv("FEASIBILITY_URL", "http://localhost:8001")
CALCULATOR_URL = os.getenv("CALCULATOR_URL", "http://localhost:8002")
ESS_SCORING_URL = os.getenv("ESS_SCORING_URL", "http://localhost:8003")
ADVISORY_LLM_URL = os.getenv("ADVISORY_LLM_URL", "http://localhost:8004")


def _request_id() -> str:
    return str(uuid.uuid4())


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/feasibility")
def feasibility(payload: dict):
    return {
        "request_id": _request_id(),
        "market_reach": {"estimated_customers": 1200, "radius_km": 3.5},
        "competitor_list": [
            {"name": "Shree Dairy", "category": "dairy", "distance_km": 1.2},
            {"name": "Gopal Milk Center", "category": "dairy", "distance_km": 2.8},
        ],
        "swot": {
            "strengths": ["Low local competition density", "Steady demand for milk products"],
            "weaknesses": ["High cold-chain setup cost"],
            "opportunities": ["Government dairy subsidy schemes available"],
            "threats": ["Seasonal demand fluctuation"],
        },
        "pricing_bands": {"low": 40, "median": 55, "high": 70},
        "feasibility_score": 72.5,
        "confidence_range": {"low": 64.0, "high": 79.0},
    }


@app.post("/api/calculator")
def calculator(payload: dict):
    return {
        "request_id": _request_id(),
        "project_cost": 200000,
        "scheme_selected": {"name": "PMEGP", "subsidy_percent": 25},
        "loan_amount": 150000,
        "emi_schedule": [
            {
                "month": 1,
                "emi": 4200,
                "principal_component": 3100,
                "interest_component": 1100,
                "outstanding_balance": 146900,
            },
            {
                "month": 2,
                "emi": 4200,
                "principal_component": 3140,
                "interest_component": 1060,
                "outstanding_balance": 143760,
            },
        ],
        "moratorium": {"months": 6, "reason": "PMEGP standard moratorium for dairy category"},
        "working_capital": 25000,
    }


@app.post("/api/ess-score")
def ess_score(payload: dict):
    return {
        "request_id": _request_id(),
        "ess_score": 61.0,
        "sub_scores": {
            "financial_health": 55.0,
            "market_stability": 70.0,
            "operational_maturity": 58.0,
            "growth_potential": 61.0,
        },
        "attribution": [
            {"feature": "monthly_revenue", "impact": 8.2},
            {"feature": "years_operating", "impact": -3.1},
            {"feature": "has_bank_account", "impact": 2.4},
        ],
        "top_improvement_action": {
            "action": "Open a dedicated business bank account to formalize cash flow tracking",
            "expected_score_delta": 4.5,
        },
    }


@app.post("/api/advisory-chat")
def advisory_chat(payload: dict):
    return {
        "request_id": _request_id(),
        "response_text": "PMEGP ke liye aap apne zile ke KVIC/DIC office mein online apply kar sakte hain...",
        "cited_sources": [
            {
                "scheme": "PMEGP",
                "document": "PMEGP Guidelines 2023",
                "url": "https://kviconline.gov.in/pmegp",
            }
        ],
        "detected_language": "hi",
    }
