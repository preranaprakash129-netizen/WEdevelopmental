import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.models import ESSScoreRequest, ESSScoreResponse
from app.scoring import lookup_business, score_profile

app = FastAPI(title="ess-scoring", version="0.1.0")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": str(exc.errors())}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        body = {"error": detail}
    else:
        body = {"error": {"code": "error", "message": str(detail)}}
    return JSONResponse(status_code=exc.status_code, content=body)


@app.post("/ess-score", response_model=ESSScoreResponse)
async def ess_score(payload: ESSScoreRequest) -> ESSScoreResponse:
    if payload.business_id:
        profile = lookup_business(payload.business_id)
        if profile is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "not_found", "message": f"No business found for id '{payload.business_id}'"},
            )
    else:
        profile = payload.profile_data

    result = score_profile(profile)
    return ESSScoreResponse(request_id=str(uuid.uuid4()), **result)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
