import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from . import local_advisor, scheme_match
from .advisor import AdvisoryError, build_advisory_response
from .config import get_settings
from .retrieval import load_chunks
from .schemas import (
    AdvisoryChatRequest,
    AdvisoryChatResponse,
    SchemeMatchRequest,
    SchemeMatchResponse,
)

app = FastAPI(title="advisory-llm", version="0.1.0")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    message = "; ".join(
        f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()
    )
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": message}},
    )


@app.exception_handler(AdvisoryError)
async def advisory_error_handler(request: Request, exc: AdvisoryError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/debug/status")
async def debug_status():
    """Which mode we're in and what's actually available. Not in the contract --
    it exists so nobody has to guess during the demo whether an answer came from
    the real corpus, the trained local classifier, or mock mode."""
    settings = get_settings()
    chunks = load_chunks(settings.chunks_path)
    return {
        "mode": settings.mode,
        "model": settings.model,
        "corpus_chunks": len(chunks),
        "corpus_schemes": sorted({chunk.scheme for chunk in chunks}),
        "translator": "bhashini" if settings.bhashini_api_key else "passthrough",
        "local_advisor_model_available": local_advisor.is_model_available(),
        "scheme_match_model_available": scheme_match.is_model_available(),
    }


# Sync on purpose: in rag mode this makes a blocking API call, so FastAPI should
# run it in the threadpool rather than on the event loop. local_ml and mock mode
# are fast and CPU-only, so running them sync here costs nothing.
@app.post(
    "/advisory-chat",
    response_model=AdvisoryChatResponse,
    # `cited_sources[].url` is optional in the contract — omit it when we don't
    # have one instead of emitting an explicit null.
    response_model_exclude_none=True,
)
def advisory_chat(payload: AdvisoryChatRequest):
    return build_advisory_response(payload, get_settings())


# Not part of the original 4-endpoint contract — added for the trained
# scheme-match classifier (see app/scheme_match.py and train/). Always
# available regardless of ADVISORY_MODE, since it's a separate trained model
# with its own artifact, not gated behind the chat mode.
@app.post("/scheme-match", response_model=SchemeMatchResponse)
def scheme_match_endpoint(payload: SchemeMatchRequest):
    profile = payload.model_dump()
    results = scheme_match.predict_ranked_schemes(profile, top_k=3)
    importance = scheme_match.model_feature_importance() or {}
    return SchemeMatchResponse(
        request_id=str(uuid.uuid4()),
        results=results,
        model_feature_importance=importance,
    )
