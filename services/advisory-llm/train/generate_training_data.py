"""Builds the labeled training set for the scheme-match classifier.

Honesty note, worth keeping front and center when presenting this: there is no
public dataset of real PMEGP/MUDRA/etc. loan applications with outcomes to train
on. So this generates synthetic business profiles and labels each with the
scheme a *real eligibility-rules engine* (built from services/advisory-llm/app/
scheme_facts.py, which is itself sourced from the official scheme pages) says
best fits -- then a classifier is trained to approximate that labeling function
from the profile features. That's a legitimate, common technique (rule
distillation / learning-to-rank a known policy) and it buys three real things a
hardcoded if/else chain doesn't: the model generalizes to feature combinations
never explicitly enumerated, it ranks *all* schemes with a confidence score
rather than returning one hard answer, and it exposes feature importances for
explainability. It does NOT mean the model has learned anything about real-world
loan approval odds -- say that plainly if asked, rather than letting a judge
infer "real applicant outcomes" from the word "trained".

Run:
    python generate_training_data.py            # writes training_data.csv
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.scheme_facts import SCHEMES, SchemeFacts  # noqa: E402

CATEGORIES = ["dairy", "tailoring", "handicrafts", "food-processing", "retail-kirana", "poultry"]
LOCATION_TYPES = ["urban", "rural", "semi-urban"]

N_SAMPLES = 12000
RNG_SEED = 42


def is_eligible(scheme: SchemeFacts, profile: Dict) -> bool:
    if scheme.requires_new_business and not profile["is_new_business"]:
        return False
    if scheme.requires_sc_st_or_woman and not (profile["is_sc_st"] or profile["gender"] == "female"):
        return False
    if scheme.women_only and profile["gender"] != "female":
        return False
    if scheme.allowed_categories is not None and profile["category"] not in scheme.allowed_categories:
        return False
    if not (scheme.min_loan <= profile["requested_amount"] <= scheme.max_loan):
        return False
    if scheme.max_annual_family_income is not None:
        cap = (
            scheme.max_annual_family_income_sc_st
            if profile["is_sc_st"] and scheme.max_annual_family_income_sc_st is not None
            else scheme.max_annual_family_income
        )
        if profile["annual_family_income"] > cap:
            return False
    return True


def fit_score(scheme: SchemeFacts, profile: Dict, rng: random.Random) -> float:
    score = 0.0

    if scheme.key == "PMEGP":
        special = profile["is_sc_st"] or profile["gender"] == "female"
        if profile["location_type"] == "rural":
            score += 35.0 if special else 25.0
        else:
            score += 25.0 if special else 15.0
    elif scheme.key == "PMFME":
        score += 35.0  # already gated to food-processing/dairy by allowed_categories
    elif scheme.key == "Karnataka Udyogini":
        score += 50.0 if profile["is_sc_st"] else 30.0
    elif scheme.key == "MUDRA":
        score += 22.0  # reliable, low-friction default for smaller tickets
    elif scheme.key == "Stand-Up India":
        score += 32.0  # attractive for large greenfield tickets when eligible
    elif scheme.key == "CGTMSE":
        score += 14.0
        if profile["requested_amount"] >= 2_000_000 and not profile["is_new_business"]:
            score += 22.0  # genuinely the better fit for a bigger, collateral-free expansion loan

    mid = (scheme.min_loan + min(scheme.max_loan, 10_000_000)) / 2.0
    span = max(1.0, min(scheme.max_loan, 10_000_000) - scheme.min_loan)
    loan_fit = 1.0 - min(1.0, abs(profile["requested_amount"] - mid) / span)
    score += 10.0 * loan_fit

    score += rng.gauss(0, 3.0)  # realistic ambiguity between close options
    return score


def label_profile(profile: Dict, rng: random.Random) -> Optional[str]:
    eligible = [s for s in SCHEMES.values() if is_eligible(s, profile)]
    if not eligible:
        return None
    scored = [(s.key, fit_score(s, profile, rng)) for s in eligible]
    scored.sort(key=lambda kv: kv[1], reverse=True)
    return scored[0][0]


def sample_profile(rng: random.Random) -> Dict:
    category = rng.choice(CATEGORIES)
    is_new_business = rng.random() < 0.55
    years_operating = 0 if is_new_business else rng.randint(1, 15)
    gender = rng.choice(["female", "male"])
    is_sc_st = rng.random() < 0.25
    location_type = rng.choice(LOCATION_TYPES)
    annual_family_income = rng.randint(40_000, 400_000)
    monthly_revenue = 0 if is_new_business else rng.randint(5_000, 150_000)

    # Requested amount skewed toward smaller tickets (realistic for microenterprises)
    # with a long tail up to 80 lakh so Stand-Up India / CGTMSE territory is covered.
    requested_amount = int(rng.lognormvariate(12.8, 1.0))
    requested_amount = max(20_000, min(requested_amount, 8_000_000))

    margin_capital = int(requested_amount * rng.uniform(0.05, 0.35))

    return {
        "category": category,
        "is_new_business": is_new_business,
        "years_operating": years_operating,
        "gender": gender,
        "is_sc_st": is_sc_st,
        "location_type": location_type,
        "annual_family_income": annual_family_income,
        "monthly_revenue": monthly_revenue,
        "requested_amount": requested_amount,
        "margin_capital": margin_capital,
    }


def main() -> None:
    rng = random.Random(RNG_SEED)
    out_path = Path(__file__).resolve().parent / "training_data.csv"

    rows: List[Dict] = []
    skipped = 0
    while len(rows) < N_SAMPLES:
        profile = sample_profile(rng)
        label = label_profile(profile, rng)
        if label is None:
            skipped += 1
            continue
        profile["label"] = label
        rows.append(profile)

    fieldnames = [
        "category", "is_new_business", "years_operating", "gender", "is_sc_st",
        "location_type", "annual_family_income", "monthly_revenue",
        "requested_amount", "margin_capital", "label",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    label_counts = {}
    for r in rows:
        label_counts[r["label"]] = label_counts.get(r["label"], 0) + 1

    print(f"Wrote {len(rows)} rows to {out_path} ({skipped} sampled profiles had no eligible scheme, discarded)")
    print("Label distribution:")
    for label, count in sorted(label_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {label:20s} {count:5d} ({100*count/len(rows):.1f}%)")


if __name__ == "__main__":
    main()
