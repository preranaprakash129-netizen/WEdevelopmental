"""The corpus manifest: which scheme documents we ingest and how we cite them.

`corpus/manifest.json` is the single source of truth for the `scheme`,
`document` and `url` values that end up in `cited_sources`. The ingest CLI reads
it, and mock mode reads it too, so a citation looks identical whether the answer
came from the real corpus or from a canned demo response.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class ManifestEntry:
    scheme: str
    document: str
    url: Optional[str]
    source_pdf: str

    @classmethod
    def from_dict(cls, raw: dict) -> "ManifestEntry":
        return cls(
            scheme=raw["scheme"],
            document=raw["document"],
            url=raw.get("url"),
            source_pdf=raw["source_pdf"],
        )


def load_manifest(path: Path) -> List[ManifestEntry]:
    """Read the manifest. A missing file is not an error — it just means no corpus."""
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [ManifestEntry.from_dict(entry) for entry in raw.get("documents", [])]


def find_by_scheme(entries: List[ManifestEntry], scheme: str) -> Optional[ManifestEntry]:
    for entry in entries:
        if entry.scheme.lower() == scheme.lower():
            return entry
    return None
