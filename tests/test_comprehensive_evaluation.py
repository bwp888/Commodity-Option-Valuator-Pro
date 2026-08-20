"""
Commodity Option Valuator Pro
=============================

Comprehensive Evaluation Tests.

Purpose
-------
Define the test contract for the unified comprehensive
evaluation layer used by:

1. Single-option valuation.
2. Scanner batch valuation.

Business Workflow
-----------------
Valuation
    ↓
Theoretical Price
Greeks
IV
Taylor
    ↓
Risk Analysis
    ↓
Opportunity Analysis
    ↓
Recommendation
    ↓
Comprehensive Evaluation

Important
---------
This test module defines the expected business contract
without modifying the existing RiskAnalyzer,
RecommendationEngine, or RecommendationWorkflow.

The final numerical thresholds for:

    RECOMMEND
    WATCH
    CAUTIOUS

must be established by the production evaluation model
before they are asserted as fixed numerical boundaries.

Author : Simon
Version : 0.1.0
Python : 3.12
"""

from __future__ import annotations

import math

import pytest

from core.recommendation_engine import (
    Recommendation,
    RecommendationAction,
    RecommendationEngine,
    RecommendationLevel,
    RecommendationResult,
)


# ==========================================================
# Recommendation Engine Baseline
# ==========================================================


def make_recommendation_engine() -> RecommendationEngine:
    """
    Create the project's existing RecommendationEngine.

    This helper intentionally uses the existing public
    interface rather than introducing a new interface.
    """

    return RecommendationEngine()


# ==========================================================
# Recommendation Result Contract
# ==========================================================


def test_recommendation_engine_exists() -> None:
    """
    Existing recommendation engine must remain available.
    """

    engine = make_recommendation_engine()

    assert isinstance(
        engine,
        RecommendationEngine,
    )


def test_recommendation_result_exists() -> None:
    """
    Existing RecommendationResult must remain available.
    """

    result = RecommendationResult(
        recommendations=(),
        total_count=0,
    )

    assert isinstance(
        result,
        RecommendationResult,
    )

    assert result.total_count == 0
    assert result.top is None
    assert result.symbols == ()


# ==========================================================
# Recommendation Output
# ==========================================================


@pytest.mark.parametrize(
    "direction",
    [
        "CALL",
        "PUT",
    ],
)
def test_active_recommendation_has_direction(
    direction: str,
) -> None:
    """
    Existing recommendation engine must continue to produce
    a direction-dependent active recommendation.

    CALL -> BUY
    PUT  -> SELL

    This preserves the existing RecommendationEngine
    contract.
    """

    engine = make_recommendation_engine()

    recommendation = engine.recommend(
        {
            "symbol": "TEST-OPTION",
            "score": engine.strong_score,
            "risk_score": 0.0,
            "direction": direction,
        }
    )

    assert isinstance(
        recommendation,
        Recommendation,
    )

    if direction == "CALL":
        assert (
            recommendation.action
            ==
            RecommendationAction.BUY
        )

    else:
        assert (
            recommendation.action
            ==
            RecommendationAction.SELL
        )


def test_recommendation_contains_reason() -> None:
    """
    Every recommendation must contain a human-readable
    reason.

    This is important because the final UI must explain
    why an option is recommended / watched / rejected.
    """

    engine = make_recommendation_engine()

    recommendation = engine.recommend(
        {
            "symbol": "TEST-C-100",
            "score": engine.strong_score,
            "risk_score": 0.0,
            "direction": "CALL",
        }
    )

    assert isinstance(
        recommendation.reason,
        str,
    )

    assert recommendation.reason.strip() != ""


def test_watch_recommendation_contains_reason() -> None:
    """
    WATCH recommendations must also explain the reason.
    """

    engine = make_recommendation_engine()

    recommendation = engine.recommend(
        {
            "symbol": "TEST-C-100",
            "score": engine.watch_score,
            "risk_score": 0.0,
            "direction": "CALL",
        }
    )

    assert (
        recommendation.action
        ==
        RecommendationAction.WATCH
    )

    assert isinstance(
        recommendation.reason,
        str,
    )

    assert recommendation.reason.strip() != ""


def test_rejected_recommendation_contains_reason() -> None:
    """
    REJECT recommendations must explain the rejection.
    """

    engine = make_recommendation_engine()

    recommendation = engine.recommend(
        {
            "symbol": "TEST-C-100",
            "score": -1.0,
            "risk_score": 0.0,
            "direction": "CALL",
        }
    )

    assert (
        recommendation.action
        ==
        RecommendationAction.REJECT
    )

    assert isinstance(
        recommendation.reason,
        str,
    )

    assert recommendation.reason.strip() != ""


# ==========================================================
# Risk-aware Recommendation
# ==========================================================


def test_excessive_risk_can_reject_opportunity() -> None:
    """
    Excessive risk must be able to prevent an otherwise
    strong opportunity from becoming an active position.

    This verifies the existing RecommendationEngine risk
    gate without imposing a new numerical risk model.
    """

    engine = make_recommendation_engine()

    recommendation = engine.recommend(
        {
            "symbol": "TEST-C-100",
            "score": engine.strong_score,
            "risk_score": (
                engine.max_risk_score
                +
                1.0
            ),
            "direction": "CALL",
        }
    )

    assert (
        recommendation.action
        ==
        RecommendationAction.REJECT
    )

    assert recommendation.risk_score > (
        engine.max_risk_score
    )

    assert (
        "risk"
        in recommendation.reason.lower()
    )


# ==========================================================
# Batch Recommendation
# ==========================================================


def test_recommend_all_returns_recommendation_result() -> None:
    """
    Existing batch recommendation workflow must return
    RecommendationResult.
    """

    engine = make_recommendation_engine()

    opportunities = [
        {
            "symbol": "TEST-C-100",
            "score": 3.0,
            "risk_score": 1.0,
            "direction": "CALL",
        },
        {
            "symbol": "TEST-P-100",
            "score": 1.0,
            "risk_score": 2.0,
            "direction": "PUT",
        },
    ]

    result = engine.recommend_all(
        opportunities
    )

    assert isinstance(
        result,
        RecommendationResult,
    )

    assert result.total_count == 2
    assert len(result.recommendations) == 2


def test_recommend_all_preserves_reasons() -> None:
    """
    Every batch recommendation must retain its reason.
    """

    engine = make_recommendation_engine()

    opportunities = [
        {
            "symbol": "TEST-C-100",
            "score": 3.0,
            "risk_score": 1.0,
            "direction": "CALL",
        },
        {
            "symbol": "TEST-P-100",
            "score": -1.0,
            "risk_score": 2.0,
            "direction": "PUT",
        },
    ]

    result = engine.recommend_all(
        opportunities
    )

    assert len(result.recommendations) == 2

    for item in result.recommendations:
        assert item.reason.strip() != ""


# ==========================================================
# Recommendation Data Integrity
# ==========================================================


def test_recommendation_score_is_numeric() -> None:
    """
    Recommendation score must remain numeric.
    """

    engine = make_recommendation_engine()

    recommendation = engine.recommend(
        {
            "symbol": "TEST-C-100",
            "score": 2.5,
            "risk_score": 1.5,
            "direction": "CALL",
        }
    )

    assert isinstance(
        recommendation.score,
        float,
    )

    assert math.isfinite(
        recommendation.score
    )


def test_recommendation_risk_score_is_numeric() -> None:
    """
    Recommendation risk score must remain numeric.
    """

    engine = make_recommendation_engine()

    recommendation = engine.recommend(
        {
            "symbol": "TEST-C-100",
            "score": 2.5,
            "risk_score": 1.5,
            "direction": "CALL",
        }
    )

    assert isinstance(
        recommendation.risk_score,
        float,
    )

    assert math.isfinite(
        recommendation.risk_score
    )


# ==========================================================
# Comprehensive Evaluation Business Contract
# ==========================================================


def test_comprehensive_evaluation_requires_reason() -> None:
    """
    Business contract:

    The final comprehensive evaluation presented to the
    user must provide an explanation.

    The current Recommendation object already satisfies
    this requirement through its ``reason`` field.
    """

    engine = make_recommendation_engine()

    recommendation = engine.recommend(
        {
            "symbol": "TEST-C-100",
            "score": 2.5,
            "risk_score": 1.0,
            "direction": "CALL",
        }
    )

    assert hasattr(
        recommendation,
        "reason",
    )

    assert recommendation.reason.strip()


def test_comprehensive_evaluation_contains_risk_information() -> None:
    """
    The final evaluation must retain risk information.

    The current Recommendation object provides
    ``risk_score`` and ``level``.
    """

    engine = make_recommendation_engine()

    recommendation = engine.recommend(
        {
            "symbol": "TEST-C-100",
            "score": 2.5,
            "risk_score": 1.0,
            "direction": "CALL",
        }
    )

    assert hasattr(
        recommendation,
        "risk_score",
    )

    assert hasattr(
        recommendation,
        "level",
    )


def test_comprehensive_evaluation_contains_opportunity_information() -> None:
    """
    The final evaluation must retain opportunity information.

    The current Recommendation object provides ``score``.
    """

    engine = make_recommendation_engine()

    recommendation = engine.recommend(
        {
            "symbol": "TEST-C-100",
            "score": 2.5,
            "risk_score": 1.0,
            "direction": "CALL",
        }
    )

    assert hasattr(
        recommendation,
        "score",
    )

    assert recommendation.score == 2.5


# ==========================================================
# Final Business Labels
# ==========================================================


def test_existing_recommendation_actions_are_stable() -> None:
    """
    Existing RecommendationEngine action values must remain
    stable while the new comprehensive evaluation layer is
    developed.

    The final UI may expose Chinese business labels such as:

        推荐
        关注
        谨慎

    but this test deliberately does not replace the existing
    BUY / SELL / WATCH / REJECT API yet.
    """

    assert RecommendationAction.BUY.value == "BUY"
    assert RecommendationAction.SELL.value == "SELL"
    assert RecommendationAction.WATCH.value == "WATCH"
    assert RecommendationAction.REJECT.value == "REJECT"


def test_existing_recommendation_levels_are_stable() -> None:
    """
    Existing A/B/C/D recommendation levels must remain
    compatible.
    """

    assert RecommendationLevel.A.value == "A"
    assert RecommendationLevel.B.value == "B"
    assert RecommendationLevel.C.value == "C"
    assert RecommendationLevel.D.value == "D"


# ==========================================================
# Explicitly Undetermined Thresholds
# ==========================================================


def test_comprehensive_thresholds_are_not_hardcoded_here() -> None:
    """
    Placeholder contract.

    The project has not yet formally fixed numerical
    thresholds mapping all valuation/risk factors to:

        推荐
        关注
        谨慎

    Therefore this test intentionally checks only that the
    existing recommendation engine exposes configurable
    thresholds.

    Numerical comprehensive-evaluation thresholds must be
    introduced together with the production evaluation
    interface, not guessed inside this test.
    """

    engine = make_recommendation_engine()

    assert isinstance(
        engine.strong_score,
        float,
    )

    assert isinstance(
        engine.watch_score,
        float,
    )

    assert isinstance(
        engine.max_risk_score,
        float,
    )