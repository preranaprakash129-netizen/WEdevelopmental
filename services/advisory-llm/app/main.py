from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .advisor import AdvisoryError, build_advisory_response
from .config import get_settings
from .retrieval import load_chunks
from .schemas import AdvisoryChatRequest, AdvisoryChatResponse

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
    """Which mode we're in and what's actually ingested.

    Not in the contract — it exists so nobody has to guess during the demo
    whether an answer came from the real corpus or from mock mode.
    """
    settings = get_settings()
    chunks = load_chunks(settings.chunks_path)
    return {
        "mode": settings.mode,
        "model": settings.model,
        "corpus_chunks": len(chunks),
        "corpus_schemes": sorted({chunk.scheme for chunk in chunks}),
        "translator": "bhashini" if settings.bhashini_api_key else "passthrough",
    }


# Sync on purpose: in rag mode this makes a blocking API call, so FastAPI should
# run it in the threadpool rather than on the event loop.
@app.post(
    "/advisory-chat",
    response_model=AdvisoryChatResponse,
    # `cited_sources[].url` is optional in the contract — omit it when we don't
    # have one instead of emitting an explicit null.
    response_model_exclude_none=True,
)
def advisory_chat(payload: AdvisoryChatRequest):
    return build_advisory_response(payload, get_settings())
