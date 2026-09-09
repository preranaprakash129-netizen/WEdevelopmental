"""Runtime configuration for the advisory-llm service.

Everything is env-driven so the service can run in three states during the
hackathon:

* ``ADVISORY_MODE=mock`` (default) — contract-shaped canned answers. No API key,
  no corpus, no network. This is what the rest of the team codes against.
* ``ADVISORY_MODE=rag`` with an ingested corpus — real BM25 retrieval over the
  scheme PDFs plus a grounded Claude answer.
* ``ADVISORY_MODE=rag`` with no corpus yet — still answers, but honestly says the
  scheme documents don't cover the question and returns ``cited_sources: []``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

SERVICE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CORPUS_DIR = SERVICE_ROOT / "corpus"

MODE_MOCK = "mock"
MODE_RAG = "rag"


@dataclass(frozen=True)
class Settings:
    mode: str
    model: str
    corpus_dir: Path
    top_k: int
    max_history_turns: int
    bhashini_api_key: Optional[str]

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            mode=os.getenv("ADVISORY_MODE", MODE_MOCK).strip().lower(),
            # Opus 5 is the default: this is an advice endpoint where a wrong
            # subsidy percentage is worse than a slow response.
            model=os.getenv("CLAUDE_MODEL", "claude-opus-5"),
            corpus_dir=Path(os.getenv("ADVISORY_CORPUS_DIR", str(DEFAULT_CORPUS_DIR))),
            top_k=int(os.getenv("ADVISORY_TOP_K", "6")),
            max_history_turns=int(os.getenv("ADVISORY_MAX_HISTORY_TURNS", "8")),
            bhashini_api_key=os.getenv("BHASHINI_API_KEY") or None,
        )

    @property
    def chunks_path(self) -> Path:
        return self.corpus_dir / "chunks.jsonl"

    @property
    def manifest_path(self) -> Path:
        return self.corpus_dir / "manifest.json"

    @property
    def pdf_dir(self) -> Path:
        return self.corpus_dir / "pdfs"


def get_settings() -> Settings:
    """Read settings fresh on every call so tests can monkeypatch the environment."""
    return Settings.from_env()
