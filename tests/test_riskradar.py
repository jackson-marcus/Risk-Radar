"""Decay math, ranking recovery, watchlist detection, gap rules, RAG, API."""

from __future__ import annotations

import pandas as pd

from riskradar.rag.guide import ask
from riskradar.risk.gaps import diligence_gaps
from riskradar.risk.scoring import category_score, decay_weight


def test_decay_recent_events_dominate():
    assert decay_weight(0, 90) == 1.0
    assert abs(decay_weight(90, 90) - 0.5) < 1e-9

    recent = pd.DataFrame({"day": [360], "severity": [3]})
    old = pd.DataFrame({"day": [30], "severity": [3]})
    assert category_score(recent, 365, 90, 6.0) > category_score(old, 365, 90, 6.0)


def test_scoring_recovers_latent_ranking(evaluated):
    m = evaluated["metrics"]
    # Poisson event counts + decay make the current score a NOISY snapshot of
    # latent riskiness — strong rank recovery, but never near-perfect
    assert 0.55 <= m["rank_spearman"] <= 0.95
    assert 0 < m["mean_score"] < 90  # scores neither saturated nor empty


def test_watchlist_catches_deteriorating_vendors(evaluated):
    m = evaluated["metrics"]
    assert m["watch_recall"] >= 0.6
    assert m["watchlist_size"] <= 20  # not just flagging everyone


def test_diligence_gap_rules():
    events = pd.DataFrame({"category": ["security"] * 4, "day": [1, 2, 3, 4]})
    risky = {
        "handles_pii": True,
        "has_soc2": False,
        "single_source": True,
        "annual_spend_usd": 900_000,
        "years_active": 1.0,
    }
    gaps = diligence_gaps(risky, events)
    rule_ids = {g["rule_id"] for g in gaps}
    assert {
        "security-soc2",
        "pii-dpa",
        "concentration-limit",
        "exit-plan",
        "incident-notification",
        "financial-review",
    } <= rule_ids

    clean = {
        "handles_pii": False,
        "has_soc2": True,
        "single_source": False,
        "annual_spend_usd": 50_000,
        "years_active": 8.0,
    }
    assert diligence_gaps(clean, pd.DataFrame({"category": [], "day": []})) == []


def test_rag_cites_and_rejects_junk():
    hit = ask("When do we need a second source for a vendor?")
    assert hit["matched"]
    assert any(r["rule_id"] in {"concentration-limit", "exit-plan"} for r in hit["rules"])

    junk = ask("quantum espresso zebra parade")
    assert not junk["matched"]


def test_api_contract(api_client):
    assert api_client.get("/health").json() == {"status": "ok"}

    board = api_client.get("/vendors").json()
    assert len(board["vendors"]) == 40
    scores = [v["score"] for v in board["vendors"]]
    assert scores == sorted(scores, reverse=True)

    vid = board["vendors"][0]["vendor_id"]
    detail = api_client.get(f"/vendor/{vid}").json()
    assert len(detail["history"]) == 12
    assert api_client.get("/vendor/999").status_code == 404

    watch = api_client.get("/watchlist").json()
    assert isinstance(watch, list)

    answer = api_client.post("/diligence/ask", json={"question": "cyber insurance minimum"}).json()
    assert answer["matched"] and answer["rules"][0]["rule_id"] == "insurance"
