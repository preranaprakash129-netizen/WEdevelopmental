import logging
import os
from contextlib import closing

import httpx
import psycopg2
import psycopg2.extras
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger("backend-api")

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

# backend-api owns the "applications" table directly — there's no dedicated microservice
# for the officer dashboard's applicant list, so this is a thin persistence layer rather
# than a proxy. DATABASE_URL comes from .env; docker-compose overrides it to the `postgres`
# container hostname (see docker-compose.yml's backend-api environment block).
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/sih26091")


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def _serialize_row(row):
    # psycopg2 returns NUMERIC columns as decimal.Decimal and TIMESTAMPTZ as datetime,
    # neither of which FastAPI's default JSON encoder can serialize directly.
    return dict(
        row,
        ess_score=float(row["ess_score"]) if row["ess_score"] is not None else None,
        created_at=row["created_at"].isoformat(),
    )


def ensure_schema():
    """Best-effort table creation. Failures here must not crash the gateway — the other
    proxy routes don't depend on postgres at all, so a missing/unreachable DB should only
    degrade the applications endpoints, not the whole service."""
    try:
        # `closing()` ensures the connection is actually closed on exit — psycopg2's own
        # `with conn:` context manager only commits/rolls back, it does NOT close the
        # connection, which would otherwise leak one per request.
        with closing(get_conn()) as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS applications (
                            id SERIAL PRIMARY KEY,
                            applicant_name TEXT,
                            location TEXT NOT NULL,
                            category TEXT NOT NULL,
                            ess_score NUMERIC,
                            status TEXT NOT NULL DEFAULT 'Under review',
                            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                        )
                        """
                    )
    except Exception:  # noqa: BLE001 - deliberately broad, see docstring
        logger.exception("Could not ensure `applications` table exists; DB may be unavailable yet")


@app.on_event("startup")
def on_startup():
    ensure_schema()


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


def _db_unavailable_response():
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "applications_db_unavailable",
                "message": "Could not reach the applications database",
            }
        },
    )


# Not part of docs/api-contract.md's original 4 endpoints — added to back the officer
# dashboard's applicant list (previously hardcoded placeholder rows in the frontend).
# Each wizard run that reaches the ESS-score step (or skips it) records a row here.
@app.post("/api/applications")
def create_application(payload: dict):
    location = payload.get("location")
    category = payload.get("category")
    if not location or not category:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "invalid_application",
                    "message": "location and category are required",
                }
            },
        )
    applicant_name = payload.get("applicant_name")
    ess_score = payload.get("ess_score")
    status = payload.get("status") or "Under review"

    try:
        with closing(get_conn()) as conn:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """
                        INSERT INTO applications (applicant_name, location, category, ess_score, status)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id, applicant_name, location, category, ess_score, status, created_at
                        """,
                        (applicant_name, location, category, ess_score, status),
                    )
                    row = cur.fetchone()
    except Exception:  # noqa: BLE001 - DB may not be up yet; degrade, don't crash
        logger.exception("Failed to insert application")
        return _db_unavailable_response()

    return JSONResponse(status_code=201, content=_serialize_row(row))


@app.get("/api/applications")
def list_applications():
    try:
        with closing(get_conn()) as conn:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """
                        SELECT id, applicant_name, location, category, ess_score, status, created_at
                        FROM applications
                        ORDER BY created_at DESC
                        LIMIT 100
                        """
                    )
                    rows = cur.fetchall()
    except Exception:  # noqa: BLE001 - DB may not be up yet; degrade, don't crash
        logger.exception("Failed to list applications")
        return _db_unavailable_response()

    return {"applications": [_serialize_row(row) for row in rows]}


# Same downstream service as advisory-chat (advisory-llm hosts both the chat
# endpoint and the trained scheme-match classifier) — reuses ADVISORY_LLM_URL
# rather than introducing a new env var for a service that isn't actually
# separate. See services/advisory-llm/app/scheme_match.py.
@app.post("/api/scheme-match")
def scheme_match(payload: dict):
    try:
        resp = httpx.post(
            f"{ADVISORY_LLM_URL}/scheme-match", json=payload, timeout=DOWNSTREAM_TIMEOUT_SECONDS
        )
    except httpx.RequestError:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "scheme_match_unavailable",
                    "message": "Could not reach the scheme-match model",
                }
            },
        )
    return JSONResponse(status_code=resp.status_code, content=resp.json())
