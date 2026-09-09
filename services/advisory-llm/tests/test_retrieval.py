import json

from app.retrieval import (
    BM25Retriever,
    Chunk,
    EmptyRetriever,
    get_retriever,
    load_chunks,
    tokenize,
)

CHUNKS = [
    Chunk(
        id="pmegp-p0001-00",
        scheme="PMEGP",
        document="PMEGP Guidelines",
        url="https://kviconline.gov.in/pmegp",
        page=1,
        text="Applications under PMEGP are submitted online and routed to the district KVIC office.",
    ),
    Chunk(
        id="mudra-p0002-00",
        scheme="MUDRA",
        document="Pradhan Mantri MUDRA Yojana",
        url="https://www.mudra.org.in/",
        page=2,
        text="MUDRA loans are extended through banks and are grouped as Shishu, Kishore and Tarun.",
    ),
    # A third, unrelated chunk. With only two documents, a term shared by both
    # (e.g. "are") gets a negative BM25 idf and can outweigh terms unique to the
    # matching document — a real degenerate case of the classic idf formula at
    # tiny corpus sizes, not something to work around with tolerant assertions.
    # A third document breaks the tie honestly.
    Chunk(
        id="ess-p0003-00",
        scheme="ESS",
        document="Entrepreneurial Sustainability Score Methodology",
        url=None,
        page=3,
        text="The sustainability score blends financial health and market stability.",
    ),
]


def test_tokenize_handles_devanagari():
    assert tokenize("मुद्रा loan") == ["मुद्रा", "loan"]


def test_bm25_ranks_the_matching_scheme_first():
    results = BM25Retriever(CHUNKS).search("How are MUDRA loans given out?", top_k=2)
    assert results
    assert results[0].chunk.scheme == "MUDRA"


def test_bm25_drops_zero_score_chunks():
    # No term overlaps either chunk, so nothing should be returned rather than
    # padding the prompt with irrelevant text.
    assert BM25Retriever(CHUNKS).search("zzzz qqqq", top_k=5) == []


def test_empty_retriever_returns_nothing():
    assert EmptyRetriever().search("PMEGP", top_k=5) == []


def test_load_chunks_missing_file_is_not_an_error(tmp_path):
    assert load_chunks(tmp_path / "chunks.jsonl") == []


def test_get_retriever_falls_back_to_empty_without_a_corpus(tmp_path):
    assert isinstance(get_retriever(tmp_path / "chunks.jsonl"), EmptyRetriever)


def test_get_retriever_builds_bm25_from_a_chunks_file(tmp_path):
    path = tmp_path / "chunks.jsonl"
    path.write_text(
        "\n".join(json.dumps(chunk.__dict__, ensure_ascii=False) for chunk in CHUNKS),
        encoding="utf-8",
    )
    retriever = get_retriever(path)
    assert isinstance(retriever, BM25Retriever)
    assert retriever.search("PMEGP district office", top_k=1)[0].chunk.scheme == "PMEGP"
