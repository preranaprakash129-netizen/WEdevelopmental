"""
Scoring logic for POST /ess-score: a lite weighted-sum ESS model.

Sub-score weights and feature mapping confirmed with the team on 2026-09-09:

- financial_health (40%)      <- monthly_revenue (70%), has_bank_account (30%)
- operational_maturity (25%)  <- years_operating (60%), employee_count (40%)
- market_stability (20%)      <- category, via a static per-category baseline
- growth_potential (15%)      <- revenue_growth_rate (monthly_revenue / years_operating,
                                  a proxy for how fast the business is scaling relative
                                  to its age)

Each raw/derived feature is min-max normalized to 0-100 against bounds learned from a
synthetic profile population (see `_generate_synthetic_profiles`), then blended per the
intra-sub-score weights above. `ess_score` is the weighted sum of the four sub-scores,
so it is automatically in [0, 100] since the sub-score weights sum to 1.

Attribution is SHAP-style relative to a neutral baseline where every feature scores 50:
impact(feature) = subscore_weight * intra_weight * (feature_score - 50)
Summed across all features this equals `ess_score - 50`, so it's a true additive
decomposition of the score rather than an approximation.
"""

import random
from typing import Optional

from app.models import ProfileData

# --- Mock business lookup, standing in for a real profile store until one exists. ---
_MOCK_BUSINESSES: dict[str, ProfileData] = {
    "biz_001": ProfileData(
        category="dairy",
        years_operating=5,
        monthly_revenue=45000,
        employee_count=2,
        has_bank_account=True,
    ),
}


def lookup_business(business_id: str) -> Optional[ProfileData]:
    return _MOCK_BUSINESSES.get(business_id)


# --- Sub-score weights (must sum to 1) ---
SUBSCORE_WEIGHTS = {
    "financial_health": 0.40,
    "operational_maturity": 0.25,
    "market_stability": 0.20,
    "growth_potential": 0.15,
}

# --- Static market-stability baseline per category (0-100). ---
# Categories match the shared list in docs/seed-data-spec.md; unlisted categories
# fall back to _DEFAULT_CATEGORY_STABILITY.
CATEGORY_STABILITY_BASELINE = {
    "dairy": 75.0,
    "retail-kirana": 70.0,
    "food-processing": 65.0,
    "tailoring": 60.0,
    "handicrafts": 55.0,
    "poultry": 50.0,
}
_DEFAULT_CATEGORY_STABILITY = 55.0

_NEUTRAL = 50.0
_IMPROVEMENT_TARGET = 85.0


def _generate_synthetic_profiles(n: int = 500, seed: int = 42) -> list[dict]:
    """Synthetic profile population used only to calibrate normalization bounds."""
    rng = random.Random(seed)
    profiles = []
    for _ in range(n):
        years = rng.uniform(0, 15)
        revenue = max(2000.0, rng.gauss(30000, 20000))
        employees = rng.randint(0, 10)
        profiles.append(
            {
                "years_operating": years,
                "monthly_revenue": revenue,
                "employee_count": float(employees),
                "revenue_growth_rate": revenue / max(years, 0.5),
            }
        )
    return profiles


def _bounds(profiles: list[dict], key: str) -> tuple[float, float]:
    values = [p[key] for p in profiles]
    return min(values), max(values)


_SYNTHETIC_PROFILES = _generate_synthetic_profiles()
_REVENUE_MIN, _REVENUE_MAX = _bounds(_SYNTHETIC_PROFILES, "monthly_revenue")
_YEARS_MIN, _YEARS_MAX = _bounds(_SYNTHETIC_PROFILES, "years_operating")
_EMPLOYEES_MIN, _EMPLOYEES_MAX = _bounds(_SYNTHETIC_PROFILES, "employee_count")
_GROWTH_MIN, _GROWTH_MAX = _bounds(_SYNTHETIC_PROFILES, "revenue_growth_rate")


def _normalize(value: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return _NEUTRAL
    return max(0.0, min(100.0, (value - lo) / (hi - lo) * 100))


def _feature_scores(profile: ProfileData) -> dict[str, float]:
    employee_count = float(profile.employee_count or 0)
    revenue_growth_rate = profile.monthly_revenue / max(profile.years_operating, 0.5)

    return {
        "monthly_revenue": _normalize(profile.monthly_revenue, _REVENUE_MIN, _REVENUE_MAX),
        "has_bank_account": 100.0 if profile.has_bank_account else 30.0,
        "years_operating": _normalize(profile.years_operating, _YEARS_MIN, _YEARS_MAX),
        "employee_count": _normalize(employee_count, _EMPLOYEES_MIN, _EMPLOYEES_MAX),
        "category": CATEGORY_STABILITY_BASELINE.get(profile.category, _DEFAULT_CATEGORY_STABILITY),
        "revenue_growth_rate": _normalize(revenue_growth_rate, _GROWTH_MIN, _GROWTH_MAX),
    }


# (sub_score, intra-sub-score weight) for each feature.
_FEATURE_SUBSCORE = {
    "monthly_revenue": ("financial_health", 0.7),
    "has_bank_account": ("financial_health", 0.3),
    "years_operating": ("operational_maturity", 0.6),
    "employee_count": ("operational_maturity", 0.4),
    "category": ("market_stability", 1.0),
    "revenue_growth_rate": ("growth_potential", 1.0),
}

# Features an entrepreneur can actually act on; category/years_operating/the derived
# growth-rate proxy are excluded from top_improvement_action candidates.
_ACTIONABLE_FEATURES = {"monthly_revenue", "has_bank_account", "employee_count"}

_ACTION_TEXT = {
    "monthly_revenue": "Increase monthly revenue through additional sales channels, higher order volume, or higher-margin offerings",
    "has_bank_account": "Open a dedicated business bank account to formalize cash flow tracking",
    "employee_count": "Consider hiring or formalizing additional staff to support operational scaling",
}


def score_profile(profile: ProfileData) -> dict:
    feature_scores = _feature_scores(profile)

    sub_scores = {name: 0.0 for name in SUBSCORE_WEIGHTS}
    for feature, (sub_score_name, intra_weight) in _FEATURE_SUBSCORE.items():
        sub_scores[sub_score_name] += intra_weight * feature_scores[feature]

    ess_score = sum(SUBSCORE_WEIGHTS[name] * value for name, value in sub_scores.items())

    attribution = []
    for feature, (sub_score_name, intra_weight) in _FEATURE_SUBSCORE.items():
        impact = SUBSCORE_WEIGHTS[sub_score_name] * intra_weight * (feature_scores[feature] - _NEUTRAL)
        attribution.append({"feature": feature, "impact": round(impact, 2)})
    attribution.sort(key=lambda item: abs(item["impact"]), reverse=True)

    best_feature = max(
        _ACTIONABLE_FEATURES,
        key=lambda feature: SUBSCORE_WEIGHTS[_FEATURE_SUBSCORE[feature][0]]
        * _FEATURE_SUBSCORE[feature][1]
        * (_IMPROVEMENT_TARGET - feature_scores[feature]),
    )
    sub_score_name, intra_weight = _FEATURE_SUBSCORE[best_feature]
    expected_score_delta = SUBSCORE_WEIGHTS[sub_score_name] * intra_weight * (
        _IMPROVEMENT_TARGET - feature_scores[best_feature]
    )

    return {
        "ess_score": round(ess_score, 2),
        "sub_scores": {name: round(value, 2) for name, value in sub_scores.items()},
        "attribution": attribution,
        "top_improvement_action": {
            "action": _ACTION_TEXT[best_feature],
            "expected_score_delta": round(max(expected_score_delta, 0.0), 2),
        },
    }
