# Seed Data Spec — Synthetic Demo Locations

**Status:** schema only. Actual data files go in `data/seed/` as they're produced
(one JSON file per location, e.g. `data/seed/rampur.json`).

Goal: 2–3 fictional rural/semi-urban locations with enough structure that
`feasibility`, `calculator`, and `advisory-llm` can all query against the same data
without hitting a live database.

## Top-level location object

| Field | Type | Required | Notes |
|---|---|---|---|
| `location_name` | string | required | Fictional, e.g. `"Rampur"` |
| `state` | string | required | Used for state-specific scheme eligibility |
| `population` | integer | required | |
| `population_density_per_sqkm` | number | required | |
| `type` | string | required | `"rural"` \| `"semi-urban"` \| `"urban"` |
| `existing_businesses` | array<object> | required | See below |
| `price_bands` | array<object> | required | See below |

## `existing_businesses[]`

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | required | Fictional business name |
| `category` | string | required | Must match categories used across all services (see category list below) |
| `distance_from_center_km` | number | required | Distance from location's notional center point |
| `years_operating` | number | optional | |
| `estimated_monthly_revenue` | number | optional | INR |

## `price_bands[]`

One entry per category present in `existing_businesses`, describing the local market's
observed pricing range for that category's typical unit of sale.

| Field | Type | Required | Notes |
|---|---|---|---|
| `category` | string | required | |
| `unit` | string | required | e.g. `"per litre"`, `"per garment"` |
| `low` | number | required | INR |
| `median` | number | required | INR |
| `high` | number | required | INR |

## Shared category list

All services must use the same category strings. Draft list (extend as needed, but
announce additions to the team since `calculator`'s scheme-eligibility rules and
`ess-scoring`'s sub-models key off this list too):

- `dairy`
- `tailoring`
- `handicrafts`
- `food-processing`
- `retail-kirana`
- `poultry`

## Planned locations (data TBD, structure only)

1. `rampur` — rural, North India, dairy + tailoring concentration
2. `sundarpur` — semi-urban, South India, food-processing + retail concentration
3. (optional, if time permits) `hillview` — rural hill town, handicrafts + poultry concentration

## Example skeleton (structure, not final data)

```json
{
  "location_name": "Rampur",
  "state": "Uttar Pradesh",
  "population": 8400,
  "population_density_per_sqkm": 320,
  "type": "rural",
  "existing_businesses": [
    {
      "name": "Shree Dairy",
      "category": "dairy",
      "distance_from_center_km": 1.2,
      "years_operating": 5,
      "estimated_monthly_revenue": 45000
    }
  ],
  "price_bands": [
    { "category": "dairy", "unit": "per litre", "low": 40, "median": 55, "high": 70 }
  ]
}
```
