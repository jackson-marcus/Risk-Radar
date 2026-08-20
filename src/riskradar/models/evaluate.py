"""Score all vendors and evaluate against planted truth; log to MLflow.

Usage:
    python -m riskradar.models.evaluate
"""

from __future__ import annotations

import logging
import pickle

import mlflow
import pandas as pd
from scipy.stats import spearmanr

from riskradar.risk.scoring import score_all
from riskradar.settings import get_config, get_settings, resolve_path

logger = logging.getLogger(__name__)


def evaluate() -> dict:
    cfg = get_config()
    processed = resolve_path(cfg["data"]["processed_dir"])
    vendors = pd.read_parquet(processed / "vendors.parquet")
    events = pd.read_parquet(processed / "events.parquet")
    as_of = cfg["data"]["history_days"]

    scored = score_all(vendors, events, as_of).merge(vendors, on="vendor_id")

    rank_corr = float(spearmanr(scored["score"], scored["true_riskiness"]).statistic)

    flagged = scored[scored["watchlist"]]
    deteriorating = scored[scored["is_deteriorating"]]
    caught = int(flagged["is_deteriorating"].sum())
    metrics = {
        "rank_spearman": round(rank_corr, 4),
        "watchlist_size": len(flagged),
        "deteriorating_planted": len(deteriorating),
        "deteriorating_caught": caught,
        "watch_recall": round(caught / max(len(deteriorating), 1), 4),
        "watch_precision": round(caught / max(len(flagged), 1), 4),
        "mean_score": round(float(scored["score"].mean()), 1),
    }

    mlflow.set_tracking_uri(get_settings().mlflow_tracking_uri)
    mlflow.set_experiment(cfg["eval"]["experiment_name"])
    with mlflow.start_run(run_name="vendor-risk"):
        mlflow.log_params({"n_vendors": len(vendors), "as_of_day": as_of})
        mlflow.log_metrics(metrics)
    logger.info("vendor-risk %s", metrics)

    artifacts = resolve_path(cfg["data"]["artifacts_dir"])
    artifacts.mkdir(parents=True, exist_ok=True)
    scored.to_parquet(artifacts / "scored.parquet", index=False)
    with open(artifacts / "metrics.pkl", "wb") as f:
        pickle.dump(metrics, f)
    return metrics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    evaluate()
