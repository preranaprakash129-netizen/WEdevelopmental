"""
Confirms backend-api's /api/ess-score route (the only path the frontend is allowed to
call per docs/api-contract.md > Orchestration) forwards the intake profile fields to
ess-scoring's /ess-score as profile_data, unmodified -- and never substitutes a
business_id. Guards against a regression where the gateway route starts mutating or
partially forwarding the payload as more fields get added to the wizard.

Downstream ess-scoring is mocked (`app.main.httpx.post` is monkeypatched) so this test
doesn't need ess-scoring actually running -- it only exercises backend-api's own
proxying/error-handling logic.
"""

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

INTAKE_PROFILE_REQUEST = {
    "profile_data": {
        "category": "tailoring",
        "years_operating": 2,
        "monthly_revenue": 18000,
        "employee_count": 1,
        "has_bank_account": True,
    }
}

FAKE_ESS_SCORE_RESPONSE = {
    "request_id": "11111111-1111-1111-1111-111111111111",
    "ess_score": 58.4,
    "sub_scores": {
        "financial_health": 50.0,
        "market_stability": 60.0,
        "operational_maturity": 55.0,
        "growth_potential": 61.0,
    },
    "attribution": [{"feature": "monthly_revenue", "impact": 3.1}],
    "top_improvement_action": {
        "action": "Increase monthly revenue through additional sales channels",
        "expected_score_delta": 5.0,
    },
}


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_ess_score_proxy_forwards_intake_profile_data_unmodified(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return _FakeResponse(200, FAKE_ESS_SCORE_RESPONSE)

    monkeypatch.setattr("app.main.httpx.post", fake_post)

    resp = client.post("/api/ess-score", json=INTAKE_PROFILE_REQUEST)

    assert resp.status_code == 200
    assert resp.json() == FAKE_ESS_SCORE_RESPONSE
    assert captured["url"].endswith("/ess-score")
    assert captured["json"] == INTAKE_PROFILE_REQUEST
    assert "business_id" not in captured["json"]


def test_ess_score_proxy_returns_503_when_ess_scoring_unreachable(monkeypatch):
    def fake_post(url, json, timeout):
        raise httpx.RequestError("connection refused", request=None)

    monkeypatch.setattr("app.main.httpx.post", fake_post)

    resp = client.post("/api/ess-score", json=INTAKE_PROFILE_REQUEST)

    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "ess_scoring_unavailable"


@pytest.mark.parametrize("bad_payload", [{}, {"business_id": "biz_001", **INTAKE_PROFILE_REQUEST}])
def test_ess_score_proxy_passes_through_whatever_it_is_given(monkeypatch, bad_payload):
    """backend-api itself does no validation on this route -- ess-scoring owns
    request-shape validation per the contract. This just documents that the proxy
    forwards verbatim rather than silently coercing a bad payload into something valid."""
    captured = {}

    def fake_post(url, json, timeout):
        captured["json"] = json
        return _FakeResponse(422, {"error": {"code": "validation_error", "message": "bad"}})

    monkeypatch.setattr("app.main.httpx.post", fake_post)

    resp = client.post("/api/ess-score", json=bad_payload)

    assert resp.status_code == 422
    assert captured["json"] == bad_payload
