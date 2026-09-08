# services/ess-scoring

Owner: person 4

ESS sub-models, SHAP-style attribution, diagnostics.
Implements `POST /ess-score` — see [`docs/api-contract.md`](../../docs/api-contract.md).

## Local dev

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```
