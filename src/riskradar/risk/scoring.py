"""Time-decayed vendor risk scoring: category scores, composite, trend."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from riskradar.settings import get_config

CATEGORIES = ["security", "financial", "delivery", "compliance", "concentration"]


def decay_weight(age_days: float, half_life: float) -> float:
    return math.pow(0.5, age_days / half_life)


def category_score(events: pd.DataFrame, as_of_day: int, half_life: float, kappa: float) -> float:
    """Saturating map of decayed severity mass -> 0..100."""
    past = events[events["day"] <= as_of_day]
    if past.empty:
        return 0.0
    mass = sum(
        row.severity * decay_weight(as_of_day - row.day, half_life) for row in past.itertuples()
    )
    return round(100 * (1 - math.exp(-mass / kappa)), 1)


def score_vendor(events: pd.DataFrame, as_of_day: int) -> dict:
    cfg = get_config()["scoring"]
    categories = {}
    for category in CATEGORIES:
        cat_events = events[events["category"] == category]
        categories[category] = category_score(
            cat_events, as_of_day, cfg["decay_half_life_days"], cfg["saturation_kappa"]
        )
    composite = round(sum(cfg["category_weights"][c] * categories[c] for c in CATEGORIES), 1)
    return {"composite": composite, "categories": categories}


def score_all(vendors: pd.DataFrame, events: pd.DataFrame, as_of_day: int) -> pd.DataFrame:
    cfg = get_config()["scoring"]
    rows = []
    for vendor_id in vendors["vendor_id"]:
        vendor_events = events[events["vendor_id"] == vendor_id]
        now = score_vendor(vendor_events, as_of_day)
        past = score_vendor(vendor_events, as_of_day - 30)
        trend = round(now["composite"] - past["composite"], 1)
        rows.append(
            {
                "vendor_id": vendor_id,
                "score": now["composite"],
                "trend_30d": trend,
                **{f"cat_{c}": v for c, v in now["categories"].items()},
                "watchlist": bool(
                    now["composite"] >= cfg["watch_score"] or trend >= cfg["watch_trend"]
                ),
            }
        )
    return pd.DataFrame(rows)


def score_history(events: pd.DataFrame, as_of_day: int, points: int = 12) -> list[dict]:
    days = np.linspace(max(30, as_of_day - 330), as_of_day, points, dtype=int)
    return [{"day": int(d), "score": score_vendor(events, int(d))["composite"]} for d in days]
