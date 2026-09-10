# API Contract — SIH26091 (v0.1, draft)

**Status:** single source of truth for all 6 services during the hackathon. If you need to
change a field, edit this file in a PR and ping the team in chat before merging — don't
change your service's actual response shape without updating this doc first.

**Base URL (local dev):** each service is reachable directly on its own port for local
testing, and also proxied through `backend-api` (the gateway) at `/api/*`.

| Service | Direct port | Gateway path |
|---|---|---|
| backend-api | 8000 | — |
| feasibility | 8001 | `/api/feasibility` |
| calculator | 8002 | `/api/calculator` |
| ess-scoring | 8003 | `/api/ess-score` |
| advisory-llm | 8004 | `/api/advisory-chat` |

**Conventions:**
- All requests/responses are `application/json`.
- All monetary fields are in INR, integers (paise-free, rounded rupees) unless noted.
- All dates are ISO 8601 (`YYYY-MM-DD`).
- Every response includes `"request_id": string` (uuid4) for tracing — omitted from
  examples below for brevity but must be implemented.
- Error shape (all services): `{"error": {"code": string, "message": string}}` with a 4xx/5xx
  HTTP status.
- **Auth:** none for this hackathon build. No auth headers/tokens required on any endpoint.

## Orchestration

`backend-api` is the only service allowed to call other services. `feasibility`,
`calculator`, `ess-scoring`, and `advisory-llm` never call each other directly — if one
service's logic depends on another's output (e.g. `calculator` needing a `project_cost`
estimate from `feasibility`), `backend-api` fetches it and passes it in as part of the
request to the downstream service. Do not add HTTP calls from one `services/*` folder to
another.

---

## 1. `POST /feasibility`

Owner: `services/feasibility` (person 2)

### Request

| Field | Type | Required | Notes |
|---|---|---|---|
| `location` | string | required | Name of demo location, must match `data/seed` |
| `category` | string | required | Business category, e.g. `"dairy"`, `"tailoring"` |
| `margin_capital` | number | required | Entrepreneur's own capital available, in INR |

```json
{
  "location": "Rampur",
  "category": "dairy",
  "margin_capital": 50000
}
```

### Response

| Field | Type | Required | Notes |
|---|---|---|---|
| `market_reach` | object | required | See below |
| `market_reach.estimated_customers` | integer | required | |
| `market_reach.radius_km` | number | required | |
| `competitor_list` | array<object> | required | May be empty array |
| `competitor_list[].name` | string | required | |
| `competitor_list[].category` | string | required | |
| `competitor_list[].distance_km` | number | required | |
| `swot` | object | required | |
| `swot.strengths` | array<string> | required | |
| `swot.weaknesses` | array<string> | required | |
| `swot.opportunities` | array<string> | required | |
| `swot.threats` | array<string> | required | |
| `pricing_bands` | object | required | |
| `pricing_bands.low` | number | required | INR |
| `pricing_bands.median` | number | required | INR |
| `pricing_bands.high` | number | required | INR |
| `feasibility_score` | number | required | 0–100 |
| `confidence_range` | object | required | |
| `confidence_range.low` | number | required | 0–100, ≤ `feasibility_score` |
| `confidence_range.high` | number | required | 0–100, ≥ `feasibility_score` |

```json
{
  "market_reach": {
    "estimated_customers": 1200,
    "radius_km": 3.5
  },
  "competitor_list": [
    { "name": "Shree Dairy", "category": "dairy", "distance_km": 1.2 },
    { "name": "Gopal Milk Center", "category": "dairy", "distance_km": 2.8 }
  ],
  "swot": {
    "strengths": ["Low local competition density", "Steady demand for milk products"],
    "weaknesses": ["High cold-chain setup cost"],
    "opportunities": ["Government dairy subsidy schemes available"],
    "threats": ["Seasonal demand fluctuation"]
  },
  "pricing_bands": { "low": 40, "median": 55, "high": 70 },
  "feasibility_score": 72.5,
  "confidence_range": { "low": 64.0, "high": 79.0 }
}
```

---

## 2. `POST /calculator`

Owner: `services/calculator` (person 3)

> **Note:** `calculator` must not call `feasibility` directly. If `project_cost` needs a
> feasibility-derived estimate, `backend-api` fetches it from `feasibility` and passes it
> into this endpoint (or a future field on this request) — see [Orchestration](#orchestration)
> above.

### Request

| Field | Type | Required | Notes |
|---|---|---|---|
| `margin_capital` | number | required | INR |
| `category` | string | required | Business category |
| `location` | string | optional | Used for scheme eligibility rules that vary by state/UT |
| `requested_loan_amount` | number | optional | If omitted, service recommends amount |
| `social_category` | string | optional | One of `"general"`, `"obc"`, `"sc"`, `"st"` — used for Stand-Up India eligibility |
| `gender` | string | optional | One of `"male"`, `"female"`, `"other"` — used for Stand-Up India eligibility |
| `is_rural` | boolean | optional | Accepted, not yet used in scheme selection |
| `enterprise_vintage_months` | number | optional | Accepted, not yet used in scheme selection |
| `requested_scheme` | string | optional | `"MUDRA"` or `"Stand-Up India"`. Bypasses cost-based routing — MUDRA's real range (≤Rs 10L) sits entirely inside the Micro Finance / Term Loan cost bands, and Stand-Up India's Rs 10L-50L portion is otherwise claimed by Term Loan Scheme; both are unreachable without this |

```json
{
  "margin_capital": 50000,
  "category": "dairy",
  "location": "Rampur"
}
```

### Response

| Field | Type | Required | Notes |
|---|---|---|---|
| `project_cost` | number | required | INR |
| `scheme_selected` | object | required | |
| `scheme_selected.name` | string | required | e.g. `"PMEGP"`, `"MUDRA (Shishu)"`, `"MUDRA (Kishor)"`, `"MUDRA (Tarun)"`, `"Stand-Up India"` |
| `scheme_selected.subsidy_percent` | number | required | 0–100 |
| `loan_amount` | number | required | INR |
| `emi_schedule` | array<object> | required | Monthly rows |
| `emi_schedule[].month` | integer | required | 1-indexed |
| `emi_schedule[].emi` | number | required | INR |
| `emi_schedule[].principal_component` | number | required | INR |
| `emi_schedule[].interest_component` | number | required | INR |
| `emi_schedule[].outstanding_balance` | number | required | INR |
| `moratorium` | object | required | |
| `moratorium.months` | integer | required | 0 if none |
| `moratorium.reason` | string | optional | |
| `working_capital` | number | required | INR, recommended working capital buffer |

```json
{
  "project_cost": 200000,
  "scheme_selected": { "name": "PMEGP", "subsidy_percent": 25 },
  "loan_amount": 150000,
  "emi_schedule": [
    { "month": 1, "emi": 4200, "principal_component": 3100, "interest_component": 1100, "outstanding_balance": 146900 },
    { "month": 2, "emi": 4200, "principal_component": 3140, "interest_component": 1060, "outstanding_balance": 143760 }
  ],
  "moratorium": { "months": 6, "reason": "PMEGP standard moratorium for dairy category" },
  "working_capital": 25000
}
```

> Note: `emi_schedule` in the example is truncated to 2 rows — real responses return the
> full schedule for the loan tenure.

---

## 3. `POST /ess-score`

Owner: `services/ess-scoring` (person 4)

### Request

Exactly one of `business_id` or `profile_data` is required.

| Field | Type | Required | Notes |
|---|---|---|---|
| `business_id` | string | optional* | Lookup existing profile |
| `profile_data` | object | optional* | Raw profile for a new/unregistered business |
| `profile_data.category` | string | required if `profile_data` present | |
| `profile_data.years_operating` | number | required if `profile_data` present | |
| `profile_data.monthly_revenue` | number | required if `profile_data` present | INR |
| `profile_data.employee_count` | integer | optional | |
| `profile_data.has_bank_account` | boolean | required if `profile_data` present | |

```json
{
  "profile_data": {
    "category": "tailoring",
    "years_operating": 2,
    "monthly_revenue": 18000,
    "employee_count": 1,
    "has_bank_account": true
  }
}
```

### Response

| Field | Type | Required | Notes |
|---|---|---|---|
| `ess_score` | number | required | 0–100, overall Entrepreneurial Sustainability Score |
| `sub_scores` | object | required | |
| `sub_scores.financial_health` | number | required | 0–100 |
| `sub_scores.market_stability` | number | required | 0–100 |
| `sub_scores.operational_maturity` | number | required | 0–100 |
| `sub_scores.growth_potential` | number | required | 0–100 |
| `attribution` | array<object> | required | SHAP-style feature attribution, sorted by `|impact|` desc |
| `attribution[].feature` | string | required | |
| `attribution[].impact` | number | required | Signed contribution to `ess_score` |
| `top_improvement_action` | object | required | |
| `top_improvement_action.action` | string | required | Human-readable recommendation |
| `top_improvement_action.expected_score_delta` | number | required | Estimated `ess_score` gain |

```json
{
  "ess_score": 61.0,
  "sub_scores": {
    "financial_health": 55.0,
    "market_stability": 70.0,
    "operational_maturity": 58.0,
    "growth_potential": 61.0
  },
  "attribution": [
    { "feature": "monthly_revenue", "impact": 8.2 },
    { "feature": "years_operating", "impact": -3.1 },
    { "feature": "has_bank_account", "impact": 2.4 }
  ],
  "top_improvement_action": {
    "action": "Open a dedicated business bank account to formalize cash flow tracking",
    "expected_score_delta": 4.5
  }
}
```

---

## 4. `POST /advisory-chat`

Owner: `services/advisory-llm` (person 6)

### Request

| Field | Type | Required | Notes |
|---|---|---|---|
| `message` | string | required | User's chat message |
| `language` | string | optional | ISO 639-1 code, e.g. `"hi"`, `"en"`. If omitted, service auto-detects |
| `context` | object | optional | |
| `context.business_id` | string | optional | |
| `context.conversation_id` | string | optional | For multi-turn continuity |

```json
{
  "message": "PMEGP ke liye kaise apply karein?",
  "context": { "conversation_id": "conv_8841" }
}
```

### Response

| Field | Type | Required | Notes |
|---|---|---|---|
| `response_text` | string | required | Answer in the detected/requested language |
| `cited_sources` | array<object> | required | May be empty array |
| `cited_sources[].scheme` | string | required | e.g. `"PMEGP"` |
| `cited_sources[].document` | string | required | Source doc name/title |
| `cited_sources[].url` | string | optional | If available |
| `detected_language` | string | required | ISO 639-1 code |

```json
{
  "response_text": "PMEGP ke liye aap apne zile ke KVIC/DIC office mein online apply kar sakte hain...",
  "cited_sources": [
    { "scheme": "PMEGP", "document": "PMEGP Guidelines 2023", "url": "https://kviconline.gov.in/pmegp" }
  ],
  "detected_language": "hi"
}
```

---

## 5. `POST /applications` and `GET /applications`

Owner: `backend-api` directly (not a proxy — there's no dedicated microservice for this;
`backend-api` persists to Postgres itself). Added after the original 4-endpoint contract to
back the officer dashboard's applicant list, replacing what used to be hardcoded placeholder
rows in the frontend. Gateway path for both: `/api/applications`.

### `POST /applications` — record a wizard run

| Field | Type | Required | Notes |
|---|---|---|---|
| `location` | string | required | |
| `category` | string | required | |
| `applicant_name` | string | optional | No name field exists in the wizard's Intake step yet; omitted for now |
| `ess_score` | number | optional | 0–100, from the ESS-scoring step if the applicant didn't skip it |
| `status` | string | optional | Defaults to `"Under review"` |

```json
{ "location": "Rampur", "category": "dairy", "ess_score": 61.0 }
```

Response: `201` with the inserted row (`id`, `applicant_name`, `location`, `category`,
`ess_score`, `status`, `created_at`). `400` if `location` or `category` is missing. `503`
with the standard error shape if the database isn't reachable.

### `GET /applications` — list recent applications

No request body. Response: `200` with `{"applications": [...]}`, same row shape as above,
newest first, capped at 100. `503` with the standard error shape if the database isn't
reachable.

---

## Open questions (track here, resolve async)

- [x] Auth — resolved: none for this hackathon build (see Conventions above).
- [x] Calculator/feasibility orchestration — resolved: `backend-api` orchestrates, services never call each other directly (see Orchestration above).

All open questions resolved as of this revision.
