"""
Commodity Option Valuator Pro
=============================

Scanner Batch Workflow Coordinator.

Commit 0033 - Phase 1
---------------------

Coordinates the existing scanner batch valuation and
comprehensive evaluation layers without introducing a second
valuation model or changing existing production contracts.
"""

from __future__ import annotations

from typing import Iterable

from core.scanner_batch_valuation import (
    BatchValuationParameters,
    BatchValuationResult,
    ScannerBatchValuator,
)
from core.scanner_comprehensive_evaluation import (
    ScannerComprehensiveEvaluator,
    ScannerEvaluationResult,
)
from data.option_chain import OptionQuote


class ScannerBatchWorkflow:
    """Orchestration boundary for the existing scanner services."""

    def __init__(
        self,
        batch_valuator: ScannerBatchValuator | None = None,
        comprehensive_evaluator: ScannerComprehensiveEvaluator | None = None,
    ) -> None:
        self.batch_valuator = (
            batch_valuator if batch_valuator is not None
            else ScannerBatchValuator()
        )
        self.comprehensive_evaluator = (
            comprehensive_evaluator
            if comprehensive_evaluator is not None
            else ScannerComprehensiveEvaluator()
        )

    def scan_and_evaluate(
        self,
        quotes: Iterable[OptionQuote],
        *,
        top_n: int,
        parameters: BatchValuationParameters,
    ) -> BatchValuationResult:
        """Delegate scanner selection and batch valuation."""
        return self.batch_valuator.scan_and_evaluate(
            quotes,
            top_n=top_n,
            parameters=parameters,
        )

    def evaluate_comprehensively(
        self,
        batch_result: BatchValuationResult,
    ) -> ScannerEvaluationResult:
        """Delegate comprehensive evaluation."""
        return self.comprehensive_evaluator.evaluate(batch_result)

    def scan_and_evaluate_comprehensively(
        self,
        quotes: Iterable[OptionQuote],
        *,
        top_n: int,
        parameters: BatchValuationParameters,
    ) -> ScannerEvaluationResult:
        """Execute the complete scanner valuation/evaluation flow."""
        batch_result = self.scan_and_evaluate(
            quotes,
            top_n=top_n,
            parameters=parameters,
        )
        return self.evaluate_comprehensively(batch_result)


__all__ = ["ScannerBatchWorkflow"]
