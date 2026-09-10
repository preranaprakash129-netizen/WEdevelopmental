# Live demo script — SIH26091

Built from `data/seed/rampur.json`, `data/seed/sundarpur.json`, and `docs/api-contract.md`.
**Not yet re-verified against a running stack in this environment** (see note at the bottom) —
run the "Pre-demo check" section once, live, before presenting.

## Setup

```bash
cp .env.example .env   # fill LLM_API_KEY if advisory-chat needs it for real answers
docker compose up --build
```

Open http://localhost:5173

## Primary path — Rampur, dairy (recommended for the live click-through)

**Step 1 — Intake** (`/`)
| Field | Value |
|---|---|
| Location | `Rampur` |
| Category | `dairy` |
| Margin capital | `50000` |

Click Continue → goes to Feasibility.

**Step 2 — Feasibility** (`/feasibility`)
Calls `POST /api/feasibility` with the intake values. Expect a populated market-reach panel,
a 3-competitor list (Shree Dairy, Gopal Milk Center, Krishna Dairy Farm — all seeded in
`rampur.json`), a SWOT block, and a feasibility score. Click Continue → Calculator.

**Step 3 — Calculator** (`/calculator`)
Calls `POST /api/calculator` with the same intake values. Leave "requested loan amount" blank
to let the service recommend one. Expect a scheme selection (likely PMEGP at this project-cost
band), an EMI schedule table, and a moratorium note.

**Step 4 — Dashboard** (`/dashboard`)
⚠️ This page is a **static placeholder**, not live — it renders two hardcoded rows
(`DashboardPage.jsx`), it does not call `/api/ess-score` or `/api/advisory-chat`. Don't present
it as "live backend data" — say it's the planned officer view, not yet wired up.

## Alternate path — Sundarpur, food-processing (use if asked for a second example)

| Field | Value |
|---|---|
| Location | `Sundarpur` |
| Category | `food-processing` |
| Margin capital | `70000` |

Feasibility should surface the three seeded food-processing competitors (Amma's Pickles & Foods,
Sundarpur Snacks Co., Meenakshi Food Products) and the ₹120–260/kg price band.

## Backend-only checks (ess-scoring and advisory-llm are live but not wired into the UI yet)

These are real, working endpoints — show them via curl or a REST client if asked "does ESS
scoring / advisory chat work at all", but don't present them as part of the wizard:

```bash
curl -s http://localhost:8000/api/ess-score -H 'content-type: application/json' -d '{
  "profile_data": {
    "category": "dairy",
    "years_operating": 6,
    "monthly_revenue": 45000,
    "employee_count": 2,
    "has_bank_account": true
  }
}' | python3 -m json.tool

curl -s http://localhost:8000/api/advisory-chat -H 'content-type: application/json' -d '{
  "message": "How do I apply for PMEGP?",
  "context": { "conversation_id": "demo_1" }
}' | python3 -m json.tool
```

## Fallback if a service is flaky during the demo

- `docker compose ps` — confirm all 7 containers are `Up`.
- `docker compose logs <service> --tail 50` — check the failing one.
- If `feasibility` or `calculator` 503s, `backend-api` surfaces a clean
  `{"error": {"code": "..._unavailable", ...}}` instead of hanging — the UI should show an
  error state, not a blank screen. Worth clicking through once before the audience does.

## ✅ Verification status

The script's field values and expected responses were derived from the seed data and
`docs/api-contract.md`. On top of that, Kashif ran the full stack locally after PR #13 landed:
all 7 containers came up healthy (`docker compose ps`), and the wizard returned real
end-to-end responses from the backend rather than errors or blank states. If you run through
it again before presenting, it's still worth a quick eyeball that the competitor names and
price bands on screen match what's listed above for whichever seed location you use — response
shapes can drift if a service changes without this doc being updated.
