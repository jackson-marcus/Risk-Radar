"""API routes: /vendors, /vendor/{id}, /watchlist, /diligence/ask, /health."""

from __future__ import annotations

import functools
import logging
import pickle

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from riskradar.rag.guide import ask, rule_body
from riskradar.risk.gaps import diligence_gaps
from riskradar.risk.scoring import score_history
from riskradar.settings import get_config, resolve_path

logger = logging.getLogger(__name__)
router = APIRouter()


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@functools.lru_cache(maxsize=1)
def _artifacts():
    cfg = get_config()["data"]
    art = resolve_path(cfg["artifacts_dir"])
    if not (art / "scored.parquet").exists():
        raise FileNotFoundError(
            "Artifacts missing; run make_vendors.py + riskradar.models.evaluate"
        )
    scored = pd.read_parquet(art / "scored.parquet")
    events = pd.read_parquet(resolve_path(cfg["processed_dir"]) / "events.parquet")
    with open(art / "metrics.pkl", "rb") as f:
        metrics = pickle.load(f)
    return scored, events, metrics


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/vendors")
def vendors() -> dict:
    try:
        scored, _, metrics = _artifacts()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    cols = [
        "vendor_id",
        "name",
        "sector",
        "score",
        "trend_30d",
        "watchlist",
        "cat_security",
        "cat_financial",
        "cat_delivery",
        "cat_compliance",
        "cat_concentration",
    ]
    return {
        "metrics": metrics,
        "vendors": scored[cols].sort_values("score", ascending=False).to_dict(orient="records"),
    }


@router.get("/vendor/{vendor_id}")
def vendor_detail(vendor_id: int) -> dict:
    try:
        scored, events, _ = _artifacts()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    match = scored[scored["vendor_id"] == vendor_id]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"unknown vendor {vendor_id}")
    row = match.iloc[0].to_dict()
    vendor_events = events[events["vendor_id"] == vendor_id]
    as_of = get_config()["data"]["history_days"]
    gaps = [
        {**gap, "policy": rule_body(gap["rule_id"])[:220]}
        for gap in diligence_gaps(row, vendor_events)
    ]
    recent = (
        vendor_events.sort_values("day", ascending=False)
        .head(8)[["day", "category", "event", "severity"]]
        .to_dict(orient="records")
    )
    clean = {k: (v.item() if hasattr(v, "item") else v) for k, v in row.items()}
    return {
        "vendor": clean,
        "history": score_history(vendor_events, as_of),
        "recent_events": recent,
        "diligence_gaps": gaps,
    }


@router.get("/watchlist")
def watchlist() -> list[dict]:
    try:
        scored, _, _ = _artifacts()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    flagged = scored[scored["watchlist"]].sort_values("trend_30d", ascending=False)
    return flagged[["vendor_id", "name", "score", "trend_30d"]].to_dict(orient="records")


@router.post("/diligence/ask")
def diligence_ask(request: AskRequest) -> dict:
    return ask(request.question)
