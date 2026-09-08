# backend-api

Owner: person 1

FastAPI gateway/orchestrator. Proxies `/api/*` to the four services and handles any
cross-service orchestration (e.g. calculator needing feasibility's output).

See [`docs/api-contract.md`](../docs/api-contract.md) for the routes it must expose.

## Local dev

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
