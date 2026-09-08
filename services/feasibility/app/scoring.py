"""Real feasibility scoring for POST /feasibility.

feasibility_score blends four signals, weighted by how directly each bears on
whether *this* business, at *this* location, is viable:
  - competitor density/proximity (30%)
  - margin_capital vs. a category's typical setup cost (30%)
  - market size, from location population/density (25%)
  - local pricing spread (15%)

confidence_range narrows as more of those signals come from real seed data
(vs. defaults for an unmatched location/category) rather than a fixed band.

Category typical-setup-cost and location-type catchment-radius figures below are
hackathon-demo assumptions, not sourced financial data — tune freely.
"""

import math
import random
import uuid
from typing import Optional

from .schemas import (
    Competitor,
    ConfidenceRange,
    FeasibilityResponse,
    MarketReach,
    PricingBands,
    SWOT,
)
from .seed_loader import load_location

CATEGORY_TYPICAL_SETUP_COST = {
    "dairy": 150000,
    "tailoring": 40000,
    "handicrafts": 60000,
    "food-processing": 120000,
    "retail-kirana": 100000,
    "poultry": 90000,
}
DEFAULT_TYPICAL_SETUP_COST = 80000
OWNER_CONTRIBUTION_TARGET_RATIO = 0.20  # margin_capital expected to cover ~20% of setup cost

TYPE_RADIUS_KM = {"rural": 5.0, "semi-urban": 3.0, "urban": 1.5}
DEFAULT_RADIUS_KM = 3.0
CUSTOMER_REACH_FRACTION = 0.08

DEFAULT_PRICE_BAND = {"low": 50, "median": 80, "high": 120}

CONFIDENCE_SPREAD_MAX = 15.0  # completeness = 0 (nothing matched)
CONFIDENCE_SPREAD_MIN = 4.0  # completeness = 1 (location + category price data both matched)


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _competitor_score(count: int, avg_distance_km: Optional[float]) -> float:
    if count == 0:
        return 85.0
    density_penalty = min(60.0, count * 12.0)
    proximity_penalty = 0.0 if avg_distance_km is None else max(0.0, (2.5 - avg_distance_km) * 12.0)
    return _clamp(100.0 - density_penalty - proximity_penalty)


def _capital_score(margin_capital: float, typical_cost: float) -> float:
    target = typical_cost * OWNER_CONTRIBUTION_TARGET_RATIO
    if target <= 0:
        return 50.0
    return _clamp((margin_capital / target) * 100.0)


def _market_score(seed: Optional[dict]) -> float:
    if not seed:
        return 50.0
    population = seed.get("population", 0)
    density = seed.get("population_density_per_sqkm", 0)
    pop_component = _clamp((population - 2000) / (50000 - 2000) * 100.0)
    density_component = _clamp((density - 100) / (1000 - 100) * 100.0)
    return 0.7 * pop_component + 0.3 * density_component


def _pricing_score(price_band: Optional[dict]) -> float:
    if not price_band or not price_band.get("median"):
        return 50.0
    spread_ratio = (price_band["high"] - price_band["low"]) / price_band["median"]
    return _clamp(spread_ratio * 150.0)


def _market_reach(seed: Optional[dict], location: str) -> MarketReach:
    if seed:
        radius_km = TYPE_RADIUS_KM.get(seed.get("type", ""), DEFAULT_RADIUS_KM)
        population = seed.get("population", 0)
        density = seed.get("population_density_per_sqkm", 0)
        local_pop_estimate = min(population, density * math.pi * radius_km**2)
        estimated_customers = max(50, round(local_pop_estimate * CUSTOMER_REACH_FRACTION))
    else:
        rng = random.Random(f"reach|{location.lower()}")
        radius_km = DEFAULT_RADIUS_KM
        estimated_customers = int(rng.uniform(300, 1200))
    return MarketReach(estimated_customers=estimated_customers, radius_km=radius_km)


def _competitor_bullet(count: int, avg_distance_km: Optional[float], category: str) -> str:
    if count == 0:
        return f"No {category} competitors identified in the surveyed area"
    if avg_distance_km is not None:
        return f"{count} {category} competitor(s) identified, averaging {avg_distance_km:.1f}km away"
    return f"{count} {category} competitor(s) identified nearby"


def _capital_bullet(margin_capital: float, typical_cost: float, category: str) -> str:
    pct = (margin_capital / typical_cost * 100.0) if typical_cost else 0.0
    return (
        f"Margin capital of Rs.{margin_capital:,.0f} covers {pct:.0f}% of the typical "
        f"Rs.{typical_cost:,.0f} setup cost for {category}"
    )


def _market_bullet(seed: dict) -> str:
    return (
        f"{seed.get('type', 'semi-urban').capitalize()} location with population "
        f"{seed.get('population', 0):,} (density {seed.get('population_density_per_sqkm', 0):.0f}/sq km)"
    )


def _pricing_bullet(price_band: dict, category: str) -> str:
    return (
        f"Local {category} pricing ranges Rs.{price_band['low']}-Rs.{price_band['high']} "
        f"(median Rs.{price_band['median']}), leaving room to position pricing"
    )


def _build_swot(
    category: str,
    margin_capital: float,
    typical_cost: float,
    seed: Optional[dict],
    matched_price_band: Optional[dict],
    competitor_score: float,
    capital_score: float,
    market_score: float,
    pricing_score: float,
    competitor_count: int,
    avg_distance_km: Optional[float],
) -> SWOT:
    strengths, weaknesses = [], []
    opportunities = ["Government subsidy schemes may be available for this category — check via the calculator service"]
    threats = ["Demand can fluctuate seasonally for this category"]

    (strengths if competitor_score >= 55 else weaknesses).append(
        _competitor_bullet(competitor_count, avg_distance_km, category)
    )
    (strengths if capital_score >= 55 else weaknesses).append(
        _capital_bullet(margin_capital, typical_cost, category)
    )

    if seed:
        (strengths if market_score >= 55 else weaknesses).append(_market_bullet(seed))
    else:
        weaknesses.append(
            f"'{category}' location not found in seed data — market size and competitor figures are estimated, not verified"
        )

    if matched_price_band:
        (opportunities if pricing_score >= 55 else weaknesses).append(
            _pricing_bullet(matched_price_band, category)
        )
    else:
        threats.append(
            f"No local pricing data available for {category} — pricing_bands shown are a generic default, not location-specific"
        )

    return SWOT(strengths=strengths, weaknesses=weaknesses, opportunities=opportunities, threats=threats)


def build_feasibility_response(location: str, category: str, margin_capital: float) -> FeasibilityResponse:
    category_key = category.lower()
    seed = load_location(location)

    matching_businesses = [
        b for b in (seed or {}).get("existing_businesses", []) if b.get("category", "").lower() == category_key
    ]
    matched_price_band = next(
        (p for p in (seed or {}).get("price_bands", []) if p.get("category", "").lower() == category_key),
        None,
    )
    price_band = matched_price_band or DEFAULT_PRICE_BAND

    avg_distance_km = (
        sum(b["distance_from_center_km"] for b in matching_businesses) / len(matching_businesses)
        if matching_businesses
        else None
    )

    typical_cost = CATEGORY_TYPICAL_SETUP_COST.get(category_key, DEFAULT_TYPICAL_SETUP_COST)

    competitor_score = _competitor_score(len(matching_businesses), avg_distance_km)
    capital_score = _capital_score(margin_capital, typical_cost)
    market_score = _market_score(seed)
    pricing_score = _pricing_score(matched_price_band)

    feasibility_score = round(
        _clamp(
            competitor_score * 0.30 + capital_score * 0.30 + market_score * 0.25 + pricing_score * 0.15
        ),
        1,
    )

    completeness = (bool(seed) + bool(matched_price_band)) / 2
    spread = CONFIDENCE_SPREAD_MAX - completeness * (CONFIDENCE_SPREAD_MAX - CONFIDENCE_SPREAD_MIN)

    return FeasibilityResponse(
        request_id=str(uuid.uuid4()),
        market_reach=_market_reach(seed, location),
        competitor_list=[
            Competitor(name=b["name"], category=b["category"], distance_km=b["distance_from_center_km"])
            for b in matching_businesses
        ],
        swot=_build_swot(
            category=category,
            margin_capital=margin_capital,
            typical_cost=typical_cost,
            seed=seed,
            matched_price_band=matched_price_band,
            competitor_score=competitor_score,
            capital_score=capital_score,
            market_score=market_score,
            pricing_score=pricing_score,
            competitor_count=len(matching_businesses),
            avg_distance_km=avg_distance_km,
        ),
        pricing_bands=PricingBands(low=price_band["low"], median=price_band["median"], high=price_band["high"]),
        feasibility_score=feasibility_score,
        confidence_range=ConfidenceRange(
            low=round(_clamp(feasibility_score - spread), 1),
            high=round(_clamp(feasibility_score + spread), 1),
        ),
    )
