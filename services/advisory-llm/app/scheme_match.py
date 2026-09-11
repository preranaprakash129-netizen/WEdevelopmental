"""Inference wrapper around the trained scheme-match model (see train/).

Loaded once at process startup (see main.py), not per-request -- the joblib
file is a few hundred KB and loads in milliseconds, but there's no reason to
pay even that cost twice.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import joblib
import pandas as pd

from .scheme_facts import SCHEMES

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "scheme_match.joblib"

_model_bundle = None


def _load() -> dict:
    global _model_bundle
    if _model_bundle is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"{MODEL_PATH} not found -- run `python train/generate_training_data.py "
                f"&& python train/train_scheme_match.py` from services/advisory-llm/ first."
            )
        _model_bundle = joblib.load(MODEL_PATH)
    return _model_bundle


def is_model_available() -> bool:
    return MODEL_PATH.exists()


def _why_bullets(scheme_key: str, profile: Dict) -> List[str]:
    """Plain-language reasons, generated from the same real rules in
    scheme_facts.py that labeled the training data -- not from the model
    itself (a Random Forest's internal logic isn't directly a sentence).
    This pairs the ML's ranking/confidence with a rule-based, verifiable
    explanation, rather than asking the model to explain itself."""
    facts = SCHEMES[scheme_key]
    bullets: List[str] = []

    if facts.women_only:
        bullets.append("Reserved for women entrepreneurs, which matches the applicant.")
    if facts.requires_sc_st_or_woman and (profile.get("is_sc_st") or profile.get("gender") == "female"):
        bullets.append("Every bank branch must fund at least one SC/ST or woman borrower under this scheme.")
    if facts.allowed_categories and profile.get("category") in facts.allowed_categories:
        bullets.append(f"Specifically targets the '{profile['category']}' category.")
    if facts.requires_new_business and profile.get("is_new_business"):
        bullets.append("Designed for new (greenfield) businesses, which matches this application.")
    if not facts.requires_new_business and not profile.get("is_new_business"):
        bullets.append("Open to existing businesses, not just new ones.")
    if facts.min_loan is not None and facts.max_loan is not None:
        if facts.min_loan <= profile.get("requested_amount", 0) <= facts.max_loan:
            bullets.append(
                f"Requested amount fits the scheme's Rs.{facts.min_loan:,}-Rs.{facts.max_loan:,} range."
            )
    if facts.subsidy_special_pct and (profile.get("is_sc_st") or profile.get("gender") == "female"):
        bullets.append(f"Special-category subsidy of {facts.subsidy_special_pct:.0f}% may apply.")
    elif facts.subsidy_general_pct:
        bullets.append(f"General-category subsidy of {facts.subsidy_general_pct:.0f}% may apply.")
    if facts.guarantee_coverage_pct_general:
        cov = (
            facts.guarantee_coverage_pct_special
            if (profile.get("is_sc_st") or profile.get("gender") == "female")
            else facts.guarantee_coverage_pct_general
        )
        bullets.append(f"Bank loan can get up to {cov:.0f}% collateral-free guarantee coverage.")

    return bullets[:3] or ["Matches this business profile's loan range and category."]


def _category_fit(facts, profile: Dict) -> float:
    if not facts.allowed_categories:
        return 1.0
    return 1.0 if profile.get("category") in facts.allowed_categories else 0.25


def _loan_amount_fit(facts, profile: Dict) -> float:
    if facts.min_loan is None or facts.max_loan is None:
        # Non-credit schemes (none in this prototype's current 6, but this
        # axis is written to degrade gracefully if one is ever added) have no
        # loan amount to fit against -- this axis simply doesn't apply, so
        # don't penalize it.
        return 1.0
    requested = profile.get("requested_amount", 0)
    lo, hi = facts.min_loan, min(facts.max_loan, 10_000_000)
    if lo <= requested <= hi:
        return 1.0
    span = max(1.0, hi - lo)
    distance = min(abs(requested - lo), abs(requested - hi))
    return round(max(0.0, 1.0 - distance / span), 4)


def _eligibility_fit(facts, profile: Dict) -> float:
    gates_applicable = 0
    gates_met = 0
    if facts.requires_new_business:
        gates_applicable += 1
        gates_met += int(bool(profile.get("is_new_business")))
    if facts.requires_sc_st_or_woman:
        gates_applicable += 1
        gates_met += int(bool(profile.get("is_sc_st") or profile.get("gender") == "female"))
    if facts.women_only:
        gates_applicable += 1
        gates_met += int(profile.get("gender") == "female")
    if facts.max_annual_family_income is not None:
        gates_applicable += 1
        cap = (
            facts.max_annual_family_income_sc_st
            if (profile.get("is_sc_st") and facts.max_annual_family_income_sc_st is not None)
            else facts.max_annual_family_income
        )
        gates_met += int(profile.get("annual_family_income", 0) <= cap)
    if gates_applicable == 0:
        return 1.0
    return gates_met / gates_applicable


def _priority_boost_fit(facts, profile: Dict) -> float:
    """1.0 = this scheme has a higher special-category tier and this profile
    qualifies for it; 0.0 = the tier exists but this profile doesn't qualify;
    0.5 = neutral, this scheme has no special-category tier at all (not a
    penalty -- just not applicable)."""
    has_special_tier = (
        bool(facts.subsidy_special_pct and facts.subsidy_special_pct != facts.subsidy_general_pct)
        or bool(
            facts.guarantee_coverage_pct_special
            and facts.guarantee_coverage_pct_special != facts.guarantee_coverage_pct_general
        )
    )
    if not has_special_tier:
        return 0.5
    qualifies = profile.get("is_sc_st") or profile.get("gender") == "female"
    return 1.0 if qualifies else 0.0


def _match_breakdown(scheme_key: str, profile: Dict) -> Dict[str, float]:
    """Four deterministic, rule-based sub-scores (0-1) behind the single
    confidence number -- powers the "AI Insights" breakdown chart on the
    frontend. These are NOT the Random Forest's internal feature
    contributions (that would need SHAP or similar, and would still need a
    plain-language translation); they're a separate, fully transparent
    rule-based decomposition using the same scheme_facts.py rules that
    labeled the training data, in the same spirit as _why_bullets above."""
    facts = SCHEMES[scheme_key]
    return {
        "category_fit": round(_category_fit(facts, profile), 4),
        "loan_amount_fit": round(_loan_amount_fit(facts, profile), 4),
        "eligibility_fit": round(_eligibility_fit(facts, profile), 4),
        "priority_boost_fit": round(_priority_boost_fit(facts, profile), 4),
    }


def _improvement_tips(scheme_key: str, profile: Dict, breakdown: Dict[str, float]) -> List[str]:
    """Plain-language, rule-based notes on which axis is weakest and why --
    informational ("here's why the match isn't stronger"), never a
    suggestion to change who you are (e.g. never framed as "become SC/ST" or
    "become a woman" to qualify for a higher tier)."""
    facts = SCHEMES[scheme_key]
    tips: List[str] = []

    if breakdown["category_fit"] < 0.6 and facts.allowed_categories:
        tips.append(
            f"{facts.display_name} is limited to: {', '.join(facts.allowed_categories)} -- "
            f"your business category ('{profile.get('category')}') isn't one of them."
        )
    if breakdown["loan_amount_fit"] < 0.6 and facts.min_loan is not None and facts.max_loan is not None:
        tips.append(
            f"Your requested amount doesn't sit well inside {facts.display_name}'s typical "
            f"Rs.{facts.min_loan:,}-Rs.{facts.max_loan:,} range -- a different amount may fit better."
        )
    if breakdown["eligibility_fit"] < 1.0:
        unmet: List[str] = []
        if facts.requires_new_business and not profile.get("is_new_business"):
            unmet.append("requires a brand-new (not yet started) business")
        if facts.requires_sc_st_or_woman and not (profile.get("is_sc_st") or profile.get("gender") == "female"):
            unmet.append("requires an SC/ST or woman applicant")
        if facts.women_only and profile.get("gender") != "female":
            unmet.append("is open only to women entrepreneurs")
        if facts.max_annual_family_income is not None:
            cap = (
                facts.max_annual_family_income_sc_st
                if (profile.get("is_sc_st") and facts.max_annual_family_income_sc_st is not None)
                else facts.max_annual_family_income
            )
            if profile.get("annual_family_income", 0) > cap:
                unmet.append(f"requires annual family income under Rs.{cap:,}")
        if unmet:
            tips.append(f"{facts.display_name} " + "; and ".join(unmet) + ".")
    if breakdown["priority_boost_fit"] == 0.0:
        tips.append(
            f"{facts.display_name} offers a higher subsidy/coverage tier for SC/ST or women "
            f"applicants -- this profile doesn't currently qualify for that higher tier, which "
            f"is part of why the overall match isn't stronger."
        )

    return tips[:3]


def predict_ranked_schemes(profile: Dict, top_k: int = 3) -> List[Dict]:
    """profile keys: category, is_new_business (bool), years_operating (int),
    gender ('male'|'female'), is_sc_st (bool), location_type
    ('urban'|'rural'|'semi-urban'), annual_family_income (int),
    monthly_revenue (int), requested_amount (int), margin_capital (int).

    Returns a list of {scheme, display_name, confidence, why, url,
    match_breakdown, improvement_tips}, ranked by the model's predicted
    probability, highest first.
    """
    bundle = _load()
    pipeline = bundle["pipeline"]
    feature_columns = bundle["feature_columns"]

    row = dict(profile)
    row["is_new_business"] = int(bool(row.get("is_new_business")))
    row["is_sc_st"] = int(bool(row.get("is_sc_st")))
    X = pd.DataFrame([{col: row.get(col) for col in feature_columns}])

    proba = pipeline.predict_proba(X)[0]
    classes = pipeline.named_steps["classifier"].classes_

    ranked = sorted(zip(classes, proba), key=lambda kv: kv[1], reverse=True)[:top_k]

    results = []
    for scheme_key, confidence in ranked:
        facts = SCHEMES[scheme_key]
        breakdown = _match_breakdown(scheme_key, profile)
        results.append(
            {
                "scheme": scheme_key,
                "display_name": facts.display_name,
                "confidence": round(float(confidence), 4),
                "why": _why_bullets(scheme_key, profile),
                "url": facts.url,
                "match_breakdown": breakdown,
                "improvement_tips": _improvement_tips(scheme_key, profile, breakdown),
            }
        )
    return results


def model_feature_importance() -> Optional[Dict[str, float]]:
    bundle = _load()
    return bundle.get("grouped_importance")
