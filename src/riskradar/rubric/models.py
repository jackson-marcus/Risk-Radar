"""Config-as-Code Scoring Rubric - Declarative Models.

Defines self-validating rubric specifications, decay schedules, and evaluation results.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class DecayType(StrEnum):
    EXPONENTIAL_HALF_LIFE = "EXPONENTIAL_HALF_LIFE"
    LINEAR = "LINEAR"
    STEP = "STEP"


@dataclass(frozen=True)
class CategorySpec:
    """Declarative specification of a single risk category."""

    name: str
    weight: float
    decay_half_life_days: float = 90.0
    saturation_kappa: float = 5.0
    decay_type: DecayType = DecayType.EXPONENTIAL_HALF_LIFE
    description: str = ""

    def __post_init__(self) -> None:
        if self.weight <= 0.0:
            raise ValueError(
                f"Category weight for '{self.name}' must be positive, got {self.weight}"
            )
        if self.decay_half_life_days <= 0.0:
            raise ValueError(
                f"Half life for '{self.name}' must be positive, got {self.decay_half_life_days}"
            )
        if self.saturation_kappa <= 0.0:
            raise ValueError(
                f"Saturation kappa for '{self.name}' must be positive, got {self.saturation_kappa}"
            )


@dataclass(frozen=True)
class ScoringRubric:
    """Config-as-Code Rubric defining risk categories, weights, and escalation thresholds."""

    rubric_id: str
    version: str
    categories: tuple[CategorySpec, ...]
    watch_score_threshold: float = 60.0
    watch_trend_threshold: float = 15.0

    def __post_init__(self) -> None:
        if not self.categories:
            raise ValueError("Rubric must contain at least one CategorySpec")
        total_weight = sum(c.weight for c in self.categories)
        if not math.isclose(total_weight, 1.0, rel_tol=1e-3, abs_tol=1e-3):
            raise ValueError(f"Rubric category weights must sum to 1.0, got {total_weight:.4f}")

    def get_category(self, name: str) -> CategorySpec | None:
        for c in self.categories:
            if c.name == name:
                return c
        return None


@dataclass(frozen=True)
class VendorRiskEvaluation:
    """Outcome of evaluating a vendor against a ScoringRubric."""

    vendor_id: int | str
    composite_score: float
    category_scores: dict[str, float]
    trend_30d: float
    watchlist_flag: bool
    rubric_version: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "vendor_id": self.vendor_id,
            "composite_score": round(self.composite_score, 1),
            "category_scores": {k: round(v, 1) for k, v in self.category_scores.items()},
            "trend_30d": round(self.trend_30d, 1),
            "watchlist": self.watchlist_flag,
            "rubric_version": self.rubric_version,
        }
