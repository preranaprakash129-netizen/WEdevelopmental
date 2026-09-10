"""RAG-mode assembly: retrieval in, grounded citations out.

The model call itself is monkeypatched — these tests cover the wiring we own
(what reaches the prompt, how cited ids become cited_sources, what happens when
nothing is grounded), not Claude's behaviour.
"""

import json

import pytest
from fastapi.testclient import TestClient

from app import advisor
from app.advisor import GroundedAnswer, _sources_from_ids, _user_block
from app.main import app
from app.retrieval import Chunk, ScoredChunk

client = TestClient(app)

PMEGP_CHUNK = Chunk(
    id="pmegp-p0001-00",
    scheme="PMEGP",
    document="PMEGP Guidelines",
    url="https://kviconline.gov.in/pmegp",
    page=14,
    text="Applications under PMEGP are submitted online and routed to the district KVIC office.",
)
PMEGP_CHUNK_2 = Chunk(
    id="pmegp-p0002-00",
    scheme="PMEGP",
    document="PMEGP Guidelines",
    url="https://kviconline.gov.in/pmegp",
    page=15,
    text="The district task force committee interviews applicants before the bank appraisal.",
)
MUDRA_CHUNK = Chunk(
    id="mudra-p0002-00",
    scheme="MUDRA",
    document="Pradhan Mantri MUDRA Yojana",
    url="https://www.mudra.org.in/",
    page=2,
    text="MUDRA loans are extended through banks and grouped as Shishu, Kishore and Tarun.",
)
HITS = [ScoredChunk(PMEGP_CHUNK, 4.0), ScoredChunk(PMEGP_CHUNK_2, 2.0), ScoredChunk(MUDRA_CHUNK, 1.0)]


@pytest.fixture
def rag_corpus(monkeypatch, tmp_path):
    """Run the service in rag mode against a two-document corpus."""
    chunks_path = tmp_path / "chunks.jsonl"
    chunks_path.write_text(
        "\n".join(
            json.dumps(chunk.__dict__, ensure_ascii=False)
            for chunk in (PMEGP_CHUNK, PMEGP_CHUNK_2, MUDRA_CHUNK)
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("ADVISORY_MODE", "rag")
    monkeypatch.setenv("ADVISORY_CORPUS_DIR", str(tmp_path))
    return tmp_path


def test_sources_from_ids_dedupes_by_document():
    # Two chunks of the same PDF are one citation, not two.
    sources = _sources_from_ids(["pmegp-p0001-00", "pmegp-p0002-00"], HITS)
    assert sources == [
        {
            "scheme": "PMEGP",
            "document": "PMEGP Guidelines",
            "url": "https://kviconline.gov.in/pmegp",
        }
    ]


def test_sources_from_ids_drops_ids_that_were_never_retrieved():
    sources = _sources_from_ids(["not-a-real-id", "mudra-p0002-00"], HITS)
    assert [s["scheme"] for s in sources] == ["MUDRA"]


def test_sources_preserve_citation_order():
    sources = _sources_from_ids(["mudra-p0002-00", "pmegp-p0001-00"], HITS)
    assert [s["scheme"] for s in sources] == ["MUDRA", "PMEGP"]


def test_user_block_labels_every_extract_with_its_id_and_page():
    block = _user_block("How do I apply?", "hi", HITS)
    assert "Answer in: Hindi (hi)" in block
    assert "[pmegp-p0001-00] PMEGP — PMEGP Guidelines (page 14)" in block
    assert "How do I apply?" in block


def test_rag_mode_without_a_corpus_answers_honestly(monkeypatch, tmp_path):
    monkeypatch.setenv("ADVISORY_MODE", "rag")
    monkeypatch.setenv("ADVISORY_CORPUS_DIR", str(tmp_path))

    def fail(**kwargs):
        raise AssertionError("the model should not be called when retrieval is empty")

    monkeypatch.setattr(advisor, "_generate", fail)

    body = client.post("/advisory-chat", json={"message": "Am I eligible for PMEGP?"}).json()
    assert body["cited_sources"] == []
    assert "don't have" in body["response_text"]


def test_rag_mode_returns_citations_for_the_chunks_the_model_used(rag_corpus, monkeypatch):
    captured = {}

    def fake_generate(**kwargs):
        captured.update(kwargs)
        return GroundedAnswer(
            answer="Apply online, then your district KVIC office takes it forward.",
            cited_chunk_ids=["pmegp-p0001-00"],
            grounded=True,
        )

    monkeypatch.setattr(advisor, "_generate", fake_generate)

    body = client.post(
        "/advisory-chat", json={"message": "How do I apply for PMEGP?"}
    ).json()

    assert body["cited_sources"] == [
        {
            "scheme": "PMEGP",
            "document": "PMEGP Guidelines",
            "url": "https://kviconline.gov.in/pmegp",
        }
    ]
    # Retrieval ran and the PMEGP chunks actually reached the prompt.
    assert any(hit.chunk.scheme == "PMEGP" for hit in captured["hits"])
    assert captured["language"] == "en"


def test_ungrounded_answer_returns_no_citations(rag_corpus, monkeypatch):
    monkeypatch.setattr(
        advisor,
        "_generate",
        lambda **kwargs: GroundedAnswer(
            answer="I don't have that in my scheme documents.",
            # Even if the model names chunks, an ungrounded answer cites nothing.
            cited_chunk_ids=["pmegp-p0001-00"],
            grounded=False,
        ),
    )

    body = client.post("/advisory-chat", json={"message": "What is the GST rate?"}).json()
    assert body["cited_sources"] == []


def test_rag_mode_generates_in_the_detected_language(rag_corpus, monkeypatch):
    captured = {}

    def fake_generate(**kwargs):
        captured.update(kwargs)
        return GroundedAnswer(answer="ऑनलाइन आवेदन करें।", cited_chunk_ids=[], grounded=True)

    monkeypatch.setattr(advisor, "_generate", fake_generate)

    body = client.post(
        "/advisory-chat", json={"message": "PMEGP ke liye kaise apply karein?"}
    ).json()

    # No Bhashini key, so we ask for the answer in Hindi directly rather than
    # generating English and translating.
    assert captured["language"] == "hi"
    assert body["detected_language"] == "hi"


def test_llm_failure_maps_to_the_contract_error_shape(rag_corpus, monkeypatch):
    def boom(**kwargs):
        raise advisor.AdvisoryError("llm_unreachable", "Could not reach the API.", status_code=503)

    monkeypatch.setattr(advisor, "_generate", boom)

    resp = client.post("/advisory-chat", json={"message": "How do I apply for PMEGP?"})
    assert resp.status_code == 503
    assert set(resp.json()["error"]) == {"code", "message"}


def test_missing_credentials_maps_to_the_contract_error_shape(rag_corpus, monkeypatch):
    # This is the real failure the anthropic SDK raises when no credential
    # source resolves at all — a client-side TypeError before any HTTP call,
    # not anthropic.AuthenticationError. _generate must still map it to the
    # contract's error shape instead of letting it escape as a bare 500.
    import anthropic

    def no_credentials(*args, **kwargs):
        raise TypeError(
            "Could not resolve authentication method. Expected one of api_key, "
            "auth_token, or credentials to be set."
        )

    monkeypatch.setattr(anthropic, "Anthropic", no_credentials)

    resp = client.post("/advisory-chat", json={"message": "How do I apply for PMEGP?"})
    assert resp.status_code == 503
    body = resp.json()
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == "llm_unauthenticated"


def test_unrelated_type_error_is_not_swallowed_as_a_credentials_error(rag_corpus, monkeypatch):
    import anthropic

    def broken(*args, **kwargs):
        raise TypeError("unsupported operand type(s) for +: 'int' and 'str'")

    monkeypatch.setattr(anthropic, "Anthropic", broken)

    with pytest.raises(TypeError):
        client.post("/advisory-chat", json={"message": "How do I apply for PMEGP?"})
