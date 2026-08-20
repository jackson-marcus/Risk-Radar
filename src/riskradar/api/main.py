"""FastAPI application factory."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from riskradar import __version__
from riskradar.api.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app() -> FastAPI:
    app = FastAPI(
        title="riskradar",
        description="Vendor risk management: time-decayed multi-category risk scoring, deterioration watchlist with trend detection, rule-based diligence gap analysis, and a cited due-diligence policy assistant.",
        version=__version__,
    )
    app.include_router(router)
    return app


app = create_app()
