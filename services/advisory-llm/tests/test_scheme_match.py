"""Coverage for the trained scheme-match classifier (app/scheme_match.py) and
the /scheme-match endpoint. These tests need the trained artifact at
models/scheme_match.joblib — run `python train/generate_training_data.py &&
python train/train_scheme_match.py` first (the Dockerfile does this at build
time; see the module docstring in app/scheme_match.py)."""

import pytest
from fastapi.testclient import TestClient

from app import scheme_match
from app.main import app
from app.scheme_facts import SCHEMES

client = TestClient(app)

pytestmark = pytest.mark.skipif(
    not scheme_match.is_model_available(),
    reason="models/scheme_match.joblib not trained — run the train/ scripts first",
)

RURAL_SC_ST_WOMAN_DAIRY = {
    "category": "dairy",
    "is_new_business": False,
    "years_operating": 2,
    "gender": "female",
    "is_sc_st": True,
    "location_type": "rural",
    "annual_family_income": 90000,
    "monthly_revenue": 15000,
    "requested_amount": 150000,
    "margin_capital": 20000,
}

NEW_URBAN_FOOD_PROCESSING = {
    "category": "food-processing",
    "is_new_business": True,
    "years_operating": 0,
    "gender": "male",
    "is_sc_st": False,
    "location_type": "urban",
    "annual_family_income": 400000,
    "monthly_revenue": 0,
    "requested_amount": 800000,
    "margin_capital": 150000,
}


def test_predict_ranked_schemes_returns_known_scheme_keys():
    results = scheme_match.predict_ranked_schemes(RURAL_SC_ST_WOMAN_DAIRY, top_k=3)
    assert results
    assert len(results) <= 3
    for r in results:
        assert r["scheme"] in SCHEMES
        assert 0.0 <= r["confidence"] <= 1.0
        assert r["why"]
        assert r["url"] == SCHEMES[r["scheme"]].url


def test_confidences_are_sorted_descending():
    results = scheme_match.predict_ranked_schemes(NEW_URBAN_FOOD_PROCESSING, top_k=3)
    confidences = [r["confidence"] for r in results]
    assert confidences == sorted(confidences, reverse=True)


def test_scheme_match_endpoint_matches_contract_shape():
    resp = client.post("/scheme-match", json=RURAL_SC_ST_WOMAN_DAIRY)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"request_id", "results", "model_feature_importance"}
    assert body["request_id"]
    assert body["results"]
    for r in body["results"]:
        assert set(r) == {
            "scheme", "display_name", "confidence", "why", "url",
            "match_breakdown", "improvement_tips", "documents", "apply_process",
        }
        assert set(r["match_breakdown"]) == {
            "category_fit", "loan_amount_fit", "eligibility_fit", "priority_boost_fit",
        }
    assert isinstance(body["model_feature_importance"], dict)
    assert body["model_feature_importance"]


def test_scheme_match_documents_and_apply_process_are_populated():
    """documents/apply_process come straight from scheme_facts.py, which has
    real (non-empty) values for every scheme in SCHEMES -- so any result
    should carry them through, not just PMEGP specifically."""
    resp = client.post("/scheme-match", json=RURAL_SC_ST_WOMAN_DAIRY)
    body = resp.json()
    for r in body["results"]:
        facts = SCHEMES[r["scheme"]]
        assert r["documents"] == facts.documents
        assert r["documents"]
        assert r["apply_process"] == facts.apply_process
        assert r["apply_process"]


def test_pmegp_documents_and_apply_process_match_scheme_facts():
    facts = SCHEMES["PMEGP"]
    result = next((r for r in scheme_match.predict_ranked_schemes(NEW_URBAN_FOOD_PROCESSING, top_k=6) if r["scheme"] == "PMEGP"), None)
    assert result is not None
    assert result["documents"] == facts.documents
    assert result["apply_process"] == facts.apply_process


def test_scheme_match_endpoint_rejects_missing_fields():
    resp = client.post("/scheme-match", json={"category": "dairy"})
    assert resp.status_code == 422


def test_model_feature_importance_is_populated():
    importance = scheme_match.model_feature_importance()
    assert importance
    assert all(0.0 <= v <= 1.0 for v in importance.values())


def test_match_breakdown_and_improvement_tips_present_and_bounded():
    profile = {
        "category": "tailoring",
        "is_new_business": True,
        "years_operating": 0,
        "gender": "male",
        "is_sc_st": False,
        "location_type": "urban",
        "annual_family_income": 500000,
        "monthly_revenue": 0,
        "requested_amount": 9000000,
        "margin_capital": 200000,
    }
    results = scheme_match.predict_ranked_schemes(profile, top_k=3)
    for r in results:
        assert set(r["match_breakdown"]) == {
            "category_fit", "loan_amount_fit", "eligibility_fit", "priority_boost_fit",
        }
        for v in r["match_breakdown"].values():
            assert 0.0 <= v <= 1.0
        assert isinstance(r["improvement_tips"], list)
        assert len(r["improvement_tips"]) <= 3
