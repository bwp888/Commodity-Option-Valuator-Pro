"""
Commodity Option Valuator Pro
=============================

Tests for Recommendation Summary.

Commit 0020
-----------

Author : Simon
Version : 0.6.2
"""

from __future__ import annotations

import pytest

from core.recommendation_engine import (
    Recommendation,
    RecommendationAction,
    RecommendationLevel,
    RecommendationResult,
)

from core.recommendation_summary import (
    RecommendationSummary,
    RecommendationSummaryBuilder,
    summarize_recommendations,
    summarize_workflow,
)

from core.recommendation_workflow import (
    RecommendationWorkflowResult,
)

from core.opportunity_analyzer import (
    OpportunityAnalysisResult,
)


# ==========================================================
# Test Helpers
# ==========================================================


def make_recommendation(
    symbol: str,
    action: RecommendationAction,
    level: RecommendationLevel,
    score: float = 3.0,
    risk_score: float = 2.0,
) -> Recommendation:
    """
    Create a deterministic recommendation.
    """

    return Recommendation(
        symbol=symbol,
        action=action,
        level=level,
        score=score,
        risk_score=risk_score,
        reason="test recommendation",
    )


def make_result(
    *recommendations: Recommendation,
) -> RecommendationResult:
    """
    Create a RecommendationResult.
    """

    return RecommendationResult(
        recommendations=tuple(
            recommendations
        ),
        total_count=len(
            recommendations
        ),
    )


# ==========================================================
# Import
# ==========================================================


def test_summary_import() -> None:
    """
    Summary classes should be importable.
    """

    assert RecommendationSummary is not None
    assert RecommendationSummaryBuilder is not None


# ==========================================================
# Empty Result
# ==========================================================


def test_empty_result_summary() -> None:
    """
    Empty recommendation result should produce zero counts.
    """

    result = make_result()

    summary = summarize_recommendations(
        result
    )

    assert isinstance(
        summary,
        RecommendationSummary,
    )

    assert summary.total_count == 0
    assert summary.buy_count == 0
    assert summary.sell_count == 0
    assert summary.watch_count == 0
    assert summary.reject_count == 0

    assert summary.level_a_count == 0
    assert summary.level_b_count == 0
    assert summary.level_c_count == 0
    assert summary.level_d_count == 0

    assert summary.top is None
    assert summary.top_symbol is None
    assert summary.top_action is None
    assert summary.top_level is None

    assert summary.active_count == 0
    assert summary.has_active_recommendation is False


# ==========================================================
# Action Counts
# ==========================================================


def test_buy_count() -> None:
    """
    BUY recommendations should be counted.
    """

    result = make_result(
        make_recommendation(
            "CALL-100",
            RecommendationAction.BUY,
            RecommendationLevel.A,
        )
    )

    summary = summarize_recommendations(
        result
    )

    assert summary.buy_count == 1
    assert summary.active_count == 1


def test_sell_count() -> None:
    """
    SELL recommendations should be counted.
    """

    result = make_result(
        make_recommendation(
            "PUT-100",
            RecommendationAction.SELL,
            RecommendationLevel.A,
        )
    )

    summary = summarize_recommendations(
        result
    )

    assert summary.sell_count == 1
    assert summary.active_count == 1


def test_watch_count() -> None:
    """
    WATCH recommendations should be counted.
    """

    result = make_result(
        make_recommendation(
            "CALL-105",
            RecommendationAction.WATCH,
            RecommendationLevel.B,
        )
    )

    summary = summarize_recommendations(
        result
    )

    assert summary.watch_count == 1
    assert summary.active_count == 0


def test_reject_count() -> None:
    """
    REJECT recommendations should be counted.
    """

    result = make_result(
        make_recommendation(
            "CALL-110",
            RecommendationAction.REJECT,
            RecommendationLevel.C,
        )
    )

    summary = summarize_recommendations(
        result
    )

    assert summary.reject_count == 1
    assert summary.active_count == 0


# ==========================================================
# Level Counts
# ==========================================================


@pytest.mark.parametrize(
    (
        "level",
        "expected_a",
        "expected_b",
        "expected_c",
        "expected_d",
    ),
    [
        (
            RecommendationLevel.A,
            1,
            0,
            0,
            0,
        ),
        (
            RecommendationLevel.B,
            0,
            1,
            0,
            0,
        ),
        (
            RecommendationLevel.C,
            0,
            0,
            1,
            0,
        ),
        (
            RecommendationLevel.D,
            0,
            0,
            0,
            1,
        ),
    ],
)
def test_level_counts(
    level: RecommendationLevel,
    expected_a: int,
    expected_b: int,
    expected_c: int,
    expected_d: int,
) -> None:
    """
    Each recommendation level should be counted correctly.
    """

    result = make_result(
        make_recommendation(
            "TEST",
            RecommendationAction.WATCH,
            level,
        )
    )

    summary = summarize_recommendations(
        result
    )

    assert summary.level_a_count == expected_a
    assert summary.level_b_count == expected_b
    assert summary.level_c_count == expected_c
    assert summary.level_d_count == expected_d


# ==========================================================
# Mixed Result
# ==========================================================


def test_mixed_summary() -> None:
    """
    Mixed recommendations should produce correct totals.
    """

    result = make_result(
        make_recommendation(
            "A1",
            RecommendationAction.BUY,
            RecommendationLevel.A,
        ),
        make_recommendation(
            "A2",
            RecommendationAction.BUY,
            RecommendationLevel.A,
        ),
        make_recommendation(
            "B1",
            RecommendationAction.SELL,
            RecommendationLevel.B,
        ),
        make_recommendation(
            "B2",
            RecommendationAction.WATCH,
            RecommendationLevel.B,
        ),
        make_recommendation(
            "C1",
            RecommendationAction.REJECT,
            RecommendationLevel.C,
        ),
        make_recommendation(
            "D1",
            RecommendationAction.REJECT,
            RecommendationLevel.D,
        ),
    )

    summary = summarize_recommendations(
        result
    )

    assert summary.total_count == 6

    assert summary.buy_count == 2
    assert summary.sell_count == 1
    assert summary.watch_count == 1
    assert summary.reject_count == 2

    assert summary.level_a_count == 2
    assert summary.level_b_count == 2
    assert summary.level_c_count == 1
    assert summary.level_d_count == 1

    assert summary.active_count == 3
    assert summary.has_active_recommendation is True


# ==========================================================
# Top Recommendation
# ==========================================================


def test_top_recommendation_is_preserved() -> None:
    """
    Summary should preserve the top recommendation.
    """

    top = make_recommendation(
        "TOP",
        RecommendationAction.BUY,
        RecommendationLevel.A,
        score=5.0,
    )

    second = make_recommendation(
        "SECOND",
        RecommendationAction.WATCH,
        RecommendationLevel.B,
        score=1.0,
    )

    result = make_result(
        top,
        second,
    )

    summary = summarize_recommendations(
        result
    )

    assert summary.top is top
    assert summary.top_symbol == "TOP"
    assert summary.top_action == RecommendationAction.BUY
    assert summary.top_level == RecommendationLevel.A


# ==========================================================
# Action Counts Dictionary
# ==========================================================


def test_action_counts_dictionary() -> None:
    """
    Action counts should expose stable string keys.
    """

    result = make_result(
        make_recommendation(
            "BUY",
            RecommendationAction.BUY,
            RecommendationLevel.A,
        ),
        make_recommendation(
            "SELL",
            RecommendationAction.SELL,
            RecommendationLevel.A,
        ),
        make_recommendation(
            "WATCH",
            RecommendationAction.WATCH,
            RecommendationLevel.B,
        ),
        make_recommendation(
            "REJECT",
            RecommendationAction.REJECT,
            RecommendationLevel.C,
        ),
    )

    summary = summarize_recommendations(
        result
    )

    assert summary.action_counts == {
        "BUY": 1,
        "SELL": 1,
        "WATCH": 1,
        "REJECT": 1,
    }


# ==========================================================
# Level Counts Dictionary
# ==========================================================


def test_level_counts_dictionary() -> None:
    """
    Level counts should expose stable string keys.
    """

    result = make_result(
        make_recommendation(
            "A",
            RecommendationAction.BUY,
            RecommendationLevel.A,
        ),
        make_recommendation(
            "B",
            RecommendationAction.WATCH,
            RecommendationLevel.B,
        ),
        make_recommendation(
            "C",
            RecommendationAction.REJECT,
            RecommendationLevel.C,
        ),
        make_recommendation(
            "D",
            RecommendationAction.REJECT,
            RecommendationLevel.D,
        ),
    )

    summary = summarize_recommendations(
        result
    )

    assert summary.level_counts == {
        "A": 1,
        "B": 1,
        "C": 1,
        "D": 1,
    }


# ==========================================================
# Validation
# ==========================================================


def test_rejects_invalid_result() -> None:
    """
    Invalid result type should be rejected.
    """

    with pytest.raises(
        TypeError,
        match="result must be a RecommendationResult",
    ):
        RecommendationSummaryBuilder.from_result(
            "invalid"  # type: ignore[arg-type]
        )


def test_rejects_invalid_workflow_result() -> None:
    """
    Invalid workflow result should be rejected.
    """

    with pytest.raises(
        TypeError,
        match="workflow_result must be a RecommendationWorkflowResult",
    ):
        RecommendationSummaryBuilder.from_workflow(
            "invalid"  # type: ignore[arg-type]
        )


def test_rejects_inconsistent_total_count() -> None:
    """
    Inconsistent RecommendationResult should be rejected.
    """

    recommendation = make_recommendation(
        "TEST",
        RecommendationAction.BUY,
        RecommendationLevel.A,
    )

    result = RecommendationResult(
        recommendations=(
            recommendation,
        ),
        total_count=2,
    )

    with pytest.raises(
        ValueError,
        match="total_count",
    ):
        summarize_recommendations(
            result
        )


# ==========================================================
# Recommendation Validation
# ==========================================================


def test_recommendations_must_contain_recommendation() -> None:
    """
    Invalid recommendation members should be rejected.
    """

    result = RecommendationResult(
        recommendations=(
            "invalid",  # type: ignore[assignment]
        ),
        total_count=1,
    )

    with pytest.raises(
        TypeError,
        match="result.recommendations must contain Recommendation",
    ):
        summarize_recommendations(
            result
        )


# ==========================================================
# Workflow Integration
# ==========================================================


def test_workflow_summary() -> None:
    """
    Workflow result should be supported directly.
    """

    recommendation = make_recommendation(
        "TOP",
        RecommendationAction.BUY,
        RecommendationLevel.A,
    )

    recommendation_result = make_result(
        recommendation
    )

    workflow_result = RecommendationWorkflowResult(
        analysis=OpportunityAnalysisResult(
            signals=(),
            total_count=0,
        ),
        recommendations=recommendation_result,
        ranked_count=1,
    )

    summary = summarize_workflow(
        workflow_result
    )

    assert summary.total_count == 1
    assert summary.buy_count == 1
    assert summary.top_symbol == "TOP"


# ==========================================================
# Frozen Result
# ==========================================================


def test_summary_is_frozen() -> None:
    """
    Summary should be immutable.
    """

    result = make_result(
        make_recommendation(
            "TEST",
            RecommendationAction.BUY,
            RecommendationLevel.A,
        )
    )

    summary = summarize_recommendations(
        result
    )

    with pytest.raises(
        AttributeError
    ):
        summary.buy_count = 100  # type: ignore[misc]


# ==========================================================
# Convenience Functions
# ==========================================================


def test_summarize_recommendations_matches_builder() -> None:
    """
    Convenience function should match builder output.
    """

    result = make_result(
        make_recommendation(
            "TEST",
            RecommendationAction.BUY,
            RecommendationLevel.A,
        )
    )

    direct = summarize_recommendations(
        result
    )

    built = RecommendationSummaryBuilder.from_result(
        result
    )

    assert direct == built


# ==========================================================
# Active Recommendation Semantics
# ==========================================================


def test_watch_and_reject_are_not_active() -> None:
    """
    WATCH and REJECT should not count as active positions.
    """

    result = make_result(
        make_recommendation(
            "WATCH",
            RecommendationAction.WATCH,
            RecommendationLevel.B,
        ),
        make_recommendation(
            "REJECT",
            RecommendationAction.REJECT,
            RecommendationLevel.D,
        ),
    )

    summary = summarize_recommendations(
        result
    )

    assert summary.active_count == 0
    assert summary.has_active_recommendation is False


def test_buy_and_sell_are_active() -> None:
    """
    BUY and SELL should both count as active recommendations.
    """

    result = make_result(
        make_recommendation(
            "BUY",
            RecommendationAction.BUY,
            RecommendationLevel.A,
        ),
        make_recommendation(
            "SELL",
            RecommendationAction.SELL,
            RecommendationLevel.A,
        ),
    )

    summary = summarize_recommendations(
        result
    )

    assert summary.active_count == 2
    assert summary.has_active_recommendation is True


# ==========================================================
# Symbol Helpers
# ==========================================================


def test_top_helpers_for_empty_summary() -> None:
    """
    Empty summary top helpers should return None.
    """

    summary = summarize_recommendations(
        make_result()
    )

    assert summary.top_symbol is None
    assert summary.top_action is None
    assert summary.top_level is None


def test_top_helpers_for_existing_summary() -> None:
    """
    Top helpers should expose top recommendation fields.
    """

    recommendation = make_recommendation(
        "TOP",
        RecommendationAction.SELL,
        RecommendationLevel.B,
    )

    summary = summarize_recommendations(
        make_result(
            recommendation
        )
    )

    assert summary.top_symbol == "TOP"
    assert summary.top_action == RecommendationAction.SELL
    assert summary.top_level == RecommendationLevel.B