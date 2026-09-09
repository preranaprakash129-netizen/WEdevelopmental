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


def test_feasibility_unknown_location_returns_valid_shape_with_empty_competitors():
    resp = client.post(
        "/feasibility",
        json={"location": "Nowhereville", "category": "handicrafts", "margin_capital": 10000},
    )
    assert resp.status_code == 200
    assert resp.json()["competitor_list"] == []


def test_confidence_range_narrower_when_location_and_category_data_both_match():
    known = client.post(
        "/feasibility",
        json={"location": "Rampur", "category": "dairy", "margin_capital": 50000},
    ).json()
    unknown = client.post(
        "/feasibility",
        json={"location": "Nowhereville", "category": "handicrafts", "margin_capital": 10000},
    ).json()

    known_spread = known["confidence_range"]["high"] - known["confidence_range"]["low"]
    unknown_spread = unknown["confidence_range"]["high"] - unknown["confidence_range"]["low"]
    assert known_spread < unknown_spread


def test_real_seed_data_produces_distinct_sensible_scores():
    combos = [
        ("Rampur", "dairy", 50000),
        ("Rampur", "tailoring", 20000),
        ("Sundarpur", "food-processing", 80000),
    ]
    results = []
    for location, category, margin_capital in combos:
        resp = client.post(
            "/feasibility",
            json={"location": location, "category": category, "margin_capital": margin_capital},
        )
        assert resp.status_code == 200
        results.append(resp.json())

    scores = [r["feasibility_score"] for r in results]
    assert len(set(scores)) == len(scores), "expected each combination to score differently"

    for r in results:
        assert 0 <= r["feasibility_score"] <= 100
        assert r["confidence_range"]["low"] <= r["feasibility_score"] <= r["confidence_range"]["high"]
        assert r["competitor_list"], "real seed data has competitors in these categories"
        assert r["swot"]["strengths"] or r["swot"]["weaknesses"]
