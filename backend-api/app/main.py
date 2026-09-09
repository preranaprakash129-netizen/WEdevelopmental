import os
import uuid

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="SIH26091 backend-api", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Downstream service base URLs. backend-api is the only service allowed to call
# these directly (see docs/api-contract.md > Orchestration). /api/feasibility now
# proxies to FEASIBILITY_URL; the other three routes still return stub payloads
# until their services are ready to be proxied to.
FEASIBILITY_URL = os.getenv("FEASIBILITY_URL", "http://localhost:8001")
CALCULATOR_URL = os.getenv("CALCULATOR_URL", "http://localhost:8002")
ESS_SCORING_URL = os.getenv("ESS_SCORING_URL", "http://localhost:8003")
ADVISORY_LLM_URL = os.getenv("ADVISORY_LLM_URL", "http://localhost:8004")

DOWNSTREAM_TIMEOUT_SECONDS = 10.0


def _request_id() -> str:
    return str(uuid.uuid4())


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/feasibility")
def feasibility(payload: dict):
    try:
        resp = httpx.post(
            f"{FEASIBILITY_URL}/feasibility", json=payload, timeout=DOWNSTREAM_TIMEOUT_SECONDS
        )
    except httpx.RequestError:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "feasibility_unavailable",
                    "message": "Could not reach the feasibility service",
                }
            },
        )
    return JSONResponse(status_code=resp.status_code, content=resp.json())


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
