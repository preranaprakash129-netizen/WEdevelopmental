"""BM25 retrieval over ingested scheme-document chunks.

Keyword retrieval, not embeddings: it needs no model download, runs offline,
and is deterministic — when a judge asks why a particular circular was cited we
can point at the matched terms. The `Retriever` protocol is the seam to swap in
a vector or hybrid retriever later without touching `advisor.py`.
"""

from __future__ import annotations

import json
import re
import string
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Protocol, Tuple

# Deliberately not \w+: Python's re module excludes combining marks (Unicode
# category Mn) from \w, which splits Devanagari/Bengali/Tamil vowel signs off
# their base consonant — "मुद्रा" would tokenize as ['म', 'द', 'र']. Splitting on
# whitespace and punctuation instead keeps a script's combining marks attached
# to the token they belong to.
_PUNCTUATION_CHARS = string.punctuation + "।॥‘’“”…–—"
_TOKEN_RE = re.compile(rf"[^\s{re.escape(_PUNCTUATION_CHARS)}]+", re.UNICODE)


def tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())


@dataclass(frozen=True)
class Chunk:
    id: str
    scheme: str
    document: str
    text: str
    url: Optional[str] = None
    page: Optional[int] = None

    @classmethod
    def from_dict(cls, raw: dict) -> "Chunk":
        return cls(
            id=raw["id"],
            scheme=raw["scheme"],
            document=raw["document"],
            text=raw["text"],
            url=raw.get("url"),
            page=raw.get("page"),
        )


@dataclass(frozen=True)
class ScoredChunk:
    chunk: Chunk
    score: float


class Retriever(Protocol):
    def search(self, query: str, top_k: int) -> List[ScoredChunk]: ...


class EmptyRetriever:
    """Stands in until a corpus is ingested.

    Returning nothing is the point: `advisor.py` then produces an honest
    "not covered by my documents" answer with `cited_sources: []` instead of
    letting the model answer from memory.
    """

    def search(self, query: str, top_k: int) -> List[ScoredChunk]:
        return []


class BM25Retriever:
    def __init__(self, chunks: Iterable[Chunk]) -> None:
        from rank_bm25 import BM25Okapi

        self._chunks: List[Chunk] = list(chunks)
        if not self._chunks:
            raise ValueError("BM25Retriever needs at least one chunk")
        self._bm25 = BM25Okapi([tokenize(chunk.text) for chunk in self._chunks])

    def search(self, query: str, top_k: int) -> List[ScoredChunk]:
        tokens = tokenize(query)
        if not tokens:
            return []
        scores = self._bm25.get_scores(tokens)
        ranked: List[Tuple[Chunk, float]] = sorted(
            zip(self._chunks, scores), key=lambda pair: pair[1], reverse=True
        )
        # Drop zero-score chunks: BM25 returns every document, and padding the
        # prompt with irrelevant text is how a grounded answer starts drifting.
        return [ScoredChunk(chunk, float(score)) for chunk, score in ranked[:top_k] if score > 0]


def load_chunks(path: Path) -> List[Chunk]:
    """Read a chunks.jsonl written by `python -m app.ingest`. Missing file -> []."""
    if not path.exists():
        return []
    chunks: List[Chunk] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                chunks.append(Chunk.from_dict(json.loads(line)))
    return chunks


_retriever_lock = threading.Lock()
_retriever_cache: Optional[Tuple[Path, float, Retriever]] = None


def get_retriever(chunks_path: Path) -> Retriever:
    """Build (and cache) a retriever for a chunks file.

    Cached on (path, mtime) so re-running the ingest CLI against a live reload
    server picks up the new corpus without a restart.
    """
    global _retriever_cache

    mtime = chunks_path.stat().st_mtime if chunks_path.exists() else 0.0
    with _retriever_lock:
        if _retriever_cache is not None:
            cached_path, cached_mtime, retriever = _retriever_cache
            if cached_path == chunks_path and cached_mtime == mtime:
                return retriever

        chunks = load_chunks(chunks_path)
        retriever: Retriever = BM25Retriever(chunks) if chunks else EmptyRetriever()
        _retriever_cache = (chunks_path, mtime, retriever)
        return retriever


def reset_retriever_cache() -> None:
    """Test hook — drops the memoized retriever."""
    global _retriever_cache
    with _retriever_lock:
        _retriever_cache = None
