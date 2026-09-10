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


def predict_ranked_schemes(profile: Dict, top_k: int = 3) -> List[Dict]:
    """profile keys: category, is_new_business (bool), years_operating (int),
    gender ('male'|'female'), is_sc_st (bool), location_type
    ('urban'|'rural'|'semi-urban'), annual_family_income (int),
    monthly_revenue (int), requested_amount (int), margin_capital (int).

    Returns a list of {scheme, display_name, confidence, why, url}, ranked by
    the model's predicted probability, highest first.
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
        results.append(
            {
                "scheme": scheme_key,
                "display_name": facts.display_name,
                "confidence": round(float(confidence), 4),
                "why": _why_bullets(scheme_key, profile),
                "url": facts.url,
            }
        )
    return results


def model_feature_importance() -> Optional[Dict[str, float]]:
    bundle = _load()
    return bundle.get("grouped_importance")
