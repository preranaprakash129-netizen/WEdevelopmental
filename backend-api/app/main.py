import logging
import os
from contextlib import closing
from typing import Optional

import httpx
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger("backend-api")

app = FastAPI(title="SIH26091 backend-api", version="0.1.0")

# Was allow_origins=["*"] (wide open). In practice the frontend never makes a
# cross-origin browser request here at all -- both dev (vite.config.js's proxy)
# and docker-compose (frontend/nginx.conf's proxy_pass) forward /api/* to
# backend-api server-side, so the browser only ever sees same-origin requests to
# whatever origin served the page. Locked to those two origins anyway, as
# defense-in-depth against some other page trying to call this API directly from
# a browser. Override via CORS_ALLOWED_ORIGINS (comma-separated) if the demo runs
# from a different host/IP than localhost.
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    """Basic hardening headers, applied to every response. CSP here is `default-src
    'none'` because backend-api only ever serves JSON, never HTML -- it doesn't need
    to allow loading any resource type. (This does NOT cover the frontend's own served
    HTML/JS -- that would need a CSP header from frontend/nginx.conf instead, which is
    outside this task's backend-api-only scope; flagged as a follow-up.)"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    return response


# Matches the {"error": {"code", "message"}} shape every service in this contract uses
# for errors (see docs/api-contract.md > Conventions) -- FastAPI's default validation
# error shape ({"detail": [...]}) doesn't, and this is the one route in this file that
# actually validates its input rather than just proxying a dict downstream.
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    message = "; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors())
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": message}},
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
#
# This is the one route in this file that actually processes its input locally
# (writes to Postgres) rather than just forwarding a dict to a downstream service
# that validates it -- so unlike the proxy routes above, it gets its own Pydantic
# model. Bounds are deliberately generous (this is applicant-entered business data,
# not a security-critical field) but real: a length cap on every text field, and
# ess_score bounded to the 0-100 range the contract defines everywhere else.
class CreateApplicationRequest(BaseModel):
    applicant_name: Optional[str] = Field(default=None, max_length=200)
    location: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=100)
    ess_score: Optional[float] = Field(default=None, ge=0, le=100)
    status: str = Field(default="Under review", max_length=50)


@app.post("/api/applications")
def create_application(payload: CreateApplicationRequest):
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
                        (payload.applicant_name, payload.location, payload.category, payload.ess_score, payload.status),
                    )
                    row = cur.fetchone()
    except Exception:  # noqa: BLE001 - DB may not be up yet; degrade, don't crash
        logger.exception("Failed to insert application")
        return _db_unavailable_response()

    return JSONResponse(status_code=201, content=_serialize_row(row))


ESS_SCORE_BUCKETS = ["0-20", "20-40", "40-60", "60-80", "80-100"]


# Backs the Officer Dashboard's "AI Insights" section. Real aggregates computed from
# the applications table -- no invented numbers. One gap, documented rather than
# faked: scheme-match results (POST /api/scheme-match's classifier output) are never
# persisted anywhere -- that call is a stateless proxy to advisory-llm, and this table
# has no matched-scheme column -- so a per-scheme application count cannot be built
# from real data today. matched_scheme_breakdown is returned as null so the frontend
# can show an honest "not available yet" note instead of a missing field.
@app.get("/api/applications/insights")
def application_insights():
    try:
        with closing(get_conn()) as conn:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """
                        SELECT category, COUNT(*) AS count
                        FROM applications
                        GROUP BY category
                        ORDER BY count DESC
                        """
                    )
                    category_breakdown = [dict(row) for row in cur.fetchall()]

                    cur.execute(
                        """
                        SELECT
                            CASE
                                WHEN ess_score IS NULL THEN NULL
                                WHEN ess_score < 20 THEN '0-20'
                                WHEN ess_score < 40 THEN '20-40'
                                WHEN ess_score < 60 THEN '40-60'
                                WHEN ess_score < 80 THEN '60-80'
                                ELSE '80-100'
                            END AS bucket,
                            COUNT(*) AS count
                        FROM applications
                        GROUP BY bucket
                        """
                    )
                    bucket_counts = {row["bucket"]: row["count"] for row in cur.fetchall()}
    except Exception:  # noqa: BLE001 - DB may not be up yet; degrade, don't crash
        logger.exception("Failed to compute application insights")
        return _db_unavailable_response()

    total_applications = sum(row["count"] for row in category_breakdown)

    return {
        "total_applications": total_applications,
        "category_breakdown": category_breakdown,
        "ess_score_histogram": {
            "buckets": [
                {"range": label, "count": bucket_counts.get(label, 0)} for label in ESS_SCORE_BUCKETS
            ],
            "unscored_count": bucket_counts.get(None, 0),
        },
        "matched_scheme_breakdown": None,
    }


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
