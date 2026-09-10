"""Runtime configuration for the advisory-llm service.

Everything is env-driven so the service can run in four states:

* ``ADVISORY_MODE=local_ml`` (default) — fully local: a trained TF-IDF/SVM
  scheme+intent classifier routes the question, then a deterministic template
  answers from services/advisory-llm/app/scheme_facts.py's structured data.
  No external API call, no network dependency, no hallucination risk (nothing
  generates text -- every number is looked up). Needs the classifier trained
  once via `python train/train_local_advisor.py`.
* ``ADVISORY_MODE=rag`` with an ingested corpus — BM25 retrieval over the
  scheme PDFs/chunks plus a grounded Claude answer. Needs ANTHROPIC_API_KEY.
* ``ADVISORY_MODE=rag`` with no corpus yet — still answers, but honestly says
  the scheme documents don't cover the question and returns ``cited_sources: []``.
* ``ADVISORY_MODE=mock`` — contract-shaped canned answers. No API key, no
  corpus, no network, no trained model. What the rest of the team codes against
  before any of the above is ready.
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
MODE_LOCAL_ML = "local_ml"


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
            mode=os.getenv("ADVISORY_MODE", MODE_LOCAL_ML).strip().lower(),
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
