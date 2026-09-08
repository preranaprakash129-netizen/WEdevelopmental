"""Loads location data per docs/seed-data-spec.md.

Real files land in data/seed/<slug>.json as the team produces them. Until then,
falls back to a couple of local fixtures so this service is usable end-to-end today.
"""

import json
import re
from pathlib import Path
from typing import Optional

SEED_DIR = Path(__file__).resolve().parents[3] / "data" / "seed"

FIXTURE_LOCATIONS = {
    "rampur": {
        "location_name": "Rampur",
        "state": "Uttar Pradesh",
        "population": 8400,
        "population_density_per_sqkm": 320,
        "type": "rural",
        "existing_businesses": [
            {
                "name": "Shree Dairy",
                "category": "dairy",
                "distance_from_center_km": 1.2,
                "years_operating": 5,
                "estimated_monthly_revenue": 45000,
            },
            {
                "name": "Gopal Milk Center",
                "category": "dairy",
                "distance_from_center_km": 2.8,
                "years_operating": 3,
                "estimated_monthly_revenue": 30000,
            },
            {
                "name": "Rampur Tailors",
                "category": "tailoring",
                "distance_from_center_km": 0.9,
                "years_operating": 8,
                "estimated_monthly_revenue": 22000,
            },
        ],
        "price_bands": [
            {"category": "dairy", "unit": "per litre", "low": 40, "median": 55, "high": 70},
            {"category": "tailoring", "unit": "per garment", "low": 150, "median": 300, "high": 600},
        ],
    },
    "sundarpur": {
        "location_name": "Sundarpur",
        "state": "Tamil Nadu",
        "population": 15600,
        "population_density_per_sqkm": 540,
        "type": "semi-urban",
        "existing_businesses": [
            {
                "name": "Amma's Pickles & Foods",
                "category": "food-processing",
                "distance_from_center_km": 1.5,
                "years_operating": 4,
                "estimated_monthly_revenue": 60000,
            },
            {
                "name": "Sundarpur Kirana Store",
                "category": "retail-kirana",
                "distance_from_center_km": 0.5,
                "years_operating": 10,
                "estimated_monthly_revenue": 90000,
            },
        ],
        "price_bands": [
            {"category": "food-processing", "unit": "per kg", "low": 120, "median": 180, "high": 260},
            {"category": "retail-kirana", "unit": "per basket", "low": 200, "median": 350, "high": 550},
        ],
    },
}


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.strip().lower())


def load_location(name: str) -> Optional[dict]:
    """Returns the location object for `name`, or None if unknown anywhere."""
    slug = _slugify(name)
    seed_file = SEED_DIR / f"{slug}.json"
    if seed_file.exists():
        with seed_file.open(encoding="utf-8") as f:
            return json.load(f)
    return FIXTURE_LOCATIONS.get(slug)
