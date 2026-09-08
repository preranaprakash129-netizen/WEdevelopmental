from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_feasibility_matches_contract_shape():
    resp = client.post(
        "/feasibility",
        json={"location": "Rampur", "category": "dairy", "margin_capital": 50000},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert "request_id" in body
    assert set(body["market_reach"]) == {"estimated_customers", "radius_km"}
    assert isinstance(body["competitor_list"], list)
    for competitor in body["competitor_list"]:
        assert set(competitor) == {"name", "category", "distance_km"}
    assert set(body["swot"]) == {"strengths", "weaknesses", "opportunities", "threats"}
    assert set(body["pricing_bands"]) == {"low", "median", "high"}
    assert 0 <= body["feasibility_score"] <= 100
    assert body["confidence_range"]["low"] <= body["feasibility_score"] <= body["confidence_range"]["high"]


def test_feasibility_missing_field_returns_contract_error_shape():
    resp = client.post("/feasibility", json={"location": "Rampur", "category": "dairy"})
    assert resp.status_code == 422
    body = resp.json()
    assert set(body["error"]) == {"code", "message"}


def test_feasibility_unknown_location_still_returns_mock():
    resp = client.post(
        "/feasibility",
        json={"location": "Nowhereville", "category": "handicrafts", "margin_capital": 10000},
    )
    assert resp.status_code == 200
    assert resp.json()["competitor_list"]
