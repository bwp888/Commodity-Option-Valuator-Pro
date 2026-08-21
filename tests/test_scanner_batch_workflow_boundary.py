"""
Commodity Option Valuator Pro
=============================

Scanner Batch Workflow Boundary Tests.

Commit 0033 - Phase 2
---------------------

Purpose
-------
Validate the result boundaries and exception boundaries of
ScannerBatchWorkflow without changing the existing production
valuation contracts.

Covered boundaries
------------------
1. Normal execution
2. No candidate contracts
3. Insufficient parameter coverage
4. Invalid input type
5. Result order preservation
6. Existing valuation-contract delegation

Important
---------
This test module intentionally does not modify or redesign:

- ui/scanner.py
- ScannerBatchValuator
- SingleOptionValuator
- ScannerComprehensiveEvaluator
- ScannerBatchWorkflow production implementation

The Workflow remains an orchestration boundary only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pytest

from core.scanner_batch_valuation import (
    BatchValuationItem,
    BatchValuationParameters,
    BatchValuationResult,
)
from core.scanner_batch_workflow import ScannerBatchWorkflow
from core.scanner_comprehensive_evaluation import (
    ScannerEvaluationResult,
)
from data.option_chain import OptionQuote
from models.option import OptionDirection


# ==========================================================
# Test Data Helpers
# ==========================================================


def make_quote(
    *,
    symbol: str = "AU2608-C-900",
    underlying: str = "AU2608",
    option_type: str = "CALL",
    volume: int = 100,
) -> OptionQuote:
    """
    Build a valid OptionQuote for Workflow boundary tests.

    The quote structure follows the existing OptionQuote contract
    already used by Commit 0033 Phase 1 tests.
    """
    return OptionQuote(
        symbol=symbol,
        underlying=underlying,
        option_type=option_type,
        strike=900.0,
        last_price=35.0,
        bid_price=34.5,
        ask_price=35.5,
        volume=volume,
        open_interest=500,
    )


def make_parameters() -> BatchValuationParameters:
    """
    Build a complete BatchValuationParameters object.

    The parameter contract is intentionally reused rather than
    reconstructed inside the Workflow test.
    """
    from core.single_option_valuation import (
        ReferenceVolatilityScenario,
    )

    return BatchValuationParameters(
        current_futures_prices={
            "AU2608": 900.0,
        },
        target_futures_prices={
            "AU2608": 1000.0,
        },
        remaining_days={
            "AU2608": 30,
        },
        reference_volatility={
            "AU2608": ReferenceVolatilityScenario(
                current=0.267,
                target=0.2955,
            ),
        },
        risk_free_rate=0.025,
        direction=OptionDirection.LONG,
    )


def make_candidate(
    symbol: str,
    underlying: str = "AU2608",
    option_type: str = "CALL",
    volume: int = 100,
) -> object:
    """
    Create a lightweight candidate double.

    BatchValuationItem only requires the ScannerCandidate-compatible
    attributes exposed by its public properties.
    """
    return type(
        "CandidateDouble",
        (),
        {
            "symbol": symbol,
            "underlying": underlying,
            "option_type": option_type,
            "volume": volume,
        },
    )()


def make_batch_result(
    symbols: tuple[str, ...] = (
        "AU2608-C-900",
    ),
) -> BatchValuationResult:
    """
    Build a BatchValuationResult whose item order is deterministic.

    The actual valuation result is deliberately represented by an
    object double because this test suite is testing the Workflow
    orchestration boundary, not SingleOptionValuator.
    """
    items = tuple(
        BatchValuationItem(
            candidate=make_candidate(symbol),
            result=object(),  # type: ignore[arg-type]
        )
        for symbol in symbols
    )

    return BatchValuationResult(
        items=items,
    )


def make_empty_batch_result() -> BatchValuationResult:
    """Build the existing empty BatchValuationResult contract."""
    return BatchValuationResult(
        items=(),
    )


def make_evaluation_result() -> ScannerEvaluationResult:
    """Build an empty comprehensive evaluation result."""
    return ScannerEvaluationResult(
        items=(),
    )


# ==========================================================
# Dependency Doubles
# ==========================================================


@dataclass
class FakeBatchValuator:
    """
    Test double for ScannerBatchValuator.

    It records the Workflow call without reimplementing any
    valuation logic.
    """

    result: BatchValuationResult
    calls: int = 0
    received_quotes: tuple[OptionQuote, ...] | None = None
    received_top_n: int | None = None
    received_parameters: object | None = None

    def scan_and_evaluate(
        self,
        quotes: Iterable[OptionQuote],
        *,
        top_n: int,
        parameters: BatchValuationParameters,
    ) -> BatchValuationResult:
        """Record and return the preconfigured batch result."""
        self.calls += 1
        self.received_quotes = tuple(quotes)
        self.received_top_n = top_n
        self.received_parameters = parameters

        return self.result


@dataclass
class RaisingBatchValuator:
    """
    Test double used to verify Workflow exception propagation.

    The Workflow must not reinterpret or swallow an exception
    originating from the existing batch valuation contract.
    """

    exception: Exception
    calls: int = 0

    def scan_and_evaluate(
        self,
        quotes: Iterable[OptionQuote],
        *,
        top_n: int,
        parameters: BatchValuationParameters,
    ) -> BatchValuationResult:
        """Raise the configured production-layer exception."""
        self.calls += 1
        raise self.exception


@dataclass
class FakeComprehensiveEvaluator:
    """
    Test double for ScannerComprehensiveEvaluator.
    """

    result: ScannerEvaluationResult
    calls: int = 0
    received: BatchValuationResult | None = None

    def evaluate(
        self,
        batch_result: BatchValuationResult,
    ) -> ScannerEvaluationResult:
        """Record the exact BatchValuationResult received."""
        self.calls += 1
        self.received = batch_result

        return self.result


# ==========================================================
# 1. Normal Execution
# ==========================================================


def test_workflow_normal_execution() -> None:
    """
    Normal Workflow execution must delegate to the existing
    ScannerBatchValuator and return its result unchanged.
    """
    batch_result = make_batch_result()

    batch = FakeBatchValuator(
        result=batch_result,
    )

    workflow = ScannerBatchWorkflow(
        batch_valuator=batch,
    )

    quote = make_quote()
    parameters = make_parameters()

    result = workflow.scan_and_evaluate(
        [quote],
        top_n=2,
        parameters=parameters,
    )

    assert result is batch_result

    assert batch.calls == 1
    assert batch.received_quotes == (quote,)
    assert batch.received_top_n == 2
    assert batch.received_parameters is parameters


# ==========================================================
# 2. No Candidate Contracts
# ==========================================================


def test_workflow_no_candidate_contracts() -> None:
    """
    When the existing batch valuation layer returns an empty
    BatchValuationResult, Workflow must preserve that result.

    Workflow must not:
    - fabricate a candidate,
    - fabricate a valuation result,
    - invoke comprehensive evaluation implicitly.
    """
    empty_result = make_empty_batch_result()

    batch = FakeBatchValuator(
        result=empty_result,
    )

    evaluator = FakeComprehensiveEvaluator(
        result=make_evaluation_result(),
    )

    workflow = ScannerBatchWorkflow(
        batch_valuator=batch,
        comprehensive_evaluator=evaluator,
    )

    result = workflow.scan_and_evaluate(
        [],
        top_n=2,
        parameters=make_parameters(),
    )

    assert result is empty_result
    assert result.count == 0
    assert result.items == ()
    assert result.symbols == ()

    assert batch.calls == 1

    # scan_and_evaluate() must not implicitly call the
    # comprehensive evaluation layer.
    assert evaluator.calls == 0


# ==========================================================
# 3. Insufficient Parameter Coverage
# ==========================================================


def test_workflow_propagates_insufficient_parameter_coverage() -> None:
    """
    Parameter coverage belongs to the existing batch valuation
    layer / parameter resolver.

    Workflow must propagate the existing ValueError instead of:
    - inventing defaults,
    - silently skipping the candidate,
    - modifying the parameters,
    - recalculating missing data.
    """
    expected_error = ValueError(
        "current_futures_prices is missing underlying: AU2608"
    )

    batch = RaisingBatchValuator(
        exception=expected_error,
    )

    workflow = ScannerBatchWorkflow(
        batch_valuator=batch,
    )

    with pytest.raises(
        ValueError,
        match="current_futures_prices is missing underlying: AU2608",
    ):
        workflow.scan_and_evaluate(
            [make_quote()],
            top_n=2,
            parameters=make_parameters(),
        )

    assert batch.calls == 1


def test_workflow_does_not_fill_missing_parameters() -> None:
    """
    Workflow must pass the original parameter object through.

    This protects the boundary against hidden parameter completion
    logic being introduced into ScannerBatchWorkflow.
    """
    batch = FakeBatchValuator(
        result=make_batch_result(),
    )

    workflow = ScannerBatchWorkflow(
        batch_valuator=batch,
    )

    parameters = make_parameters()

    workflow.scan_and_evaluate(
        [make_quote()],
        top_n=2,
        parameters=parameters,
    )

    assert batch.received_parameters is parameters


# ==========================================================
# 4. Invalid Input Type
# ==========================================================


def test_workflow_does_not_reinterpret_invalid_quotes_input() -> None:
    """
    Invalid quotes input must be passed to the existing batch
    valuation contract rather than being silently converted.

    The fake deliberately rejects the wrong input type so that
    this test verifies Workflow does not add an alternative
    interpretation layer.
    """

    @dataclass
    class StrictBatchValuator:
        calls: int = 0

        def scan_and_evaluate(
            self,
            quotes: Iterable[OptionQuote],
            *,
            top_n: int,
            parameters: BatchValuationParameters,
        ) -> BatchValuationResult:
            self.calls += 1

            if isinstance(quotes, (str, bytes)):
                raise TypeError(
                    "quotes must be an iterable of OptionQuote"
                )

            return make_empty_batch_result()

    batch = StrictBatchValuator()

    workflow = ScannerBatchWorkflow(
        batch_valuator=batch,
    )

    with pytest.raises(
        TypeError,
        match="quotes must be an iterable of OptionQuote",
    ):
        workflow.scan_and_evaluate(
            "invalid-quotes-input",  # type: ignore[arg-type]
            top_n=2,
            parameters=make_parameters(),
        )

    assert batch.calls == 1


def test_workflow_does_not_reinterpret_invalid_parameter_type() -> None:
    """
    Invalid parameter objects must not be converted by Workflow.

    Existing production validation remains responsible for the
    BatchValuationParameters contract.
    """
    batch = RaisingBatchValuator(
        exception=TypeError(
            "parameters must be BatchValuationParameters"
        ),
    )

    workflow = ScannerBatchWorkflow(
        batch_valuator=batch,
    )

    with pytest.raises(
        TypeError,
        match="parameters must be BatchValuationParameters",
    ):
        workflow.scan_and_evaluate(
            [make_quote()],
            top_n=2,
            parameters=object(),  # type: ignore[arg-type]
        )

    assert batch.calls == 1


# ==========================================================
# 5. Result Order Preservation
# ==========================================================


def test_workflow_preserves_batch_result_order() -> None:
    """
    Workflow must preserve the order produced by the existing
    ScannerBatchValuator.

    BatchValuationResult explicitly defines its items as preserving
    scanner-selected contract order. Workflow must not sort, reverse,
    regroup, or otherwise reorder them.
    """
    expected_symbols = (
        "AU2608-C-900",
        "AU2608-C-910",
        "AU2608-C-920",
    )

    batch_result = make_batch_result(
        symbols=expected_symbols,
    )

    batch = FakeBatchValuator(
        result=batch_result,
    )

    workflow = ScannerBatchWorkflow(
        batch_valuator=batch,
    )

    result = workflow.scan_and_evaluate(
        [
            make_quote(
                symbol="AU2608-C-900",
            ),
            make_quote(
                symbol="AU2608-C-910",
            ),
            make_quote(
                symbol="AU2608-C-920",
            ),
        ],
        top_n=3,
        parameters=make_parameters(),
    )

    assert result is batch_result
    assert result.symbols == expected_symbols


# ==========================================================
# 6. Existing Valuation Contract Protection
# ==========================================================


def test_workflow_delegates_to_existing_batch_valuator() -> None:
    """
    Workflow must use the existing ScannerBatchValuator contract.

    This test intentionally injects a batch service and verifies that
    Workflow delegates to it rather than performing valuation itself.
    """
    batch_result = make_batch_result()

    batch = FakeBatchValuator(
        result=batch_result,
    )

    workflow = ScannerBatchWorkflow(
        batch_valuator=batch,
    )

    result = workflow.scan_and_evaluate(
        [make_quote()],
        top_n=2,
        parameters=make_parameters(),
    )

    assert batch.calls == 1
    assert result is batch_result


def test_complete_workflow_uses_existing_valuation_contracts_in_order() -> None:
    """
    The complete Workflow must execute:

        ScannerBatchValuator
                ↓
        BatchValuationResult
                ↓
        ScannerComprehensiveEvaluator

    The Workflow must not replace either existing service.
    """
    batch_result = make_batch_result()
    evaluation_result = make_evaluation_result()

    batch = FakeBatchValuator(
        result=batch_result,
    )

    evaluator = FakeComprehensiveEvaluator(
        result=evaluation_result,
    )

    workflow = ScannerBatchWorkflow(
        batch_valuator=batch,
        comprehensive_evaluator=evaluator,
    )

    result = workflow.scan_and_evaluate_comprehensively(
        [make_quote()],
        top_n=2,
        parameters=make_parameters(),
    )

    assert result is evaluation_result

    assert batch.calls == 1
    assert evaluator.calls == 1

    # Comprehensive evaluation must receive exactly the result
    # returned by the existing batch valuation layer.
    assert evaluator.received is batch_result


def test_workflow_does_not_bypass_comprehensive_evaluator() -> None:
    """
    Comprehensive evaluation must remain delegated to the existing
    ScannerComprehensiveEvaluator.
    """
    batch_result = make_batch_result()
    evaluation_result = make_evaluation_result()

    evaluator = FakeComprehensiveEvaluator(
        result=evaluation_result,
    )

    workflow = ScannerBatchWorkflow(
        batch_valuator=FakeBatchValuator(
            result=batch_result,
        ),
        comprehensive_evaluator=evaluator,
    )

    result = workflow.evaluate_comprehensively(
        batch_result,
    )

    assert result is evaluation_result
    assert evaluator.calls == 1
    assert evaluator.received is batch_result


# ==========================================================
# Public Contract Stability
# ==========================================================


def test_workflow_public_export_remains_stable() -> None:
    """
    Protect the existing public module export.
    """
    from core.scanner_batch_workflow import __all__

    assert __all__ == [
        "ScannerBatchWorkflow",
    ]