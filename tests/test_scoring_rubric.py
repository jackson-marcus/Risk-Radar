"""Unit tests for the Config-as-Code Scoring Rubric Engine in RiskRadar."""

from __future__ import annotations

import pytest

from riskradar.rubric import (
    CategorySpec,
    DecayType,
    RubricScoringEngine,
    ScoringRubric,
    VendorRiskEvaluation,
)


@pytest.fixture
def sample_risk_events() -> list[dict]:
    return [
        {"vendor_id": 1, "day": 100, "category": "security", "severity": 3.0},
        {"vendor_id": 1, "day": 150, "category": "security", "severity": 4.0},
        {"vendor_id": 1, "day": 175, "category": "financial", "severity": 2.0},
    ]


def test_rubric_weight_validation():
    # Valid sum = 1.0
    rubric = ScoringRubric(
        rubric_id="TEST-01",
        version="1.0.0",
        categories=(
            CategorySpec(name="security", weight=0.6),
            CategorySpec(name="financial", weight=0.4),
        ),
    )
    assert rubric.version == "1.0.0"

    # Invalid sum != 1.0 raises ValueError
    with pytest.raises(ValueError, match=r"must sum to 1\.0"):
        ScoringRubric(
            rubric_id="TEST-02",
            version="1.0.0",
            categories=(
                CategorySpec(name="security", weight=0.5),
                CategorySpec(name="financial", weight=0.2),
            ),
        )


def test_rubric_scoring_decay_and_trend(sample_risk_events):
    rubric = RubricScoringEngine.create_default_rubric()
    eval_res: VendorRiskEvaluation = RubricScoringEngine.evaluate_vendor(
        rubric=rubric,
        vendor_id=1,
        events=sample_risk_events,
        as_of_day=180,
    )

    assert isinstance(eval_res, VendorRiskEvaluation)
    assert eval_res.vendor_id == 1
    assert 0.0 <= eval_res.composite_score <= 100.0
    assert eval_res.category_scores["security"] > 0.0
    assert eval_res.category_scores["financial"] > 0.0
    assert eval_res.category_scores["compliance"] == 0.0
    assert "composite_score" in eval_res.as_dict()


def test_custom_linear_decay_rubric():
    rubric = ScoringRubric(
        rubric_id="CUSTOM-LINEAR",
        version="2.0.0",
        categories=(
            CategorySpec(
                name="cyber",
                weight=1.0,
                decay_half_life_days=30.0,
                saturation_kappa=4.0,
                decay_type=DecayType.LINEAR,
            ),
        ),
        watch_score_threshold=50.0,
    )

    events = [{"vendor_id": 99, "day": 10, "category": "cyber", "severity": 4.0}]
    res = RubricScoringEngine.evaluate_vendor(rubric, vendor_id=99, events=events, as_of_day=20)
    assert res.composite_score > 0.0
