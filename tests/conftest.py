"""Offline fixtures: generated vendors scored into tmp artifacts."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from make_vendors import generate  # noqa: E402

from riskradar.settings import get_config, get_settings  # noqa: E402


@pytest.fixture(scope="session")
def vendor_data():
    return generate(n_vendors=40, days=365, n_deteriorating=5, seed=7)


@pytest.fixture(scope="session")
def evaluated(tmp_path_factory, vendor_data):
    vendors, events = vendor_data
    tmp = tmp_path_factory.mktemp("riskradar")
    (tmp / "processed").mkdir()
    vendors.to_parquet(tmp / "processed" / "vendors.parquet", index=False)
    events.to_parquet(tmp / "processed" / "events.parquet", index=False)

    cfg = get_config()
    originals = (cfg["data"]["processed_dir"], cfg["data"]["artifacts_dir"])
    cfg["data"]["processed_dir"] = str(tmp / "processed")
    cfg["data"]["artifacts_dir"] = str(tmp / "artifacts")

    old_uri = os.environ.get("MLFLOW_TRACKING_URI")
    os.environ["MLFLOW_TRACKING_URI"] = f"sqlite:///{tmp / 'mlflow.db'}"
    get_settings.cache_clear()

    from riskradar.models.evaluate import evaluate

    metrics = evaluate()
    yield {"metrics": metrics, "artifacts": tmp / "artifacts"}

    cfg["data"]["processed_dir"], cfg["data"]["artifacts_dir"] = originals
    if old_uri is None:
        os.environ.pop("MLFLOW_TRACKING_URI", None)
    else:
        os.environ["MLFLOW_TRACKING_URI"] = old_uri
    get_settings.cache_clear()


@pytest.fixture
def api_client(evaluated):
    from fastapi.testclient import TestClient

    from riskradar.api import routes
    from riskradar.api.main import app

    routes._artifacts.cache_clear()
    try:
        yield TestClient(app)
    finally:
        routes._artifacts.cache_clear()
