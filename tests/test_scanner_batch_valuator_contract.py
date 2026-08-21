"""
Commodity Option Valuator Pro
=============================

Scanner Batch Valuator Contract Tests.

Commit 0034 - Phase 1
---------------------

Purpose
-------
Lock the existing ScannerBatchValuator contract before adding
boundary and exception tests.

The tests in this module are intentionally based on the current
production contracts:

    OptionQuote
        ↓
    ScannerCandidate
        ↓
    ScannerValuationBridge
        ↓
    ScannerBatchValuator
        ↓
    SingleOptionValuationInput
        ↓
    SingleOptionValuator
        ↓
    BatchValuationResult

Important
---------
This module tests the existing production contracts.

It does NOT redesign or modify:

- ScannerBatchValuator
- ScannerValuationBridge
- SingleOptionValuator
- ScannerBatchWorkflow
- ScannerComprehensiveEvaluator
- ui/scanner.py
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from core.scanner_batch_valuation import (
    BatchValuationParameters,
    BatchValuationResult,
    ScannerBatchValuator,
)
from core.scanner_valuation_bridge import (
    ScannerCandidate,
    ScannerValuationBridge,
)
from core.single_option_valuation import (
    ReferenceVolatilityScenario,
    SingleOptionValuationInput,
    SingleOptionValuationResult,
    SingleOptionValuator,
)
from data.option_chain import OptionQuote
from models.option import OptionDirection


# ============================================================
# Helpers
# ============================================================


def make_quote(
    symbol: str,
    *,
    underlying: str = "AU2608",
    option_type: str = "CALL",
    strike: float = 100.0,
    last_price: float = 5.0,
    volume: int = 100,
    open_interest: int = 500,
    implied_volatility: float = 0.20,
) -> OptionQuote:
    """
    Create a real production OptionQuote.

    No test-only replacement of OptionQuote is introduced.
    """
    return OptionQuote(
        symbol=symbol,
        underlying=underlying,
        option_type=option_type,
        strike=strike,
        last_price=last_price,
        volume=volume,
        open_interest=open_interest,
        implied_volatility=implied_volatility,
    )


def make_candidate(
    symbol: str,
    *,
    underlying: str = "AU2608",
    option_type: str = "CALL",
    strike: float = 100.0,
    volume: int = 100,
) -> ScannerCandidate:
    """
    Create the real production ScannerCandidate.
    """
    quote = make_quote(
        symbol,
        underlying=underlying,
        option_type=option_type,
        strike=strike,
        volume=volume,
    )

    return ScannerCandidate(
        quote=quote,
    )


def make_parameters(
    *,
    underlyings: tuple[str, ...] = ("AU2608",),
) -> BatchValuationParameters:
    """
    Create the real production BatchValuationParameters.

    Every underlying represented by the selected candidates receives
    complete parameter coverage.
    """
    current_futures_prices = {
        underlying: 100.0
        for underlying in underlyings
    }

    target_futures_prices = {
        underlying: 105.0
        for underlying in underlyings
    }

    remaining_days = {
        underlying: 30
        for underlying in underlyings
    }

    reference_volatility = {
        underlying: ReferenceVolatilityScenario(
            current=0.20,
            target=0.22,
        )
        for underlying in underlyings
    }

    return BatchValuationParameters(
        current_futures_prices=current_futures_prices,
        target_futures_prices=target_futures_prices,
        remaining_days=remaining_days,
        reference_volatility=reference_volatility,
        risk_free_rate=0.025,
        direction=OptionDirection.LONG,
    )


def make_valuator(
    *,
    candidates: tuple[ScannerCandidate, ...],
) -> tuple[
    ScannerBatchValuator,
    Mock,
    Mock,
]:
    """
    Build ScannerBatchValuator using the real production contracts.

    Only the external bridge / single-option valuation service is
    mocked.

    The bridge mock deliberately returns the REAL grouped-selection
    contract:

        dict[
            tuple[str, str],
            list[ScannerCandidate],
        ]
    """
    bridge = Mock(
        spec=ScannerValuationBridge,
    )

    grouped: dict[
        tuple[str, str],
        list[ScannerCandidate],
    ] = {}

    for candidate in candidates:
        key = (
            candidate.underlying,
            candidate.option_type,
        )

        grouped.setdefault(
            key,
            [],
        ).append(candidate)

    bridge.select_top_by_underlying_and_type.return_value = (
        grouped
    )

    def create_input(
        candidate: ScannerCandidate,
        **kwargs: object,
    ) -> SingleOptionValuationInput:
        """
        Delegate input creation to the REAL production bridge.

        This prevents the test double from inventing a second
        SingleOptionValuationInput contract.
        """
        return ScannerValuationBridge.create_valuation_input(
            candidate,
            **kwargs,
        )

    bridge.create_valuation_input.side_effect = create_input

    valuator = Mock(
        spec=SingleOptionValuator,
    )

    valuator.evaluate.side_effect = (
        lambda valuation_input: Mock(
            spec=SingleOptionValuationResult,
        )
    )

    batch_valuator = ScannerBatchValuator(
        bridge=bridge,
        valuator=valuator,
    )

    return (
        batch_valuator,
        bridge,
        valuator,
    )


# ============================================================
# 1. Normal Execution
# ============================================================


def test_batch_valuator_normal_execution() -> None:
    """
    Normal batch execution returns the existing
    BatchValuationResult contract.
    """
    candidate = make_candidate(
        "AU2608-C-100",
    )

    batch_valuator, bridge, valuator = make_valuator(
        candidates=(candidate,),
    )

    result = batch_valuator.scan_and_evaluate(
        [
            candidate.quote,
        ],
        top_n=1,
        parameters=make_parameters(),
    )

    assert isinstance(
        result,
        BatchValuationResult,
    )

    assert result.count == 1

    assert result.symbols == (
        "AU2608-C-100",
    )

    bridge.select_top_by_underlying_and_type.assert_called_once()

    valuator.evaluate.assert_called_once()


# ============================================================
# 2. Empty Candidate Result
# ============================================================


def test_batch_valuator_empty_candidate_selection_returns_empty_result() -> None:
    """
    An empty bridge selection must produce an empty
    BatchValuationResult.

    No valuation call may be fabricated.
    """
    batch_valuator, bridge, valuator = make_valuator(
        candidates=(),
    )

    result = batch_valuator.scan_and_evaluate(
        [],
        top_n=1,
        parameters=make_parameters(),
    )

    assert isinstance(
        result,
        BatchValuationResult,
    )

    assert result.items == ()
    assert result.results == ()
    assert result.count == 0
    assert result.symbols == ()

    bridge.select_top_by_underlying_and_type.assert_called_once()

    valuator.evaluate.assert_not_called()


# ============================================================
# 3. Single Candidate
# ============================================================


def test_batch_valuator_single_candidate() -> None:
    """
    One selected ScannerCandidate produces exactly one
    BatchValuationItem.
    """
    candidate = make_candidate(
        "AU2608-C-100",
    )

    batch_valuator, _, valuator = make_valuator(
        candidates=(candidate,),
    )

    result = batch_valuator.scan_and_evaluate(
        [
            candidate.quote,
        ],
        top_n=1,
        parameters=make_parameters(),
    )

    assert result.count == 1

    item = result.items[0]

    assert isinstance(
        item.candidate,
        ScannerCandidate,
    )

    assert item.candidate is candidate

    assert item.symbol == candidate.symbol

    valuator.evaluate.assert_called_once()


# ============================================================
# 4. Multiple Candidates
# ============================================================


def test_batch_valuator_multiple_candidates() -> None:
    """
    Multiple selected candidates produce one batch item and one
    SingleOptionValuator call per candidate.
    """
    candidates = (
        make_candidate(
            "AU2608-C-100",
            strike=100.0,
            volume=300,
        ),
        make_candidate(
            "AU2608-C-105",
            strike=105.0,
            volume=200,
        ),
        make_candidate(
            "AU2608-C-110",
            strike=110.0,
            volume=100,
        ),
    )

    batch_valuator, _, valuator = make_valuator(
        candidates=candidates,
    )

    result = batch_valuator.scan_and_evaluate(
        [
            candidate.quote
            for candidate in candidates
        ],
        top_n=3,
        parameters=make_parameters(),
    )

    assert result.count == 3

    assert result.symbols == (
        "AU2608-C-100",
        "AU2608-C-105",
        "AU2608-C-110",
    )

    assert valuator.evaluate.call_count == 3


# ============================================================
# 5. Bridge Selection Contract
# ============================================================


def test_batch_valuator_uses_existing_bridge_selection_contract() -> None:
    """
    ScannerBatchValuator must consume the existing grouped result
    contract of ScannerValuationBridge.

    The production bridge returns:

        dict[
            tuple[str, str],
            list[ScannerCandidate],
        ]
    """
    candidates = (
        make_candidate(
            "AU2608-C-100",
        ),
        make_candidate(
            "AU2608-P-100",
            option_type="PUT",
        ),
    )

    batch_valuator, bridge, _ = make_valuator(
        candidates=candidates,
    )

    result = batch_valuator.scan_and_evaluate(
        [
            candidate.quote
            for candidate in candidates
        ],
        top_n=1,
        parameters=make_parameters(),
    )

    assert result.count == 2

    grouped_result = (
        bridge.select_top_by_underlying_and_type
        .return_value
    )

    assert isinstance(
        grouped_result,
        dict,
    )

    assert all(
        isinstance(key, tuple)
        for key in grouped_result
    )

    assert all(
        isinstance(value, list)
        for value in grouped_result.values()
    )

    assert all(
        isinstance(candidate, ScannerCandidate)
        for candidates_in_group in grouped_result.values()
        for candidate in candidates_in_group
    )


# ============================================================
# 6. SingleOptionValuator Delegation
# ============================================================


def test_batch_valuator_delegates_to_single_option_valuator() -> None:
    """
    ScannerBatchValuator must delegate valuation to the existing
    SingleOptionValuator.

    The argument passed to evaluate() must be the existing
    SingleOptionValuationInput contract.
    """
    candidate = make_candidate(
        "AU2608-C-100",
    )

    batch_valuator, _, valuator = make_valuator(
        candidates=(candidate,),
    )

    batch_valuator.scan_and_evaluate(
        [
            candidate.quote,
        ],
        top_n=1,
        parameters=make_parameters(),
    )

    valuator.evaluate.assert_called_once()

    valuation_input = (
        valuator.evaluate.call_args.args[0]
    )

    assert isinstance(
        valuation_input,
        SingleOptionValuationInput,
    )

    assert valuation_input.symbol == (
        candidate.symbol
    )

    assert valuation_input.strike == (
        candidate.strike
    )

    assert valuation_input.current_option_price == (
        candidate.option_price
    )

    assert valuation_input.current_option_iv == (
        candidate.implied_volatility
    )


# ============================================================
# 7. Parameter Propagation
# ============================================================


def test_batch_valuator_passes_batch_parameters_into_valuation_input() -> None:
    """
    BatchValuationParameters must be resolved into the existing
    SingleOptionValuationInput contract.
    """
    candidate = make_candidate(
        "AU2608-C-100",
    )

    batch_valuator, _, valuator = make_valuator(
        candidates=(candidate,),
    )

    parameters = make_parameters()

    batch_valuator.scan_and_evaluate(
        [
            candidate.quote,
        ],
        top_n=1,
        parameters=parameters,
    )

    valuation_input = (
        valuator.evaluate.call_args.args[0]
    )

    assert valuation_input.current_futures_price == 100.0

    assert valuation_input.target_futures_price == 105.0

    assert valuation_input.remaining_days == 30

    assert valuation_input.risk_free_rate == 0.025

    assert valuation_input.direction == (
        OptionDirection.LONG
    )

    assert (
        valuation_input.reference_volatility.current
        == 0.20
    )

    assert (
        valuation_input.reference_volatility.target
        == 0.22
    )


# ============================================================
# 8. Candidate / Result Pairing
# ============================================================


def test_batch_valuator_preserves_candidate_result_pairing() -> None:
    """
    Each BatchValuationItem must preserve the association between
    the selected ScannerCandidate and the result returned by the
    SingleOptionValuator.
    """
    candidates = (
        make_candidate(
            "AU2608-C-100",
            strike=100.0,
        ),
        make_candidate(
            "AU2608-C-105",
            strike=105.0,
        ),
    )

    batch_valuator, _, valuator = make_valuator(
        candidates=candidates,
    )

    valuation_results = [
        Mock(
            spec=SingleOptionValuationResult,
        ),
        Mock(
            spec=SingleOptionValuationResult,
        ),
    ]

    valuator.evaluate.side_effect = valuation_results

    result = batch_valuator.scan_and_evaluate(
        [
            candidate.quote
            for candidate in candidates
        ],
        top_n=2,
        parameters=make_parameters(),
    )

    assert result.count == 2

    assert result.items[0].candidate is candidates[0]
    assert result.items[1].candidate is candidates[1]

    assert result.items[0].result is (
        valuation_results[0]
    )

    assert result.items[1].result is (
        valuation_results[1]
    )


# ============================================================
# 9. Result Order Preservation
# ============================================================


def test_batch_valuator_preserves_selected_candidate_order() -> None:
    """
    ScannerBatchValuator must preserve the order returned by the
    bridge grouping contract when flattening selected candidates.

    No additional sorting is introduced by the batch layer.
    """
    first = make_candidate(
        "AU2608-C-110",
        strike=110.0,
    )

    second = make_candidate(
        "AU2608-C-100",
        strike=100.0,
    )

    third = make_candidate(
        "AU2608-P-105",
        option_type="PUT",
        strike=105.0,
    )

    batch_valuator, bridge, _ = make_valuator(
        candidates=(
            first,
            second,
            third,
        ),
    )

    # Explicitly define the exact grouped order returned by the
    # bridge. This is the contract consumed by ScannerBatchValuator.
    bridge.select_top_by_underlying_and_type.return_value = {
        ("AU2608", "CALL"): [
            first,
            second,
        ],
        ("AU2608", "PUT"): [
            third,
        ],
    }

    result = batch_valuator.scan_and_evaluate(
        [
            first.quote,
            second.quote,
            third.quote,
        ],
        top_n=2,
        parameters=make_parameters(),
    )

    assert result.symbols == (
        "AU2608-C-110",
        "AU2608-C-100",
        "AU2608-P-105",
    )


# ============================================================
# 10. Direct Candidate Evaluation Uses Existing Input Contract
# ============================================================


def test_evaluate_candidate_uses_existing_single_option_input() -> None:
    """
    The direct evaluate_candidate() path must create the existing
    SingleOptionValuationInput before delegating to the
    SingleOptionValuator.
    """
    candidate = make_candidate(
        "AU2608-C-100",
    )

    batch_valuator, _, valuator = make_valuator(
        candidates=(candidate,),
    )

    parameters = make_parameters()

    item = batch_valuator.evaluate_candidate(
        candidate,
        parameters,
    )

    assert item.candidate is candidate

    valuator.evaluate.assert_called_once()

    valuation_input = (
        valuator.evaluate.call_args.args[0]
    )

    assert isinstance(
        valuation_input,
        SingleOptionValuationInput,
    )

    assert valuation_input.symbol == (
        candidate.symbol
    )


# ============================================================
# 11. Batch Result Contract
# ============================================================


def test_batch_valuator_returns_existing_result_contract() -> None:
    """
    The public batch valuation result must remain
    BatchValuationResult and expose the existing result properties.
    """
    candidate = make_candidate(
        "AU2608-C-100",
    )

    batch_valuator, _, _ = make_valuator(
        candidates=(candidate,),
    )

    result = batch_valuator.scan_and_evaluate(
        [
            candidate.quote,
        ],
        top_n=1,
        parameters=make_parameters(),
    )

    assert isinstance(
        result,
        BatchValuationResult,
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
        result.symbols,
        tuple,
    )

    assert result.count == len(
        result.items
    )

    assert result.count == len(
        result.results
    )

    assert result.count == len(
        result.symbols
    )