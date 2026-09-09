from fastapi.testclient import TestClient

from app.conversation import get_store
from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_advisory_chat_matches_contract_shape():
    # The exact example request from docs/api-contract.md.
    resp = client.post(
        "/advisory-chat",
        json={
            "message": "PMEGP ke liye kaise apply karein?",
            "context": {"conversation_id": "conv_8841"},
        },
    )
    assert resp.status_code == 200
    body = resp.json()

    assert set(body) == {"request_id", "response_text", "cited_sources", "detected_language"}
    assert body["request_id"]
    assert isinstance(body["response_text"], str) and body["response_text"]
    assert isinstance(body["cited_sources"], list)
    for source in body["cited_sources"]:
        assert set(source) <= {"scheme", "document", "url"}
        assert {"scheme", "document"} <= set(source)
    assert body["detected_language"] == "hi"


def test_request_id_is_unique_per_response():
    payload = {"message": "How do I apply for MUDRA?"}
    first = client.post("/advisory-chat", json=payload).json()
    second = client.post("/advisory-chat", json=payload).json()
    assert first["request_id"] != second["request_id"]


def test_pmegp_question_cites_pmegp():
    resp = client.post("/advisory-chat", json={"message": "Am I eligible for PMEGP?"})
    body = resp.json()
    assert [s["scheme"] for s in body["cited_sources"]] == ["PMEGP"]
    assert body["detected_language"] == "en"


def test_question_with_no_scheme_returns_empty_cited_sources():
    # The contract allows an empty array; make sure we send [] rather than
    # dropping the key or inventing a citation.
    resp = client.post("/advisory-chat", json={"message": "I want to start a small business"})
    body = resp.json()
    assert body["cited_sources"] == []


def test_explicit_language_overrides_detection():
    resp = client.post(
        "/advisory-chat",
        json={"message": "PMEGP ke liye kaise apply karein?", "language": "en"},
    )
    assert resp.json()["detected_language"] == "en"


def test_conversation_id_accumulates_history():
    client.post("/advisory-chat", json={"message": "What is PMEGP?", "context": {"conversation_id": "conv_1"}})
    client.post("/advisory-chat", json={"message": "And MUDRA?", "context": {"conversation_id": "conv_1"}})

    history = get_store().history("conv_1", max_turns=10)
    assert [turn.role for turn in history] == ["user", "assistant", "user", "assistant"]


def test_requests_without_conversation_id_are_not_stored():
    client.post("/advisory-chat", json={"message": "What is PMEGP?"})
    assert get_store().history("", max_turns=10) == []


def test_missing_message_returns_contract_error_shape():
    resp = client.post("/advisory-chat", json={"context": {"conversation_id": "conv_1"}})
    assert resp.status_code == 422
    body = resp.json()
    assert set(body["error"]) == {"code", "message"}


def test_empty_message_is_rejected():
    resp = client.post("/advisory-chat", json={"message": ""})
    assert resp.status_code == 422
    assert set(resp.json()["error"]) == {"code", "message"}


def test_debug_status_reports_mock_mode_and_empty_corpus(monkeypatch, tmp_path):
    monkeypatch.setenv("ADVISORY_CORPUS_DIR", str(tmp_path))
    body = client.get("/debug/status").json()
    assert body["mode"] == "mock"
    assert body["corpus_chunks"] == 0
    assert body["translator"] == "passthrough"
