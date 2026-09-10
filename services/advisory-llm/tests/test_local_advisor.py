"""Coverage for the local (no-API) chatbot: app/local_advisor.py, which routes
a question through the trained scheme+intent classifiers (see
train/train_local_advisor.py) and answers from the structured facts in
app/scheme_facts.py — never from generated text. Needs the trained artifact
at models/local_advisor.joblib (Dockerfile trains it at build time; run
`python train/train_local_advisor.py` locally otherwise)."""

import pytest
from fastapi.testclient import TestClient

from app import local_advisor
from app.main import app

client = TestClient(app)

pytestmark = pytest.mark.skipif(
    not local_advisor.is_model_available(),
    reason="models/local_advisor.joblib not trained — run train/train_local_advisor.py first",
)


def test_eligibility_question_cites_the_right_scheme():
    result = local_advisor.answer("Am I eligible for PMEGP?")
    assert [s["scheme"] for s in result["cited_sources"]] == ["PMEGP"]
    assert "PMEGP" in result["response_text"] or "Employment Generation" in result["response_text"]


def test_apply_process_question_names_the_process():
    result = local_advisor.answer("How do I apply for MUDRA?")
    assert [s["scheme"] for s in result["cited_sources"]] == ["MUDRA"]


def test_out_of_domain_question_is_rejected_honestly():
    # Regression test for a real bug found during development: an early
    # version of the classifier confidently answered PMEGP::eligibility for
    # this because closed-set classifiers always pick their nearest class
    # without explicit negative examples. Fixed by adding a genuine
    # GENERAL::unclear training class (see train/chat_training_examples.py) —
    # not by raising the confidence threshold.
    result = local_advisor.answer(
        "What is the airspeed velocity of an unladen swallow?"
    )
    assert result["cited_sources"] == []


def test_greeting_gets_a_greeting_not_a_scheme_answer():
    result = local_advisor.answer("hi there, thanks!")
    assert result["cited_sources"] == []


def test_advisory_chat_endpoint_uses_local_ml_and_cites_sources(monkeypatch):
    monkeypatch.delenv("ADVISORY_MODE", raising=False)
    resp = client.post("/advisory-chat", json={"message": "What documents do I need for PMEGP?"})
    assert resp.status_code == 200
    body = resp.json()
    assert [s["scheme"] for s in body["cited_sources"]] == ["PMEGP"]


def test_kannada_language_gets_kannada_answer_text():
    result = local_advisor.answer("Am I eligible for PMEGP?", language="kn")
    assert [s["scheme"] for s in result["cited_sources"]] == ["PMEGP"]
    assert "PMEGP" in result["response_text"]
    # Kannada script present, not just the English template reused
    assert any("ಀ" <= ch <= "೿" for ch in result["response_text"])


def test_default_language_is_still_english():
    result = local_advisor.answer("Am I eligible for PMEGP?")
    assert "open to general applicants" in result["response_text"]
