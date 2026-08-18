"""
Commodity Option Valuator Pro
=============================

Market Ranking Workflow Tests.

Commit 0016
-----------

Test integration between MarketValuationWorkflow
and MarketRankingEngine.

Author : Simon
Version : 0.5.0
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

from models.option_scanner import (
    OptionDirection,
)


# ==========================================================
# Test Data
# ==========================================================


def make_records() -> list[dict[str, Any]]:
    """
    Create deterministic market records for tests.
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


# ==========================================================
# Import / Initialization
# ==========================================================


def test_workflow_has_ranking_engine() -> None:
    """
    Workflow should initialize a ranking engine.
    """

    workflow = MarketValuationWorkflow()

    assert isinstance(
        workflow.ranking_engine,
        MarketRankingEngine,
    )


def test_workflow_accepts_custom_ranking_engine() -> None:
    """
    Workflow should accept a custom ranking engine.
    """

    engine = MarketRankingEngine()

    workflow = MarketValuationWorkflow(
        ranking_engine=engine,
    )

    assert workflow.ranking_engine is engine


# ==========================================================
# Ranking Completed Result
# ==========================================================


def test_rank_result_returns_ranking_result() -> None:
    """
    A completed valuation result should be rankable.
    """

    workflow = MarketValuationWorkflow()

    valuation_result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    ranked = workflow.rank_result(
        valuation_result,
    )

    assert isinstance(
        ranked,
        RankingResult,
    )


def test_rank_result_preserves_contract_count() -> None:
    """
    Ranking should contain all valued contracts by default.
    """

    workflow = MarketValuationWorkflow()

    valuation_result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    ranked = workflow.rank_result(
        valuation_result,
    )

    assert ranked.total_count == (
        valuation_result.successful_count
    )


def test_rank_result_supports_top_n() -> None:
    """
    Ranking should support TOP N.
    """

    workflow = MarketValuationWorkflow()

    valuation_result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    ranked = workflow.rank_result(
        valuation_result,
        top_n=2,
    )

    assert len(ranked.items) == 2


# ==========================================================
# Direction Filters
# ==========================================================


def test_rank_call_workflow() -> None:
    """
    CALL filtering should work before ranking.
    """

    workflow = MarketValuationWorkflow()

    valuation_result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
        direction="CALL",
    )

    ranked = workflow.rank_result(
        valuation_result,
    )

    assert len(ranked.items) == 2

    for item in ranked.items:
        assert (
            item.contract.direction
            == OptionDirection.CALL
        )


def test_rank_put_workflow() -> None:
    """
    PUT filtering should work before ranking.
    """

    workflow = MarketValuationWorkflow()

    valuation_result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
        direction="PUT",
    )

    ranked = workflow.rank_result(
        valuation_result,
    )

    assert len(ranked.items) == 1

    assert (
        ranked.items[0].contract.direction
        == OptionDirection.PUT
    )


# ==========================================================
# Volume Filters
# ==========================================================


def test_rank_with_min_volume() -> None:
    """
    Minimum volume filtering should work before ranking.
    """

    workflow = MarketValuationWorkflow()

    valuation_result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
        min_volume=500,
    )

    ranked = workflow.rank_result(
        valuation_result,
    )

    assert len(ranked.items) == 2

    for item in ranked.items:
        assert item.contract.volume >= 500


# ==========================================================
# Combined Filters
# ==========================================================


def test_rank_with_combined_filters() -> None:
    """
    Direction and volume filters should combine correctly.
    """

    workflow = MarketValuationWorkflow()

    valuation_result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
        direction="CALL",
        min_volume=600,
    )

    ranked = workflow.rank_result(
        valuation_result,
    )

    assert len(ranked.items) == 1

    assert (
        ranked.items[0].contract.symbol
        == "TEST-C-105"
    )


# ==========================================================
# Rank Items Convenience API
# ==========================================================


def test_rank_items_accepts_workflow_items() -> None:
    """
    rank_items should accept workflow items directly.
    """

    workflow = MarketValuationWorkflow()

    valuation_result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    ranked = workflow.rank_items(
        valuation_result.items,
    )

    assert isinstance(
        ranked,
        RankingResult,
    )

    assert ranked.total_count == 3


def test_rank_items_accepts_generator() -> None:
    """
    rank_items should accept generators.
    """

    workflow = MarketValuationWorkflow()

    valuation_result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    items = (
        item
        for item in valuation_result.items
    )

    ranked = workflow.rank_items(
        items,
    )

    assert ranked.total_count == 3


# ==========================================================
# Run And Rank
# ==========================================================


def test_run_and_rank_returns_ranking_result() -> None:
    """
    Complete valuation + ranking workflow should work.
    """

    workflow = MarketValuationWorkflow()

    result = workflow.run_and_rank(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    assert isinstance(
        result,
        RankingResult,
    )


def test_run_and_rank_supports_top_n() -> None:
    """
    run_and_rank should support TOP N ranking.
    """

    workflow = MarketValuationWorkflow()

    result = workflow.run_and_rank(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
        top_n=2,
    )

    assert len(result.items) == 2


def test_run_and_rank_supports_call_filter() -> None:
    """
    run_and_rank should support CALL filtering.
    """

    workflow = MarketValuationWorkflow()

    result = workflow.run_and_rank(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
        direction="CALL",
    )

    assert len(result.items) == 2

    for item in result.items:
        assert (
            item.contract.direction
            == OptionDirection.CALL
        )


def test_run_and_rank_supports_put_filter() -> None:
    """
    run_and_rank should support PUT filtering.
    """

    workflow = MarketValuationWorkflow()

    result = workflow.run_and_rank(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
        direction="PUT",
    )

    assert len(result.items) == 1

    assert (
        result.items[0].contract.direction
        == OptionDirection.PUT
    )


# ==========================================================
# Empty Data
# ==========================================================


def test_rank_empty_workflow_result() -> None:
    """
    Empty valuation result should produce empty ranking.
    """

    workflow = MarketValuationWorkflow()

    valuation_result = workflow.run(
        records=[],
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    ranked = workflow.rank_result(
        valuation_result,
    )

    assert isinstance(
        ranked,
        RankingResult,
    )

    assert ranked.total_count == 0

    assert ranked.items == ()


def test_run_and_rank_empty_records() -> None:
    """
    run_and_rank should handle empty records.
    """

    workflow = MarketValuationWorkflow()

    result = workflow.run_and_rank(
        records=[],
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    assert result.total_count == 0

    assert result.items == ()


# ==========================================================
# Result Immutability
# ==========================================================


def test_rank_result_does_not_modify_workflow_result() -> None:
    """
    Ranking should not mutate the original valuation result.
    """

    workflow = MarketValuationWorkflow()

    valuation_result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    original_items = valuation_result.items

    workflow.rank_result(
        valuation_result,
        top_n=1,
    )

    assert valuation_result.items == original_items


# ==========================================================
# Reusability
# ==========================================================


def test_workflow_can_run_and_rank_repeatedly() -> None:
    """
    The same workflow instance should support repeated
    valuation and ranking operations.
    """

    workflow = MarketValuationWorkflow()

    first = workflow.run_and_rank(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
        top_n=2,
    )

    second = workflow.run_and_rank(
        records=make_records(),
        underlying_price=101,
        days=20,
        volatility=0.25,
        top_n=1,
    )

    assert isinstance(
        first,
        RankingResult,
    )

    assert isinstance(
        second,
        RankingResult,
    )

    assert len(first.items) == 2
    assert len(second.items) == 1


# ==========================================================
# Invalid Ranking Parameters
# ==========================================================


def test_rank_result_rejects_invalid_top_n() -> None:
    """
    Ranking engine should reject invalid TOP N values.
    """

    workflow = MarketValuationWorkflow()

    valuation_result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    with pytest.raises(
        ValueError
    ):
        workflow.rank_result(
            valuation_result,
            top_n=0,
        )


def test_run_and_rank_rejects_invalid_top_n() -> None:
    """
    run_and_rank should reject invalid TOP N values.
    """

    workflow = MarketValuationWorkflow()

    with pytest.raises(
        ValueError
    ):
        workflow.run_and_rank(
            records=make_records(),
            underlying_price=100,
            days=30,
            volatility=0.20,
            top_n=0,
        )


# ==========================================================
# Public API
# ==========================================================


def test_workflow_result_type_is_stable() -> None:
    """
    Existing workflow result API should remain unchanged.
    """

    workflow = MarketValuationWorkflow()

    result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    assert isinstance(
        result,
        MarketValuationWorkflowResult,
    )

    assert isinstance(
        result.items,
        tuple,
    )

    assert isinstance(
        result.results,
        tuple,
    )

    assert isinstance(
        result.contracts,
        tuple,
    )


def test_ranking_does_not_replace_existing_run_api() -> None:
    """
    Existing run() should still return the valuation
    workflow result rather than RankingResult.
    """

    workflow = MarketValuationWorkflow()

    result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    assert isinstance(
        result,
        MarketValuationWorkflowResult,
    )

    assert not isinstance(
        result,
        RankingResult,
    )