"""Contract-shaped mock responses for POST /feasibility.

Numbers here are placeholders (seeded per location+category so responses are stable
across calls, not random noise) so other services can integrate against the real
shape today. The actual scoring/SWOT/pricing methodology is TODO.
"""

import random
import uuid

from .schemas import (
    Competitor,
    ConfidenceRange,
    FeasibilityResponse,
    MarketReach,
    PricingBands,
    SWOT,
)
from .seed_loader import load_location


def build_feasibility_response(location: str, category: str, margin_capital: float) -> FeasibilityResponse:
    rng = random.Random(f"{location.lower()}|{category.lower()}")
    seed = load_location(location) or {}

    matching_businesses = [
        b for b in seed.get("existing_businesses", []) if b.get("category") == category
    ]
    price_band = next(
        (p for p in seed.get("price_bands", []) if p.get("category") == category), None
    )

    competitor_list = [
        Competitor(name=b["name"], category=b["category"], distance_km=b["distance_from_center_km"])
        for b in matching_businesses
    ] or [
        Competitor(name=f"{category.title()} Corner", category=category, distance_km=round(rng.uniform(0.5, 4.0), 1))
    ]

    if price_band:
        pricing_bands = PricingBands(low=price_band["low"], median=price_band["median"], high=price_band["high"])
    else:
        base = round(rng.uniform(30, 200))
        pricing_bands = PricingBands(low=base, median=round(base * 1.3), high=round(base * 1.7))

    feasibility_score = round(rng.uniform(45, 85), 1)
    spread = round(rng.uniform(5, 12), 1)

    return FeasibilityResponse(
        request_id=str(uuid.uuid4()),
        market_reach=MarketReach(
            estimated_customers=int(rng.uniform(400, 2000)),
            radius_km=round(rng.uniform(1.5, 5.0), 1),
        ),
        competitor_list=competitor_list,
        swot=SWOT(
            strengths=["Low local competition density", f"Steady demand for {category} in this area"],
            weaknesses=[
                "High upfront setup cost relative to margin capital"
                if margin_capital < 50000
                else "Requires ongoing working capital"
            ],
            opportunities=["Government subsidy schemes available for this category"],
            threats=["Seasonal demand fluctuation"],
        ),
        pricing_bands=pricing_bands,
        feasibility_score=feasibility_score,
        confidence_range=ConfidenceRange(
            low=max(0.0, feasibility_score - spread),
            high=min(100.0, feasibility_score + spread),
        ),
    )
