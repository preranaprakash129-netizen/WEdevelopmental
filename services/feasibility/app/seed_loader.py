"""Loads location data per docs/seed-data-spec.md.

Reads data/seed/<slug>.json — see that directory for the locations currently seeded.
"""

import json
import re
from pathlib import Path
from typing import Optional

SEED_DIR = Path(__file__).resolve().parents[3] / "data" / "seed"


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.strip().lower())


def load_location(name: str) -> Optional[dict]:
    """Returns the location object for `name`, or None if no seed file exists for it."""
    slug = _slugify(name)
    seed_file = SEED_DIR / f"{slug}.json"
    if not seed_file.exists():
        return None
    with seed_file.open(encoding="utf-8") as f:
        return json.load(f)
