from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_calculator_endpoint_happy_path():
    response = client.post(
        "/calculator",
        json={"margin_capital": 50_000, "category": "dairy", "location": "Rampur"},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["project_cost"] == 500_000
    assert body["scheme_selected"]["name"] == "Term Loan Scheme"
    assert body["loan_amount"] == 450_000
    assert body["working_capital"] == 125_000
    assert len(body["emi_schedule"]) == 90
    assert body["emi_schedule"][-1]["outstanding_balance"] == 0
    assert isinstance(body["request_id"], str) and body["request_id"]


def test_calculator_endpoint_rejects_zero_margin_capital():
    response = client.post(
        "/calculator",
        json={"margin_capital": 0, "category": "dairy"},
    )

    assert response.status_code == 422
