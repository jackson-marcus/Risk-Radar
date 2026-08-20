"""Vendor catalog + event history driven by latent riskiness, with a
deteriorating cohort in the final 60 days (the watchlist must catch them).

Usage:
    uv run python scripts/make_vendors.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from riskradar.settings import get_config, resolve_path

CATEGORIES = ["security", "financial", "delivery", "compliance", "concentration"]
EVENT_TYPES = {
    "security": ["credential leak reported", "phishing incident", "unpatched CVE exposure"],
    "financial": ["late filing", "credit downgrade", "layoffs announced"],
    "delivery": ["SLA breach", "missed delivery window", "quality escape"],
    "compliance": ["audit finding", "expired certification", "policy violation"],
    "concentration": ["price increase notice", "capacity constraint", "regional outage"],
}
SECTORS = ["cloud", "logistics", "manufacturing", "payments", "staffing", "analytics"]


def generate(n_vendors: int, days: int, n_deteriorating: int, seed: int = 42):
    rng = np.random.default_rng(seed)
    riskiness = rng.beta(2, 5, n_vendors)
    deteriorating = rng.choice(n_vendors, size=n_deteriorating, replace=False)

    vendors, events = [], []
    for i in range(n_vendors):
        u = float(riskiness[i])
        vendor_id = i + 1
        vendors.append(
            {
                "vendor_id": vendor_id,
                "name": f"{rng.choice(['Nova', 'Apex', 'Blue', 'Iron', 'Quick', 'Prime'])}"
                f"{rng.choice(['soft', 'chain', 'works', 'core', 'link', 'grid'])}-{vendor_id:02d}",
                "sector": str(rng.choice(SECTORS)),
                "annual_spend_usd": int(rng.lognormal(12, 1.0)),
                "years_active": round(float(rng.uniform(0.5, 15)), 1),
                "has_soc2": bool(rng.random() > u * 0.9),
                "handles_pii": bool(rng.random() < 0.5),
                "single_source": bool(rng.random() < 0.3),
                "true_riskiness": round(u, 4),
                "is_deteriorating": bool(i in deteriorating),
            }
        )
        for category in CATEGORIES:
            tilt = rng.uniform(0.5, 1.5)
            base_rate = u * tilt * days / 35
            n_events = rng.poisson(base_rate)
            event_days = rng.integers(0, days, n_events)
            if i in deteriorating:
                extra = rng.poisson(u * 6 + 2)
                event_days = np.concatenate([event_days, rng.integers(days - 60, days, extra)])
            for day in event_days:
                events.append(
                    {
                        "vendor_id": vendor_id,
                        "day": int(day),
                        "category": category,
                        "event": str(rng.choice(EVENT_TYPES[category])),
                        "severity": int(np.clip(rng.poisson(1 + 2.5 * u) + 1, 1, 5)),
                    }
                )

    return pd.DataFrame(vendors), pd.DataFrame(events)


def main() -> None:
    cfg = get_config()["data"]
    vendors, events = generate(
        cfg["n_vendors"], cfg["history_days"], cfg["n_deteriorating"], cfg["seed"]
    )
    out = resolve_path(cfg["processed_dir"])
    out.mkdir(parents=True, exist_ok=True)
    vendors.to_parquet(out / "vendors.parquet", index=False)
    events.to_parquet(out / "events.parquet", index=False)
    print(json.dumps({"vendors": len(vendors), "events": len(events)}))


if __name__ == "__main__":
    main()
