"""
Commodity Option Valuator Pro
=============================

Tests for Recommendation Engine.

Commit 0018
-----------

Author : Simon
Version : 0.6.0
"""

from __future__ import annotations

import pytest

from core.recommendation_engine import (
    Recommendation,
    RecommendationAction,
    RecommendationEngine,
    RecommendationLevel,
    RecommendationResult,
)


# ==========================================================
# Test Data
# ==========================================================


def make_opportunity(
    symbol: str = "TEST-C-100",
    score: float = 3.0,
    risk_score: float = 2.0,
    direction: str = "CALL",
) -> dict[str, object]:
    """Create a deterministic opportunity."""

    return {
        "symbol": symbol,
        "score": score,
        "risk_score": risk_score,
        "direction": direction,
    }


# ==========================================================
# Import
# ==========================================================


def test_recommendation_engine_import() -> None:
    """Engine should be importable."""

    engine = RecommendationEngine()

    assert engine is not None


# ==========================================================
# Structures
# ==========================================================


def test_recommendation_structure() -> None:
    """Recommendation should expose all fields."""

    recommendation = Recommendation(
        symbol="TEST-C-100",
        action=RecommendationAction.BUY,
        level=RecommendationLevel.A,
        score=3.0,
        risk_score=2.0,
        reason="test",
    )

    assert recommendation.symbol == "TEST-C-100"
    assert recommendation.action == RecommendationAction.BUY
    assert recommendation.level == RecommendationLevel.A
    assert recommendation.score == 3.0
    assert recommendation.risk_score == 2.0
    assert recommendation.reason == "test"


def test_recommendation_result_structure() -> None:
    """RecommendationResult should expose recommendations."""

    recommendation = Recommendation(
        symbol="TEST-C-100",
        action=RecommendationAction.BUY,
        level=RecommendationLevel.A,
        score=3.0,
        risk_score=2.0,
        reason="test",
    )

    result = RecommendationResult(
        recommendations=(recommendation,),
        total_count=1,
    )

    assert result.total_count == 1
    assert result.top is recommendation
    assert result.symbols == (
        "TEST-C-100",
    )


def test_recommendation_result_empty() -> None:
    """Empty result should be supported."""

    result = RecommendationResult(
        recommendations=(),
        total_count=0,
    )

    assert result.top is None
    assert result.symbols == ()
    assert result.total_count == 0


def test_recommendation_result_top_n() -> None:
    """top_n should return the requested number."""

    first = Recommendation(
        symbol="TEST-C-100",
        action=RecommendationAction.BUY,
        level=RecommendationLevel.A,
        score=5.0,
        risk_score=1.0,
        reason="test",
    )

    second = Recommendation(
        symbol="TEST-C-105",
        action=RecommendationAction.BUY,
        level=RecommendationLevel.B,
        score=3.0,
        risk_score=2.0,
        reason="test",
    )

    result = RecommendationResult(
        recommendations=(
            first,
            second,
        ),
        total_count=2,
    )

    top = result.top_n(1)

    assert len(top) == 1
    assert top[0] is first


def test_recommendation_result_top_n_rejects_zero() -> None:
    """top_n should reject zero."""

    result = RecommendationResult(
        recommendations=(),
        total_count=0,
    )

    with pytest.raises(ValueError):
        result.top_n(0)


# ==========================================================
# Initialization
# ==========================================================


def test_default_thresholds() -> None:
    """Default thresholds should be stored."""

    engine = RecommendationEngine()

    assert engine.strong_score == 2.0
    assert engine.watch_score == 0.0
    assert engine.max_risk_score == 7.0


def test_custom_thresholds() -> None:
    """Custom thresholds should be accepted."""

    engine = RecommendationEngine(
        strong_score=5.0,
        watch_score=1.0,
        max_risk_score=6.0,
    )

    assert engine.strong_score == 5.0
    assert engine.watch_score == 1.0
    assert engine.max_risk_score == 6.0


def test_rejects_invalid_score_thresholds() -> None:
    """Strong threshold must exceed watch threshold."""

    with pytest.raises(ValueError):
        RecommendationEngine(
            strong_score=1.0,
            watch_score=1.0,
        )


def test_rejects_negative_max_risk() -> None:
    """Maximum risk must not be negative."""

    with pytest.raises(ValueError):
        RecommendationEngine(
            max_risk_score=-1.0,
        )


# ==========================================================
# Direction
# ==========================================================


def test_call_direction_becomes_buy() -> None:
    """CALL opportunity should become BUY."""

    engine = RecommendationEngine()

    result = engine.recommend(
        make_opportunity(
            direction="CALL",
            score=3.0,
            risk_score=2.0,
        )
    )

    assert result.action == RecommendationAction.BUY


def test_put_direction_becomes_sell() -> None:
    """PUT opportunity should become SELL."""

    engine = RecommendationEngine()

    result = engine.recommend(
        make_opportunity(
            direction="PUT",
            score=3.0,
            risk_score=2.0,
        )
    )

    assert result.action == RecommendationAction.SELL


def test_direction_is_case_insensitive() -> None:
    """Direction normalization should ignore case."""

    engine = RecommendationEngine()

    result = engine.recommend(
        make_opportunity(
            direction="call",
        )
    )

    assert result.action == RecommendationAction.BUY


def test_invalid_direction_is_rejected() -> None:
    """Invalid direction should raise ValueError."""

    engine = RecommendationEngine()

    with pytest.raises(
        ValueError,
        match="invalid option direction",
    ):
        engine.recommend(
            make_opportunity(
                direction="INVALID",
            )
        )


# ==========================================================
# Active Recommendation
# ==========================================================


def test_high_score_call_is_level_a_buy() -> None:
    """Strong CALL opportunity should receive A BUY."""

    engine = RecommendationEngine()

    result = engine.recommend(
        make_opportunity(
            direction="CALL",
            score=3.0,
            risk_score=2.0,
        )
    )

    assert result.action == RecommendationAction.BUY
    assert result.level == RecommendationLevel.A


def test_high_score_put_is_level_a_sell() -> None:
    """Strong PUT opportunity should receive A SELL."""

    engine = RecommendationEngine()

    result = engine.recommend(
        make_opportunity(
            direction="PUT",
            score=3.0,
            risk_score=2.0,
        )
    )

    assert result.action == RecommendationAction.SELL
    assert result.level == RecommendationLevel.A


def test_score_at_strong_threshold_is_active() -> None:
    """Score exactly at strong threshold should be active."""

    engine = RecommendationEngine(
        strong_score=2.0,
    )

    result = engine.recommend(
        make_opportunity(
            score=2.0,
            risk_score=2.0,
        )
    )

    assert result.action == RecommendationAction.BUY


# ==========================================================
# Watch
# ==========================================================


def test_moderate_score_becomes_watch() -> None:
    """Moderate score should produce WATCH."""

    engine = RecommendationEngine()

    result = engine.recommend(
        make_opportunity(
            score=1.0,
            risk_score=2.0,
        )
    )

    assert result.action == RecommendationAction.WATCH
    assert result.level == RecommendationLevel.B


def test_zero_score_is_watch() -> None:
    """Score at watch threshold should remain observable."""

    engine = RecommendationEngine()

    result = engine.recommend(
        make_opportunity(
            score=0.0,
            risk_score=2.0,
        )
    )

    assert result.action == RecommendationAction.WATCH


# ==========================================================
# Reject
# ==========================================================


def test_negative_score_is_rejected() -> None:
    """Negative score should be rejected."""

    engine = RecommendationEngine()

    result = engine.recommend(
        make_opportunity(
            score=-1.0,
            risk_score=2.0,
        )
    )

    assert result.action == RecommendationAction.REJECT
    assert result.level == RecommendationLevel.C


def test_excessive_risk_is_rejected() -> None:
    """Risk above threshold should be rejected."""

    engine = RecommendationEngine()

    result = engine.recommend(
        make_opportunity(
            score=5.0,
            risk_score=8.0,
        )
    )

    assert result.action == RecommendationAction.REJECT
    assert result.level == RecommendationLevel.D


def test_risk_at_maximum_is_acceptable() -> None:
    """Risk exactly at threshold should remain acceptable."""

    engine = RecommendationEngine(
        max_risk_score=7.0,
    )

    result = engine.recommend(
        make_opportunity(
            score=3.0,
            risk_score=7.0,
        )
    )

    assert result.action == RecommendationAction.BUY
    assert result.level == RecommendationLevel.A


# ==========================================================
# Levels
# ==========================================================


def test_level_a_requires_strong_score_and_acceptable_risk() -> None:
    """A level should require strong score."""

    engine = RecommendationEngine()

    result = engine.recommend(
        make_opportunity(
            score=1.99,
            risk_score=2.0,
        )
    )

    assert result.level == RecommendationLevel.B


def test_level_b_for_moderate_opportunity() -> None:
    """Moderate opportunity should receive B."""

    engine = RecommendationEngine()

    result = engine.recommend(
        make_opportunity(
            score=1.0,
            risk_score=2.0,
        )
    )

    assert result.level == RecommendationLevel.B


def test_level_c_for_low_score() -> None:
    """Low score should receive C when risk is acceptable."""

    engine = RecommendationEngine()

    result = engine.recommend(
        make_opportunity(
            score=-1.0,
            risk_score=2.0,
        )
    )

    assert result.level == RecommendationLevel.C


def test_level_d_for_excessive_risk() -> None:
    """Excessive risk should receive D."""

    engine = RecommendationEngine()

    result = engine.recommend(
        make_opportunity(
            score=5.0,
            risk_score=8.0,
        )
    )

    assert result.level == RecommendationLevel.D


# ==========================================================
# Reasons
# ==========================================================


def test_buy_reason_is_present() -> None:
    """BUY recommendation should have a meaningful reason."""

    engine = RecommendationEngine()

    result = engine.recommend(
        make_opportunity(
            direction="CALL",
            score=3.0,
            risk_score=2.0,
        )
    )

    assert "CALL" in result.reason
    assert "score" in result.reason
    assert "risk" in result.reason


def test_sell_reason_is_present() -> None:
    """SELL recommendation should have a meaningful reason."""

    engine = RecommendationEngine()

    result = engine.recommend(
        make_opportunity(
            direction="PUT",
            score=3.0,
            risk_score=2.0,
        )
    )

    assert "PUT" in result.reason
    assert "score" in result.reason
    assert "risk" in result.reason


def test_watch_reason_is_present() -> None:
    """WATCH recommendation should explain the threshold."""

    engine = RecommendationEngine()

    result = engine.recommend(
        make_opportunity(
            score=1.0,
            risk_score=2.0,
        )
    )

    assert "threshold" in result.reason


def test_reject_reason_for_high_risk() -> None:
    """High-risk rejection should explain the risk."""

    engine = RecommendationEngine()

    result = engine.recommend(
        make_opportunity(
            score=5.0,
            risk_score=8.0,
        )
    )

    assert "Risk score" in result.reason


def test_reject_reason_for_low_score() -> None:
    """Low-score rejection should explain the score."""

    engine = RecommendationEngine()

    result = engine.recommend(
        make_opportunity(
            score=-1.0,
            risk_score=2.0,
        )
    )

    assert "Opportunity score" in result.reason


# ==========================================================
# Input Validation
# ==========================================================


def test_non_dictionary_opportunity_is_rejected() -> None:
    """Opportunity must be a dictionary."""

    engine = RecommendationEngine()

    with pytest.raises(TypeError):
        engine.recommend(
            "invalid"  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "missing_field",
    [
        "symbol",
        "score",
        "risk_score",
        "direction",
    ],
)
def test_missing_required_field_is_rejected(
    missing_field: str,
) -> None:
    """Required opportunity fields must be present."""

    engine = RecommendationEngine()

    opportunity = make_opportunity()

    del opportunity[missing_field]

    with pytest.raises(
        ValueError,
        match="missing opportunity field",
    ):
        engine.recommend(
            opportunity
        )


def test_empty_symbol_is_rejected() -> None:
    """Symbol must not be empty."""

    engine = RecommendationEngine()

    with pytest.raises(
        ValueError,
        match="symbol must not be empty",
    ):
        engine.recommend(
            make_opportunity(
                symbol="",
            )
        )


def test_numeric_values_are_converted_to_float() -> None:
    """Numeric input values should be normalized."""

    engine = RecommendationEngine()

    result = engine.recommend(
        make_opportunity(
            score=3,
            risk_score=2,
        )
    )

    assert isinstance(
        result.score,
        float,
    )

    assert isinstance(
        result.risk_score,
        float,
    )


# ==========================================================
# Batch
# ==========================================================


def test_recommend_all() -> None:
    """Batch recommendation should process all records."""

    engine = RecommendationEngine()

    opportunities = [
        make_opportunity(
            symbol="TEST-C-100",
            direction="CALL",
            score=3.0,
            risk_score=2.0,
        ),
        make_opportunity(
            symbol="TEST-P-100",
            direction="PUT",
            score=1.0,
            risk_score=2.0,
        ),
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


def test_recommend_all_accepts_generator() -> None:
    """Batch recommendation should accept generators."""

    engine = RecommendationEngine()

    opportunities = (
        make_opportunity(
            symbol=f"TEST-C-{index}",
        )
        for index in range(3)
    )

    result = engine.recommend_all(
        opportunities
    )

    assert result.total_count == 3


def test_recommend_all_sorts_a_before_b() -> None:
    """A-level recommendations should rank before B."""

    engine = RecommendationEngine()

    opportunities = [
        make_opportunity(
            symbol="WATCH",
            score=1.0,
            risk_score=1.0,
        ),
        make_opportunity(
            symbol="STRONG",
            score=5.0,
            risk_score=1.0,
        ),
    ]

    result = engine.recommend_all(
        opportunities
    )

    assert result.symbols == (
        "STRONG",
        "WATCH",
    )


def test_recommend_all_sorts_by_score_within_level() -> None:
    """Higher score should rank first within the same level."""

    engine = RecommendationEngine()

    opportunities = [
        make_opportunity(
            symbol="LOW",
            score=2.5,
            risk_score=1.0,
        ),
        make_opportunity(
            symbol="HIGH",
            score=5.0,
            risk_score=1.0,
        ),
    ]

    result = engine.recommend_all(
        opportunities
    )

    assert result.symbols == (
        "HIGH",
        "LOW",
    )


def test_recommend_all_uses_lower_risk_as_tiebreaker() -> None:
    """Lower risk should win an otherwise equal score."""

    engine = RecommendationEngine()

    opportunities = [
        make_opportunity(
            symbol="HIGH-RISK",
            score=3.0,
            risk_score=5.0,
        ),
        make_opportunity(
            symbol="LOW-RISK",
            score=3.0,
            risk_score=2.0,
        ),
    ]

    result = engine.recommend_all(
        opportunities
    )

    assert result.symbols == (
        "LOW-RISK",
        "HIGH-RISK",
    )


def test_recommend_all_empty() -> None:
    """Empty batch should return empty result."""

    engine = RecommendationEngine()

    result = engine.recommend_all(
        []
    )

    assert result.recommendations == ()
    assert result.total_count == 0


# ==========================================================
# Top N
# ==========================================================


def test_recommend_top() -> None:
    """recommend_top should return requested number."""

    engine = RecommendationEngine()

    opportunities = [
        make_opportunity(
            symbol="ONE",
            score=5.0,
        ),
        make_opportunity(
            symbol="TWO",
            score=3.0,
        ),
        make_opportunity(
            symbol="THREE",
            score=1.0,
        ),
    ]

    result = engine.recommend_top(
        opportunities,
        n=2,
    )

    assert result.total_count == 2
    assert result.symbols == (
        "ONE",
        "TWO",
    )


def test_recommend_top_more_than_available() -> None:
    """TOP N larger than input should return all."""

    engine = RecommendationEngine()

    result = engine.recommend_top(
        [
            make_opportunity(
                symbol="ONE",
            ),
        ],
        n=10,
    )

    assert result.total_count == 1
    assert result.symbols == (
        "ONE",
    )


def test_recommend_top_rejects_zero() -> None:
    """TOP N zero should be rejected."""

    engine = RecommendationEngine()

    with pytest.raises(ValueError):
        engine.recommend_top(
            [],
            n=0,
        )


def test_recommend_top_rejects_negative() -> None:
    """Negative TOP N should be rejected."""

    engine = RecommendationEngine()

    with pytest.raises(ValueError):
        engine.recommend_top(
            [],
            n=-1,
        )


# ==========================================================
# Threshold Behavior
# ==========================================================


def test_custom_threshold_changes_action() -> None:
    """Custom strong threshold should affect action."""

    engine = RecommendationEngine(
        strong_score=5.0,
        watch_score=0.0,
    )

    result = engine.recommend(
        make_opportunity(
            score=3.0,
        )
    )

    assert result.action == RecommendationAction.WATCH
    assert result.level == RecommendationLevel.B


def test_custom_watch_threshold_changes_rejection() -> None:
    """Custom watch threshold should affect rejection."""

    engine = RecommendationEngine(
        strong_score=5.0,
        watch_score=2.0,
    )

    result = engine.recommend(
        make_opportunity(
            score=1.0,
        )
    )

    assert result.action == RecommendationAction.REJECT
    assert result.level == RecommendationLevel.C


def test_custom_risk_threshold_changes_recommendation() -> None:
    """Custom risk threshold should affect rejection."""

    engine = RecommendationEngine(
        max_risk_score=3.0,
    )

    result = engine.recommend(
        make_opportunity(
            score=5.0,
            risk_score=4.0,
        )
    )

    assert result.action == RecommendationAction.REJECT
    assert result.level == RecommendationLevel.D


# ==========================================================
# Enum Stability
# ==========================================================


def test_action_values_are_stable() -> None:
    """Recommendation action values should remain stable."""

    assert RecommendationAction.BUY.value == "BUY"
    assert RecommendationAction.SELL.value == "SELL"
    assert RecommendationAction.WATCH.value == "WATCH"
    assert RecommendationAction.REJECT.value == "REJECT"


def test_level_values_are_stable() -> None:
    """Recommendation level values should remain stable."""

    assert RecommendationLevel.A.value == "A"
    assert RecommendationLevel.B.value == "B"
    assert RecommendationLevel.C.value == "C"
    assert RecommendationLevel.D.value == "D"