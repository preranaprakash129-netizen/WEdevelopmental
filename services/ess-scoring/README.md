# services/ess-scoring

Owner: person 4

ESS sub-models, SHAP-style attribution, diagnostics.
Implements `POST /ess-score` — see [`docs/api-contract.md`](../../docs/api-contract.md).

## Local dev

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```

## Tests

```bash
pytest
```

## Model notes

`app/scoring.py` implements a lite weighted-sum model:

- Sub-score weights: `financial_health` 40%, `operational_maturity` 25%,
  `market_stability` 20%, `growth_potential` 15% (financial-health weighted, since
  this score feeds credit/scheme decisions).
- Features are min-max normalized against bounds calibrated from a synthetic profile
  population, then blended per sub-score.
- `attribution` is a true additive decomposition of `ess_score` relative to a neutral
  (all-50) baseline, not an approximation.
- `lookup_business` in `app/scoring.py` is a hardcoded mock until a real profile store
  (or `calculator`'s output) is available.
