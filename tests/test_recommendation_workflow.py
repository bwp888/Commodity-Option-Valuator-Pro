"""
Commodity Option Valuator Pro
=============================

Recommendation Workflow Tests.

Commit 0019
-----------

Tests the integration between:

MarketValuationWorkflow
MarketRankingEngine
OpportunityAnalyzer
RecommendationEngine

Author : Simon
Version : 0.6.1
"""

from __future__ import annotations

from typing import Any

import pytest

from core.market_ranking import (
    MarketRankingEngine,
    RankingResult,
)

from core.market_valuation_workflow import (
    MarketValuationWorkflow,
    MarketValuationWorkflowResult,
)

from core.opportunity_analyzer import (
    OpportunityAnalysisResult,
    OpportunityAnalyzer,
)

from core.recommendation_engine import (
    RecommendationAction,
    RecommendationEngine,
    RecommendationLevel,
    RecommendationResult,
)

from core.recommendation_workflow import (
    RecommendationWorkflow,
    RecommendationWorkflowResult,
)

from models.option_scanner import (
    OptionDirection,
)


# ==========================================================
# Test Data
# ==========================================================


def make_records() -> list[dict[str, Any]]:
    """
    Create deterministic market records.
    """

    return [
        {
            "symbol": "TEST-C-100",
            "direction": "CALL",
            "strike": 100,
            "price": 5.0,
            "volume": 500,
            "open_interest": 1000,
            "bid": 4.9,
            "ask": 5.1,
        },
        {
            "symbol": "TEST-P-100",
            "direction": "PUT",
            "strike": 100,
            "price": 4.0,
            "volume": 400,
            "open_interest": 900,
            "bid": 3.9,
            "ask": 4.1,
        },
        {
            "symbol": "TEST-C-105",
            "direction": "CALL",
            "strike": 105,
            "price": 2.5,
            "volume": 800,
            "open_interest": 1500,
            "bid": 2.4,
            "ask": 2.6,
        },
    ]


def make_ranking_result() -> RankingResult:
    """
    Build a deterministic RankingResult through the
    existing valuation workflow.
    """

    valuation_workflow = MarketValuationWorkflow()

    valuation_result = valuation_workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    return valuation_workflow.rank_result(
        valuation_result
    )


# ==========================================================
# Import / Initialization
# ==========================================================


def test_recommendation_workflow_import() -> None:
    """Workflow should be importable."""

    workflow = RecommendationWorkflow()

    assert workflow is not None


def test_default_components_are_created() -> None:
    """Default components should be initialized."""

    workflow = RecommendationWorkflow()

    assert isinstance(
        workflow.valuation_workflow,
        MarketValuationWorkflow,
    )

    assert isinstance(
        workflow.opportunity_analyzer,
        OpportunityAnalyzer,
    )

    assert isinstance(
        workflow.recommendation_engine,
        RecommendationEngine,
    )


def test_custom_components_are_preserved() -> None:
    """Custom components should be preserved."""

    valuation_workflow = MarketValuationWorkflow()
    analyzer = OpportunityAnalyzer(
        strong_threshold=4.0,
        medium_threshold=1.0,
    )
    engine = RecommendationEngine(
        strong_score=3.0,
        watch_score=0.0,
        max_risk_score=6.0,
    )

    workflow = RecommendationWorkflow(
        valuation_workflow=valuation_workflow,
        opportunity_analyzer=analyzer,
        recommendation_engine=engine,
    )

    assert workflow.valuation_workflow is valuation_workflow
    assert workflow.opportunity_analyzer is analyzer
    assert workflow.recommendation_engine is engine


# ==========================================================
# Analysis
# ==========================================================


def test_analyze_result_returns_analysis_result() -> None:
    """Ranking result should be analyzable."""

    workflow = RecommendationWorkflow()

    ranking_result = make_ranking_result()

    analysis = workflow.analyze_result(
        ranking_result
    )

    assert isinstance(
        analysis,
        OpportunityAnalysisResult,
    )


def test_analyze_result_preserves_count() -> None:
    """Analysis should preserve ranking count."""

    workflow = RecommendationWorkflow()

    ranking_result = make_ranking_result()

    analysis = workflow.analyze_result(
        ranking_result
    )

    assert analysis.total_count == len(
        ranking_result.items
    )


def test_analyze_result_preserves_order() -> None:
    """Analysis should preserve ranking order."""

    workflow = RecommendationWorkflow()

    ranking_result = make_ranking_result()

    analysis = workflow.analyze_result(
        ranking_result
    )

    assert tuple(
        signal.symbol
        for signal in analysis.signals
    ) == tuple(
        item.contract.symbol
        for item in ranking_result.items
    )


def test_analyze_result_rejects_invalid_input() -> None:
    """Invalid ranking input should be rejected."""

    workflow = RecommendationWorkflow()

    with pytest.raises(
        TypeError,
        match="ranking_result must be a RankingResult",
    ):
        workflow.analyze_result(
            "invalid"  # type: ignore[arg-type]
        )


# ==========================================================
# Recommendation Result
# ==========================================================


def test_recommend_result_returns_workflow_result() -> None:
    """Existing ranking result should produce workflow result."""

    workflow = RecommendationWorkflow()

    ranking_result = make_ranking_result()

    result = workflow.recommend_result(
        ranking_result
    )

    assert isinstance(
        result,
        RecommendationWorkflowResult,
    )


def test_recommend_result_contains_analysis() -> None:
    """Workflow result should contain analysis."""

    workflow = RecommendationWorkflow()

    ranking_result = make_ranking_result()

    result = workflow.recommend_result(
        ranking_result
    )

    assert isinstance(
        result.analysis,
        OpportunityAnalysisResult,
    )


def test_recommend_result_contains_recommendations() -> None:
    """Workflow result should contain recommendation result."""

    workflow = RecommendationWorkflow()

    ranking_result = make_ranking_result()

    result = workflow.recommend_result(
        ranking_result
    )

    assert isinstance(
        result.recommendations,
        RecommendationResult,
    )


def test_recommend_result_preserves_count() -> None:
    """Recommendation count should match ranked count."""

    workflow = RecommendationWorkflow()

    ranking_result = make_ranking_result()

    result = workflow.recommend_result(
        ranking_result
    )

    assert result.ranked_count == len(
        ranking_result.items
    )

    assert result.total_count == len(
        ranking_result.items
    )


def test_recommend_result_preserves_symbols() -> None:
    """Recommendation symbols should map to ranked symbols."""

    workflow = RecommendationWorkflow()

    ranking_result = make_ranking_result()

    result = workflow.recommend_result(
        ranking_result
    )

    assert set(result.symbols) == {
        item.contract.symbol
        for item in ranking_result.items
    }


# ==========================================================
# Direction Mapping
# ==========================================================


def test_call_can_produce_buy_recommendation() -> None:
    """A strong CALL should become BUY."""

    workflow = RecommendationWorkflow(
        opportunity_analyzer=OpportunityAnalyzer(
            strong_threshold=-100.0,
            medium_threshold=-200.0,
        ),
        recommendation_engine=RecommendationEngine(
            strong_score=-100.0,
            watch_score=-200.0,
        ),
    )

    ranking_result = make_ranking_result()

    result = workflow.recommend_result(
        ranking_result
    )

    call_recommendations = [
        item
        for item in result.recommendations.recommendations
        if item.symbol.startswith("TEST-C")
    ]

    assert call_recommendations

    assert any(
        item.action == RecommendationAction.BUY
        for item in call_recommendations
    )


def test_put_can_produce_sell_recommendation() -> None:
    """A strong PUT should become SELL."""

    workflow = RecommendationWorkflow(
        opportunity_analyzer=OpportunityAnalyzer(
            strong_threshold=-100.0,
            medium_threshold=-200.0,
        ),
        recommendation_engine=RecommendationEngine(
            strong_score=-100.0,
            watch_score=-200.0,
        ),
    )

    ranking_result = make_ranking_result()

    result = workflow.recommend_result(
        ranking_result
    )

    put_recommendations = [
        item
        for item in result.recommendations.recommendations
        if item.symbol.startswith("TEST-P")
    ]

    assert put_recommendations

    assert any(
        item.action == RecommendationAction.SELL
        for item in put_recommendations
    )


# ==========================================================
# Risk Propagation
# ==========================================================


def test_risk_score_is_propagated_from_valuation() -> None:
    """
    Recommendation risk_score should come from the original
    ValuationResult rather than OpportunitySignal.
    """

    workflow = RecommendationWorkflow(
        opportunity_analyzer=OpportunityAnalyzer(
            strong_threshold=-100.0,
            medium_threshold=-200.0,
        ),
        recommendation_engine=RecommendationEngine(
            strong_score=-100.0,
            watch_score=-200.0,
        ),
    )

    ranking_result = make_ranking_result()

    result = workflow.recommend_result(
        ranking_result
    )

    by_symbol = {
        item.contract.symbol: item
        for item in ranking_result.items
    }

    for recommendation in (
        result.recommendations.recommendations
    ):
        expected = float(
            by_symbol[
                recommendation.symbol
            ].valuation.risk_score
        )

        assert recommendation.risk_score == pytest.approx(
            expected
        )


# ==========================================================
# Top N
# ==========================================================


def test_recommend_top_returns_requested_count() -> None:
    """Top N should limit the ranking before recommendation."""

    workflow = RecommendationWorkflow()

    ranking_result = make_ranking_result()

    result = workflow.recommend_top(
        ranking_result,
        n=2,
    )

    assert result.total_count == 2
    assert result.ranked_count == 2


def test_recommend_top_preserves_rank_order() -> None:
    """Top N should preserve the original ranking order."""

    workflow = RecommendationWorkflow()

    ranking_result = make_ranking_result()

    expected = tuple(
        item.contract.symbol
        for item in ranking_result.items[:2]
    )

    result = workflow.recommend_top(
        ranking_result,
        n=2,
    )

    assert result.symbols == expected


def test_recommend_top_larger_than_available() -> None:
    """TOP N larger than input should return all."""

    workflow = RecommendationWorkflow()

    ranking_result = make_ranking_result()

    result = workflow.recommend_top(
        ranking_result,
        n=100,
    )

    assert result.total_count == len(
        ranking_result.items
    )


def test_recommend_top_rejects_zero() -> None:
    """TOP N zero should be rejected."""

    workflow = RecommendationWorkflow()

    ranking_result = make_ranking_result()

    with pytest.raises(ValueError):
        workflow.recommend_top(
            ranking_result,
            n=0,
        )


def test_recommend_top_rejects_negative() -> None:
    """Negative TOP N should be rejected."""

    workflow = RecommendationWorkflow()

    ranking_result = make_ranking_result()

    with pytest.raises(ValueError):
        workflow.recommend_top(
            ranking_result,
            n=-1,
        )


# ==========================================================
# Direct Ranking Items
# ==========================================================


def test_recommend_items_accepts_ranking_items() -> None:
    """Ranking items should be accepted directly."""

    workflow = RecommendationWorkflow()

    ranking_result = make_ranking_result()

    result = workflow.recommend_items(
        ranking_result.items
    )

    assert isinstance(
        result,
        RecommendationWorkflowResult,
    )

    assert result.total_count == len(
        ranking_result.items
    )


def test_recommend_items_accepts_generator() -> None:
    """Ranking item generators should be supported."""

    workflow = RecommendationWorkflow()

    ranking_result = make_ranking_result()

    items = (
        item
        for item in ranking_result.items
    )

    result = workflow.recommend_items(
        items
    )

    assert result.total_count == len(
        ranking_result.items
    )


def test_recommend_items_empty() -> None:
    """Empty ranking items should produce empty output."""

    workflow = RecommendationWorkflow()

    result = workflow.recommend_items(
        []
    )

    assert result.ranked_count == 0
    assert result.total_count == 0
    assert result.recommendations.recommendations == ()
    assert result.analysis.signals == ()


# ==========================================================
# Complete Market Workflow
# ==========================================================


def test_run_returns_complete_result() -> None:
    """Complete market workflow should return recommendations."""

    workflow = RecommendationWorkflow()

    result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    assert isinstance(
        result,
        RecommendationWorkflowResult,
    )

    assert isinstance(
        result.analysis,
        OpportunityAnalysisResult,
    )

    assert isinstance(
        result.recommendations,
        RecommendationResult,
    )


def test_run_returns_all_recommendations_by_default() -> None:
    """Complete workflow should process all selected contracts."""

    workflow = RecommendationWorkflow()

    result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    assert result.total_count == 3
    assert result.ranked_count == 3


def test_run_supports_call_filter() -> None:
    """Complete workflow should support CALL filtering."""

    workflow = RecommendationWorkflow()

    result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
        direction="CALL",
    )

    assert result.total_count == 2

    for signal in result.analysis.signals:
        assert signal.direction == (
            OptionDirection.CALL.value
        )

    for recommendation in (
        result.recommendations.recommendations
    ):
        assert recommendation.action in {
            RecommendationAction.BUY,
            RecommendationAction.WATCH,
            RecommendationAction.REJECT,
        }


def test_run_supports_put_filter() -> None:
    """Complete workflow should support PUT filtering."""

    workflow = RecommendationWorkflow()

    result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
        direction="PUT",
    )

    assert result.total_count == 1

    assert result.analysis.signals[0].direction == (
        OptionDirection.PUT.value
    )

    assert result.recommendations.recommendations[0].action in {
        RecommendationAction.SELL,
        RecommendationAction.WATCH,
        RecommendationAction.REJECT,
    }


def test_run_supports_min_volume() -> None:
    """Complete workflow should support volume filtering."""

    workflow = RecommendationWorkflow()

    result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
        min_volume=500,
    )

    assert result.total_count == 2

    for signal in result.analysis.signals:
        assert signal.symbol in {
            "TEST-C-100",
            "TEST-C-105",
        }


def test_run_supports_top_n() -> None:
    """Complete workflow should support TOP N."""

    workflow = RecommendationWorkflow()

    result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
        top_n=2,
    )

    assert result.total_count == 2
    assert result.ranked_count == 2


def test_run_supports_combined_filters() -> None:
    """Direction and volume filters should combine."""

    workflow = RecommendationWorkflow()

    result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
        direction="CALL",
        min_volume=600,
    )

    assert result.total_count == 1

    assert result.symbols == (
        "TEST-C-105",
    )


# ==========================================================
# Existing Valuation Result
# ==========================================================


def test_recommend_valuation_result() -> None:
    """
    A completed valuation result should be reusable without
    running valuation again.
    """

    workflow = RecommendationWorkflow()

    valuation_result = workflow.valuation_workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    result = workflow.recommend_valuation_result(
        valuation_result
    )

    assert isinstance(
        result,
        RecommendationWorkflowResult,
    )

    assert result.total_count == (
        valuation_result.successful_count
    )


def test_recommend_valuation_result_supports_top_n() -> None:
    """Existing valuation result should support TOP N."""

    workflow = RecommendationWorkflow()

    valuation_result = workflow.valuation_workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    result = workflow.recommend_valuation_result(
        valuation_result,
        top_n=1,
    )

    assert result.total_count == 1
    assert result.ranked_count == 1


def test_recommend_valuation_result_rejects_invalid_input() -> None:
    """Invalid valuation result should be rejected."""

    workflow = RecommendationWorkflow()

    with pytest.raises(
        TypeError,
        match="valuation_result must be a",
    ):
        workflow.recommend_valuation_result(
            "invalid"  # type: ignore[arg-type]
        )


# ==========================================================
# Empty Data
# ==========================================================


def test_recommend_empty_ranking_result() -> None:
    """Empty ranking result should remain empty."""

    workflow = RecommendationWorkflow()

    ranking_result = RankingResult(
        items=(),
        total_count=0,
    )

    result = workflow.recommend_result(
        ranking_result
    )

    assert result.ranked_count == 0
    assert result.total_count == 0
    assert result.analysis.signals == ()
    assert result.recommendations.recommendations == ()
    assert result.top is None


def test_run_empty_records() -> None:
    """Complete workflow should handle empty records."""

    workflow = RecommendationWorkflow()

    result = workflow.run(
        records=[],
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    assert result.ranked_count == 0
    assert result.total_count == 0
    assert result.symbols == ()


# ==========================================================
# Input Validation
# ==========================================================


def test_recommend_result_rejects_invalid_input() -> None:
    """Invalid ranking result should be rejected."""

    workflow = RecommendationWorkflow()

    with pytest.raises(
        TypeError,
        match="ranking_result must be a RankingResult",
    ):
        workflow.recommend_result(
            "invalid"  # type: ignore[arg-type]
        )


def test_recommend_top_rejects_invalid_ranking_result() -> None:
    """Invalid ranking result should be rejected by top API."""

    workflow = RecommendationWorkflow()

    with pytest.raises(
        TypeError,
        match="ranking_result must be a RankingResult",
    ):
        workflow.recommend_top(
            "invalid",  # type: ignore[arg-type]
            n=1,
        )


def test_recommend_items_rejects_invalid_item() -> None:
    """Invalid ranking item should be rejected."""

    workflow = RecommendationWorkflow()

    with pytest.raises(
        TypeError,
        match="ranking_result.items must contain RankingItem",
    ):
        workflow.recommend_items(
            ["invalid"]  # type: ignore[list-item]
        )


# ==========================================================
# Immutability / Reusability
# ==========================================================


def test_original_ranking_result_is_not_modified() -> None:
    """Recommendation workflow must not modify ranking data."""

    workflow = RecommendationWorkflow()

    ranking_result = make_ranking_result()

    original_items = ranking_result.items

    workflow.recommend_result(
        ranking_result
    )

    assert ranking_result.items == original_items


def test_original_valuation_result_is_not_modified() -> None:
    """Existing valuation result must remain unchanged."""

    workflow = RecommendationWorkflow()

    valuation_result = workflow.valuation_workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    original_items = valuation_result.items

    workflow.recommend_valuation_result(
        valuation_result
    )

    assert valuation_result.items == original_items


def test_workflow_is_reusable() -> None:
    """The same workflow instance should be reusable."""

    workflow = RecommendationWorkflow()

    first = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
        top_n=2,
    )

    second = workflow.run(
        records=make_records(),
        underlying_price=101,
        days=20,
        volatility=0.25,
        top_n=1,
    )

    assert isinstance(
        first,
        RecommendationWorkflowResult,
    )

    assert isinstance(
        second,
        RecommendationWorkflowResult,
    )

    assert first.total_count == 2
    assert second.total_count == 1


# ==========================================================
# Recommendation Level Stability
# ==========================================================


def test_recommendation_levels_are_valid() -> None:
    """All generated levels should use stable enum values."""

    workflow = RecommendationWorkflow()

    result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    for recommendation in (
        result.recommendations.recommendations
    ):
        assert recommendation.level in {
            RecommendationLevel.A,
            RecommendationLevel.B,
            RecommendationLevel.C,
            RecommendationLevel.D,
        }


def test_recommendation_actions_are_valid() -> None:
    """All generated actions should use stable enum values."""

    workflow = RecommendationWorkflow()

    result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    for recommendation in (
        result.recommendations.recommendations
    ):
        assert recommendation.action in {
            RecommendationAction.BUY,
            RecommendationAction.SELL,
            RecommendationAction.WATCH,
            RecommendationAction.REJECT,
        }