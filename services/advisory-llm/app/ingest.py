"""Chunk the scheme PDFs listed in corpus/manifest.json into corpus/chunks.jsonl.

    python -m app.ingest                 # everything in the manifest
    python -m app.ingest --scheme PMEGP  # just one scheme

Drop the PDFs into `corpus/pdfs/` under the `source_pdf` filename the manifest
gives them, then run this. Both the PDFs and the generated chunks are
gitignored — the manifest is what we version, so anyone on the team can rebuild
an identical corpus from the official sources.

Chunks carry their page number so a citation can be traced back to a page of the
original circular, which is the difference between "the model said so" and
something a judge can check.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterator, List, Optional

from .config import get_settings
from .manifest import ManifestEntry, load_manifest

DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 150

# Below this a "chunk" is almost always a running header, a page number or a
# stray table fragment — noise that BM25 will happily match on.
MIN_CHUNK_CHARS = 80

_WHITESPACE_RE = re.compile(r"\s+")
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest scheme PDFs into chunks.jsonl")
    parser.add_argument("--scheme", help="Only ingest this scheme (e.g. PMEGP)")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    args = parser.parse_args(argv)

    settings = get_settings()
    entries = load_manifest(settings.manifest_path)
    if not entries:
        print(f"No documents listed in {settings.manifest_path}", file=sys.stderr)
        return 1

    if args.scheme:
        entries = [e for e in entries if e.scheme.lower() == args.scheme.lower()]
        if not entries:
            print(f"No manifest entry for scheme {args.scheme!r}", file=sys.stderr)
            return 1

    records: List[dict] = []
    missing: List[str] = []

    for entry in entries:
        pdf_path = settings.pdf_dir / entry.source_pdf
        if not pdf_path.exists():
            missing.append(f"{entry.scheme}: {pdf_path}")
            continue
        entry_records = list(
            _chunk_pdf(entry, pdf_path, args.chunk_size, args.chunk_overlap)
        )
        records.extend(entry_records)
        print(f"{entry.scheme}: {len(entry_records)} chunks from {pdf_path.name}")

    for line in missing:
        print(f"MISSING PDF — skipped {line}", file=sys.stderr)

    if not records:
        print("Nothing ingested.", file=sys.stderr)
        return 1

    settings.chunks_path.parent.mkdir(parents=True, exist_ok=True)
    with settings.chunks_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} chunks to {settings.chunks_path}")
    return 0


def _chunk_pdf(
    entry: ManifestEntry, pdf_path: Path, chunk_size: int, chunk_overlap: int
) -> Iterator[dict]:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from pypdf import PdfReader

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        # Paragraph first, then sentence: scheme guidelines are clause-heavy and
        # splitting mid-clause is how an eligibility rule loses its condition.
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    slug = _slug(entry.scheme)
    reader = PdfReader(str(pdf_path))

    for page_number, page in enumerate(reader.pages, start=1):
        text = _normalize(page.extract_text() or "")
        if len(text) < MIN_CHUNK_CHARS:
            continue
        for index, piece in enumerate(splitter.split_text(text)):
            piece = piece.strip()
            if len(piece) < MIN_CHUNK_CHARS:
                continue
            yield {
                "id": f"{slug}-p{page_number:04d}-{index:02d}",
                "scheme": entry.scheme,
                "document": entry.document,
                "url": entry.url,
                "page": page_number,
                "text": piece,
            }


def _normalize(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def _slug(value: str) -> str:
    return _SLUG_RE.sub("-", value.lower()).strip("-")


if __name__ == "__main__":
    raise SystemExit(main())
