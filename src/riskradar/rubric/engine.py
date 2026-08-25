"""Config-as-Code Scoring Rubric - Evaluation Engine.

Executes generic weighted risk scoring against declarative ScoringRubric definitions.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from riskradar.rubric.models import (
    CategorySpec,
    DecayType,
    ScoringRubric,
    VendorRiskEvaluation,
)


class RubricScoringEngine:
    """Config-driven risk scoring engine."""

    @classmethod
    def compute_decay(
        cls,
        age_days: float,
        half_life: float,
        decay_type: DecayType = DecayType.EXPONENTIAL_HALF_LIFE,
    ) -> float:
        if age_days < 0:
            return 1.0
        if decay_type == DecayType.EXPONENTIAL_HALF_LIFE:
            return math.pow(0.5, age_days / max(half_life, 1e-4))
        elif decay_type == DecayType.LINEAR:
            return max(0.0, 1.0 - (age_days / (2.0 * half_life)))
        elif decay_type == DecayType.STEP:
            return 1.0 if age_days <= half_life else 0.2
        return math.pow(0.5, age_days / max(half_life, 1e-4))

    @classmethod
    def compute_category_score(
        cls,
        cat_spec: CategorySpec,
        events: list[dict[str, Any]],
        as_of_day: int,
    ) -> float:
        """Computes saturating 0..100 risk score for a single category."""
        past_events = [e for e in events if e.get("day", 0) <= as_of_day]
        if not past_events:
            return 0.0

        decayed_mass = sum(
            float(e.get("severity", 1.0))
            * cls.compute_decay(
                as_of_day - e["day"], cat_spec.decay_half_life_days, cat_spec.decay_type
            )
            for e in past_events
        )

        score = 100.0 * (1.0 - math.exp(-decayed_mass / cat_spec.saturation_kappa))
        return round(float(score), 1)

    @classmethod
    def evaluate_vendor(
        cls,
        rubric: ScoringRubric,
        vendor_id: int | str,
        events: list[dict[str, Any]] | pd.DataFrame,
        as_of_day: int,
    ) -> VendorRiskEvaluation:
        """Evaluates a vendor against the rubric at `as_of_day` and calculates 30-day velocity."""
        records = events.to_dict(orient="records") if isinstance(events, pd.DataFrame) else events

        cat_scores_now: dict[str, float] = {}
        cat_scores_past: dict[str, float] = {}

        for cat in rubric.categories:
            cat_events = [e for e in records if e.get("category") == cat.name]
            cat_scores_now[cat.name] = cls.compute_category_score(cat, cat_events, as_of_day)
            cat_scores_past[cat.name] = cls.compute_category_score(cat, cat_events, as_of_day - 30)

        composite_now = sum(cat.weight * cat_scores_now[cat.name] for cat in rubric.categories)
        composite_past = sum(cat.weight * cat_scores_past[cat.name] for cat in rubric.categories)
        trend_30d = composite_now - composite_past

        watchlist = bool(
            composite_now >= rubric.watch_score_threshold
            or trend_30d >= rubric.watch_trend_threshold
        )

        return VendorRiskEvaluation(
            vendor_id=vendor_id,
            composite_score=round(composite_now, 1),
            category_scores=cat_scores_now,
            trend_30d=round(trend_30d, 1),
            watchlist_flag=watchlist,
            rubric_version=rubric.version,
        )

    @classmethod
    def create_default_rubric(cls) -> ScoringRubric:
        """Standard 5-category corporate third-party risk rubric."""
        return ScoringRubric(
            rubric_id="CORP-TPR-V1",
            version="1.2.0",
            categories=(
                CategorySpec(
                    name="security", weight=0.35, decay_half_life_days=90.0, saturation_kappa=5.0
                ),
                CategorySpec(
                    name="financial", weight=0.25, decay_half_life_days=90.0, saturation_kappa=5.0
                ),
                CategorySpec(
                    name="compliance", weight=0.15, decay_half_life_days=90.0, saturation_kappa=5.0
                ),
                CategorySpec(
                    name="delivery", weight=0.15, decay_half_life_days=90.0, saturation_kappa=5.0
                ),
                CategorySpec(
                    name="concentration",
                    weight=0.10,
                    decay_half_life_days=90.0,
                    saturation_kappa=5.0,
                ),
            ),
            watch_score_threshold=60.0,
            watch_trend_threshold=15.0,
        )
