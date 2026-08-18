"""
Tests for market valuation workflow.

Commit 0015
"""

from __future__ import annotations

import pytest

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


def make_records() -> list[dict[str, object]]:
    """Return sample market records."""

    return [
        {
            "symbol": "TEST-C-100",
            "direction": "CALL",
            "strike": 100,
            "price": 5.0,
            "volume": 500,
            "open_interest": 1000,
        },
        {
            "symbol": "TEST-C-110",
            "direction": "CALL",
            "strike": 110,
            "price": 2.5,
            "volume": 300,
            "open_interest": 800,
        },
        {
            "symbol": "TEST-P-100",
            "direction": "PUT",
            "strike": 100,
            "price": 4.0,
            "volume": 400,
            "open_interest": 900,
        },
        {
            "symbol": "TEST-P-110",
            "direction": "PUT",
            "strike": 110,
            "price": 8.0,
            "volume": 100,
            "open_interest": 500,
        },
    ]


# ==========================================================
# Import / Construction
# ==========================================================


def test_workflow_import() -> None:
    """Workflow should be importable."""

    workflow = MarketValuationWorkflow()

    assert isinstance(
        workflow,
        MarketValuationWorkflow,
    )


def test_workflow_has_adapter() -> None:
    """Workflow should create a market data adapter."""

    workflow = MarketValuationWorkflow()

    assert workflow.adapter is not None


def test_workflow_has_pipeline() -> None:
    """Workflow should create an option pipeline."""

    workflow = MarketValuationWorkflow()

    assert workflow.pipeline is not None


# ==========================================================
# Normalization
# ==========================================================


def test_normalize_records() -> None:
    """Market records should become contracts."""

    workflow = MarketValuationWorkflow()

    contracts = workflow.normalize_records(
        make_records()
    )

    assert len(contracts) == 4

    assert contracts[0].symbol == "TEST-C-100"

    assert (
        contracts[0].direction
        == OptionDirection.CALL
    )


def test_normalize_record() -> None:
    """One record should normalize correctly."""

    workflow = MarketValuationWorkflow()

    contract = workflow.normalize_record(
        make_records()[0]
    )

    assert contract.symbol == "TEST-C-100"

    assert contract.strike == 100

    assert contract.volume == 500


# ==========================================================
# Selection
# ==========================================================


def test_select_all_contracts() -> None:
    """All contracts should be selectable."""

    workflow = MarketValuationWorkflow()

    contracts = workflow.normalize_records(
        make_records()
    )

    selected = workflow.select_contracts(
        contracts
    )

    assert len(selected) == 4


def test_select_call_contracts() -> None:
    """CALL filtering should work."""

    workflow = MarketValuationWorkflow()

    contracts = workflow.normalize_records(
        make_records()
    )

    selected = workflow.select_contracts(
        contracts,
        direction="CALL",
    )

    assert len(selected) == 2

    assert all(
        contract.direction
        == OptionDirection.CALL
        for contract in selected
    )


def test_select_put_contracts() -> None:
    """PUT filtering should work."""

    workflow = MarketValuationWorkflow()

    contracts = workflow.normalize_records(
        make_records()
    )

    selected = workflow.select_contracts(
        contracts,
        direction="PUT",
    )

    assert len(selected) == 2

    assert all(
        contract.direction
        == OptionDirection.PUT
        for contract in selected
    )


def test_select_min_volume() -> None:
    """Minimum volume filtering should work."""

    workflow = MarketValuationWorkflow()

    contracts = workflow.normalize_records(
        make_records()
    )

    selected = workflow.select_contracts(
        contracts,
        min_volume=400,
    )

    assert len(selected) == 2

    assert all(
        contract.volume >= 400
        for contract in selected
    )


def test_select_top_n() -> None:
    """TOP N should limit selected contracts."""

    workflow = MarketValuationWorkflow()

    contracts = workflow.normalize_records(
        make_records()
    )

    selected = workflow.select_contracts(
        contracts,
        top_n=2,
    )

    assert len(selected) == 2

    assert selected[0].volume >= selected[1].volume


def test_select_combined_filters() -> None:
    """Direction, volume and TOP N should combine."""

    workflow = MarketValuationWorkflow()

    contracts = workflow.normalize_records(
        make_records()
    )

    selected = workflow.select_contracts(
        contracts,
        direction="CALL",
        min_volume=300,
        top_n=1,
    )

    assert len(selected) == 1

    assert (
        selected[0].direction
        == OptionDirection.CALL
    )

    assert selected[0].volume >= 300


def test_select_rejects_invalid_direction() -> None:
    """Invalid direction should raise ValueError."""

    workflow = MarketValuationWorkflow()

    contracts = workflow.normalize_records(
        make_records()
    )

    with pytest.raises(
        ValueError,
        match="无效的期权方向",
    ):
        workflow.select_contracts(
            contracts,
            direction="INVALID",
        )


def test_select_rejects_negative_volume() -> None:
    """Negative minimum volume should fail."""

    workflow = MarketValuationWorkflow()

    contracts = workflow.normalize_records(
        make_records()
    )

    with pytest.raises(
        ValueError,
        match="最低成交量",
    ):
        workflow.select_contracts(
            contracts,
            min_volume=-1,
        )


def test_select_rejects_invalid_top_n() -> None:
    """Invalid TOP N should fail."""

    workflow = MarketValuationWorkflow()

    contracts = workflow.normalize_records(
        make_records()
    )

    with pytest.raises(
        ValueError,
        match="TOP N",
    ):
        workflow.select_contracts(
            contracts,
            top_n=0,
        )


# ==========================================================
# Pipeline Parameters
# ==========================================================


def test_build_pipeline_parameters() -> None:
    """Pipeline parameters should contain market inputs."""

    workflow = MarketValuationWorkflow()

    contract = workflow.normalize_record(
        make_records()[0]
    )

    parameters = (
        workflow.build_pipeline_parameters(
            contract=contract,
            underlying_price=100,
            days=30,
            volatility=0.20,
            risk_free_rate=0.025,
        )
    )

    assert parameters.option == contract

    assert parameters.underlying_price == 100

    assert parameters.days == 30

    assert parameters.volatility == 0.20

    assert parameters.risk_free_rate == 0.025


# ==========================================================
# Single Valuation
# ==========================================================


def test_evaluate_contract() -> None:
    """One contract should be passed to OptionPipeline."""

    workflow = MarketValuationWorkflow()

    contract = workflow.normalize_record(
        make_records()[0]
    )

    result = workflow.evaluate_contract(
        contract=contract,
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    assert result is not None

    assert result.theoretical_price >= 0


# ==========================================================
# Batch Valuation
# ==========================================================


def test_evaluate_contracts() -> None:
    """Multiple contracts should be evaluated."""

    workflow = MarketValuationWorkflow()

    contracts = workflow.normalize_records(
        make_records()
    )

    result = workflow.evaluate_contracts(
        contracts=contracts,
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    assert isinstance(
        result,
        MarketValuationWorkflowResult,
    )

    assert result.total_contracts == 4

    assert result.selected_contracts == 4

    assert result.successful_count == 4

    assert len(result.items) == 4

    assert len(result.results) == 4

    assert len(result.contracts) == 4


# ==========================================================
# Complete Workflow
# ==========================================================


def test_run_complete_workflow() -> None:
    """Complete market-to-valuation workflow should work."""

    workflow = MarketValuationWorkflow()

    result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
        risk_free_rate=0.025,
    )

    assert isinstance(
        result,
        MarketValuationWorkflowResult,
    )

    assert result.total_contracts == 4

    assert result.selected_contracts == 4

    assert result.successful_count == 4


def test_run_with_call_filter() -> None:
    """Complete workflow should support CALL filtering."""

    workflow = MarketValuationWorkflow()

    result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
        direction="CALL",
    )

    assert result.total_contracts == 4

    assert result.selected_contracts == 2

    assert result.successful_count == 2

    assert all(
        item.contract.direction
        == OptionDirection.CALL
        for item in result.items
    )


def test_run_with_put_filter() -> None:
    """Complete workflow should support PUT filtering."""

    workflow = MarketValuationWorkflow()

    result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
        direction="PUT",
    )

    assert result.selected_contracts == 2

    assert result.successful_count == 2

    assert all(
        item.contract.direction
        == OptionDirection.PUT
        for item in result.items
    )


def test_run_with_volume_filter() -> None:
    """Complete workflow should support volume filtering."""

    workflow = MarketValuationWorkflow()

    result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
        min_volume=400,
    )

    assert result.total_contracts == 4

    assert result.selected_contracts == 2

    assert result.successful_count == 2


def test_run_with_top_n() -> None:
    """Complete workflow should support TOP N."""

    workflow = MarketValuationWorkflow()

    result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
        top_n=2,
    )

    assert result.selected_contracts == 2

    assert result.successful_count == 2

    assert (
        result.items[0].contract.volume
        >= result.items[1].contract.volume
    )


def test_run_empty_records() -> None:
    """Empty market data should produce an empty result."""

    workflow = MarketValuationWorkflow()

    result = workflow.run(
        records=[],
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    assert result.total_contracts == 0

    assert result.selected_contracts == 0

    assert result.successful_count == 0

    assert result.items == ()


# ==========================================================
# Reusability
# ==========================================================


def test_workflow_can_be_reused() -> None:
    """One workflow instance should support repeated runs."""

    workflow = MarketValuationWorkflow()

    first = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
    )

    second = workflow.run(
        records=make_records()[:2],
        underlying_price=100,
        days=20,
        volatility=0.25,
    )

    assert first.total_contracts == 4

    assert second.total_contracts == 2

    assert first.successful_count == 4

    assert second.successful_count == 2


def test_results_are_tuple_based() -> None:
    """Workflow results should expose immutable tuples."""

    workflow = MarketValuationWorkflow()

    result = workflow.run(
        records=make_records(),
        underlying_price=100,
        days=30,
        volatility=0.20,
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