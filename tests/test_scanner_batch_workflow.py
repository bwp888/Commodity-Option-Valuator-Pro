"""
Commodity Option Valuator Pro
=============================

Scanner Batch Workflow Tests.

Commit 0033 - Phase 1
---------------------
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
    ScannerComprehensiveEvaluator,
    ScannerEvaluationResult,
)
from data.option_chain import OptionQuote
from models.option import OptionDirection


def make_quote() -> OptionQuote:
    return OptionQuote(
        symbol="AU2608-C-900",
        underlying="AU2608",
        option_type="CALL",
        strike=900.0,
        last_price=35.0,
        bid_price=34.5,
        ask_price=35.5,
        volume=100,
        open_interest=500,
    )


def make_parameters() -> BatchValuationParameters:
    from core.single_option_valuation import ReferenceVolatilityScenario

    return BatchValuationParameters(
        current_futures_prices={"AU2608": 900.0},
        target_futures_prices={"AU2608": 1000.0},
        remaining_days={"AU2608": 30},
        reference_volatility={
            "AU2608": ReferenceVolatilityScenario(
                current=0.267,
                target=0.2955,
            )
        },
        risk_free_rate=0.025,
        direction=OptionDirection.LONG,
    )


def make_batch_result() -> BatchValuationResult:
    candidate = type(
        "CandidateDouble",
        (),
        {
            "symbol": "AU2608-C-900",
            "underlying": "AU2608",
            "option_type": "CALL",
            "volume": 100,
        },
    )()
    item = BatchValuationItem(
        candidate=candidate,  # type: ignore[arg-type]
        result=object(),  # type: ignore[arg-type]
    )
    return BatchValuationResult(items=(item,))


def make_evaluation_result() -> ScannerEvaluationResult:
    return ScannerEvaluationResult(items=())


@dataclass
class FakeBatchValuator:
    result: BatchValuationResult
    calls: int = 0

    def scan_and_evaluate(
        self,
        quotes: Iterable[OptionQuote],
        *,
        top_n: int,
        parameters: BatchValuationParameters,
    ) -> BatchValuationResult:
        self.calls += 1
        assert top_n == 2
        assert isinstance(parameters, BatchValuationParameters)
        assert tuple(quotes)
        return self.result


@dataclass
class FakeComprehensiveEvaluator:
    result: ScannerEvaluationResult
    calls: int = 0
    received: BatchValuationResult | None = None

    def evaluate(
        self,
        batch_result: BatchValuationResult,
    ) -> ScannerEvaluationResult:
        self.calls += 1
        self.received = batch_result
        return self.result


def test_workflow_can_be_created() -> None:
    assert isinstance(ScannerBatchWorkflow(), ScannerBatchWorkflow)


def test_default_dependencies_are_existing_services() -> None:
    workflow = ScannerBatchWorkflow()
    assert isinstance(workflow.batch_valuator, __import__(
        "core.scanner_batch_valuation",
        fromlist=["ScannerBatchValuator"],
    ).ScannerBatchValuator)
    assert isinstance(
        workflow.comprehensive_evaluator,
        ScannerComprehensiveEvaluator,
    )


def test_dependencies_can_be_injected() -> None:
    batch = FakeBatchValuator(make_batch_result())
    evaluator = FakeComprehensiveEvaluator(make_evaluation_result())
    workflow = ScannerBatchWorkflow(
        batch_valuator=batch,
        comprehensive_evaluator=evaluator,
    )
    assert workflow.batch_valuator is batch
    assert workflow.comprehensive_evaluator is evaluator


def test_scan_and_evaluate_delegates_to_batch_valuator() -> None:
    batch_result = make_batch_result()
    batch = FakeBatchValuator(batch_result)
    workflow = ScannerBatchWorkflow(batch_valuator=batch)

    result = workflow.scan_and_evaluate(
        [make_quote()],
        top_n=2,
        parameters=make_parameters(),
    )

    assert result is batch_result
    assert batch.calls == 1


def test_scan_does_not_apply_comprehensive_evaluation() -> None:
    batch = FakeBatchValuator(make_batch_result())
    evaluator = FakeComprehensiveEvaluator(make_evaluation_result())
    workflow = ScannerBatchWorkflow(
        batch_valuator=batch,
        comprehensive_evaluator=evaluator,
    )

    workflow.scan_and_evaluate(
        [make_quote()],
        top_n=2,
        parameters=make_parameters(),
    )

    assert evaluator.calls == 0


def test_evaluate_comprehensively_delegates() -> None:
    batch_result = make_batch_result()
    evaluation_result = make_evaluation_result()
    evaluator = FakeComprehensiveEvaluator(evaluation_result)
    workflow = ScannerBatchWorkflow(
        comprehensive_evaluator=evaluator
    )

    result = workflow.evaluate_comprehensively(batch_result)

    assert result is evaluation_result
    assert evaluator.calls == 1
    assert evaluator.received is batch_result


def test_complete_workflow_runs_in_order() -> None:
    batch_result = make_batch_result()
    evaluation_result = make_evaluation_result()
    batch = FakeBatchValuator(batch_result)
    evaluator = FakeComprehensiveEvaluator(evaluation_result)
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
    assert evaluator.received is batch_result


def test_complete_workflow_preserves_result_identity() -> None:
    batch_result = make_batch_result()
    evaluation_result = make_evaluation_result()
    batch = FakeBatchValuator(batch_result)
    evaluator = FakeComprehensiveEvaluator(evaluation_result)
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
    assert evaluator.received is batch_result


def test_invalid_parameter_type_is_not_reinterpreted_by_workflow() -> None:
    batch = FakeBatchValuator(make_batch_result())
    workflow = ScannerBatchWorkflow(batch_valuator=batch)

    with pytest.raises(AssertionError):
        workflow.scan_and_evaluate(
            [make_quote()],
            top_n=2,
            parameters=object(),  # type: ignore[arg-type]
        )


def test_public_export_is_stable() -> None:
    from core.scanner_batch_workflow import __all__

    assert __all__ == ["ScannerBatchWorkflow"]
