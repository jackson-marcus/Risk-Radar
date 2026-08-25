"""Config-as-Code Scoring Rubric Package for RiskRadar.

Provides declarative CategorySpec, ScoringRubric, and RubricScoringEngine.
"""

from riskradar.rubric.engine import RubricScoringEngine
from riskradar.rubric.models import (
    CategorySpec,
    DecayType,
    ScoringRubric,
    VendorRiskEvaluation,
)

__all__ = [
    "CategorySpec",
    "DecayType",
    "RubricScoringEngine",
    "ScoringRubric",
    "VendorRiskEvaluation",
]
