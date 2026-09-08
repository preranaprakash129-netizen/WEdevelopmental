from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .mock_data import build_feasibility_response
from .schemas import FeasibilityRequest, FeasibilityResponse

app = FastAPI(title="feasibility", version="0.1.0")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    message = "; ".join(
        f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()
    )
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": message}},
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/feasibility", response_model=FeasibilityResponse)
async def feasibility(payload: FeasibilityRequest):
    return build_feasibility_response(
        location=payload.location,
        category=payload.category,
        margin_capital=payload.margin_capital,
    )
