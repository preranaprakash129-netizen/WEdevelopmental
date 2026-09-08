# services/feasibility

Owner: person 2

Market reach, competitor list, SWOT, pricing bands, feasibility score + confidence range.
Implements `POST /feasibility` — see [`docs/api-contract.md`](../../docs/api-contract.md).

## Local dev

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

`feasibility_score` blends competitor density/proximity, margin_capital vs. a category's
typical setup cost, market size (population/density), and local pricing spread —
see `app/scoring.py` for weights and the (hackathon-demo, tune freely) assumption tables.
`confidence_range` narrows as more of that data comes from real seed files rather than
defaults for an unmatched location/category.

## Tests

```bash
pytest
```
