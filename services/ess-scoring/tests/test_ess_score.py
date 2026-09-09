import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.scoring import SUBSCORE_WEIGHTS, _FEATURE_SUBSCORE

client = TestClient(app)

VALID_PROFILE_REQUEST = {
    "profile_data": {
        "category": "tailoring",
        "years_operating": 2,
        "monthly_revenue": 18000,
        "employee_count": 1,
        "has_bank_account": True,
    }
}


def test_profile_data_returns_contract_shaped_response():
    resp = client.post("/ess-score", json=VALID_PROFILE_REQUEST)
    assert resp.status_code == 200
    body = resp.json()

    uuid.UUID(body["request_id"])  # raises if not a valid uuid

    assert 0 <= body["ess_score"] <= 100

    sub_scores = body["sub_scores"]
    for key in ("financial_health", "market_stability", "operational_maturity", "growth_potential"):
        assert key in sub_scores
        assert 0 <= sub_scores[key] <= 100

    attribution = body["attribution"]
    assert len(attribution) > 0
    impacts_desc = [abs(item["impact"]) for item in attribution]
    assert impacts_desc == sorted(impacts_desc, reverse=True)

    action = body["top_improvement_action"]
    assert isinstance(action["action"], str) and action["action"]
    assert isinstance(action["expected_score_delta"], (int, float))


def test_business_id_lookup_returns_200():
    resp = client.post("/ess-score", json={"business_id": "biz_001"})
    assert resp.status_code == 200
    assert "ess_score" in resp.json()


def test_unknown_business_id_returns_404_with_error_envelope():
    resp = client.post("/ess-score", json={"business_id": "does_not_exist"})
    assert resp.status_code == 404
    body = resp.json()
    assert "error" in body
    assert "code" in body["error"] and "message" in body["error"]


def test_neither_field_returns_422():
    resp = client.post("/ess-score", json={})
    assert resp.status_code == 422
    assert "error" in resp.json()


def test_both_fields_returns_422():
    resp = client.post(
        "/ess-score",
        json={"business_id": "biz_001", **VALID_PROFILE_REQUEST},
    )
    assert resp.status_code == 422
    assert "error" in resp.json()


def test_subscore_weights_sum_to_one():
    assert sum(SUBSCORE_WEIGHTS.values()) == 1.0


def test_higher_revenue_increases_financial_health_and_ess_score():
    low_revenue = {**VALID_PROFILE_REQUEST["profile_data"], "monthly_revenue": 5000}
    high_revenue = {**VALID_PROFILE_REQUEST["profile_data"], "monthly_revenue": 80000}

    low_body = client.post("/ess-score", json={"profile_data": low_revenue}).json()
    high_body = client.post("/ess-score", json={"profile_data": high_revenue}).json()

    assert high_body["sub_scores"]["financial_health"] > low_body["sub_scores"]["financial_health"]
    assert high_body["ess_score"] > low_body["ess_score"]


def test_missing_bank_account_lowers_financial_health():
    with_account = {**VALID_PROFILE_REQUEST["profile_data"], "has_bank_account": True}
    without_account = {**VALID_PROFILE_REQUEST["profile_data"], "has_bank_account": False}

    with_body = client.post("/ess-score", json={"profile_data": with_account}).json()
    without_body = client.post("/ess-score", json={"profile_data": without_account}).json()

    assert with_body["sub_scores"]["financial_health"] > without_body["sub_scores"]["financial_health"]


def test_attribution_covers_every_mapped_feature_exactly_once():
    resp = client.post("/ess-score", json=VALID_PROFILE_REQUEST)
    attributed_features = {item["feature"] for item in resp.json()["attribution"]}
    assert attributed_features == set(_FEATURE_SUBSCORE)


def test_attribution_sums_to_ess_score_minus_neutral_baseline():
    resp = client.post("/ess-score", json=VALID_PROFILE_REQUEST).json()
    total_impact = sum(item["impact"] for item in resp["attribution"])
    assert total_impact == pytest.approx(resp["ess_score"] - 50, abs=0.05)


def test_unknown_category_falls_back_to_default_stability():
    resp = client.post(
        "/ess-score",
        json={"profile_data": {**VALID_PROFILE_REQUEST["profile_data"], "category": "space-tourism"}},
    )
    assert resp.status_code == 200
    assert 0 <= resp.json()["sub_scores"]["market_stability"] <= 100
