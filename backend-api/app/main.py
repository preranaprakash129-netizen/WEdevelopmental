import os

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
# these directly (see docs/api-contract.md > Orchestration). All four routes now
# proxy to their respective services.
FEASIBILITY_URL = os.getenv("FEASIBILITY_URL", "http://localhost:8001")
CALCULATOR_URL = os.getenv("CALCULATOR_URL", "http://localhost:8002")
ESS_SCORING_URL = os.getenv("ESS_SCORING_URL", "http://localhost:8003")
ADVISORY_LLM_URL = os.getenv("ADVISORY_LLM_URL", "http://localhost:8004")

DOWNSTREAM_TIMEOUT_SECONDS = 10.0


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
    try:
        resp = httpx.post(
            f"{CALCULATOR_URL}/calculator", json=payload, timeout=DOWNSTREAM_TIMEOUT_SECONDS
        )
    except httpx.RequestError:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "calculator_unavailable",
                    "message": "Could not reach the calculator service",
                }
            },
        )
    return JSONResponse(status_code=resp.status_code, content=resp.json())


@app.post("/api/ess-score")
def ess_score(payload: dict):
    try:
        resp = httpx.post(
            f"{ESS_SCORING_URL}/ess-score", json=payload, timeout=DOWNSTREAM_TIMEOUT_SECONDS
        )
    except httpx.RequestError:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "ess_scoring_unavailable",
                    "message": "Could not reach the ess-scoring service",
                }
            },
        )
    return JSONResponse(status_code=resp.status_code, content=resp.json())


@app.post("/api/advisory-chat")
def advisory_chat(payload: dict):
    try:
        resp = httpx.post(
            f"{ADVISORY_LLM_URL}/advisory-chat", json=payload, timeout=DOWNSTREAM_TIMEOUT_SECONDS
        )
    except httpx.RequestError:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "advisory_llm_unavailable",
                    "message": "Could not reach the advisory-chat service",
                }
            },
        )
    return JSONResponse(status_code=resp.status_code, content=resp.json())
