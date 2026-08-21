"""
Commodity Option Valuator Pro
=============================

Scanner Comprehensive Evaluation.

Commit 0032
-----------

Provides the final business-output layer for scanner batch
valuation.

Architecture
------------

OptionQuote
    ↓
ScannerBatchValuator
    ↓
BatchValuationResult
    ↓
ScannerComprehensiveEvaluator
    ↓
ScannerEvaluationResult
    ↓
Sorting / Filtering / UI

Responsibilities
----------------

This module:

1. Consumes existing BatchValuationResult.
2. Reuses existing ComprehensiveEvaluator.
3. Keeps scanner contract information together with
   comprehensive evaluation information.
4. Provides deterministic sorting and filtering.
5. Provides summary statistics for Scanner UI.

This module does NOT modify:

- OptionQuote
- ScannerValuationBridge
- ScannerBatchValuator
- BatchValuationParameters
- BatchValuationItem
- BatchValuationResult
- SingleOptionValuator
- SingleOptionValuationResult
- ComprehensiveEvaluator
- RecommendationEngine
- RecommendationWorkflow
- RiskAnalyzer
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.comprehensive_evaluation import (
    ComprehensiveDecision,
    ComprehensiveEvaluationResult,
    ComprehensiveEvaluator,
)
from core.scanner_batch_valuation import (
    BatchValuationItem,
    BatchValuationResult,
)


# ==========================================================
# Scanner Evaluation Item
# ==========================================================


@dataclass(frozen=True)
class ScannerEvaluationItem:
    """
    One fully evaluated scanner contract.

    The object intentionally keeps both:

    1. scanner identity information
    2. comprehensive evaluation information

    This prevents the UI from having to join data from
    multiple result objects.
    """

    batch_item: BatchValuationItem

    evaluation: ComprehensiveEvaluationResult

    @property
    def symbol(self) -> str:
        """Return option symbol."""

        return self.batch_item.symbol

    @property
    def underlying(self) -> str:
        """Return underlying futures contract."""

        return self.batch_item.underlying

    @property
    def option_type(self) -> str:
        """Return CALL / PUT."""

        return self.batch_item.option_type

    @property
    def strike(self) -> float:
        """Return option strike."""

        return float(
            self.batch_item.candidate.strike
        )

    @property
    def volume(self) -> int:
        """Return trading volume."""

        return int(
            self.batch_item.volume
        )

    @property
    def open_interest(self) -> int:
        """Return open interest."""

        return int(
            self.batch_item.candidate.open_interest
        )

    @property
    def option_price(self) -> float:
        """Return current market option price."""

        return float(
            self.batch_item.candidate.option_price
        )

    @property
    def implied_volatility(self) -> float | None:
        """Return current market implied volatility."""

        value = (
            self.batch_item.candidate.implied_volatility
        )

        if value is None:
            return None

        return float(value)

    @property
    def decision(self) -> ComprehensiveDecision:
        """Return comprehensive business decision."""

        return self.evaluation.decision

    @property
    def score(self) -> float:
        """Return comprehensive evaluation score."""

        return float(
            self.evaluation.score
        )

    @property
    def risk_score(self) -> float:
        """Return risk score."""

        return float(
            self.evaluation.risk_score
        )

    @property
    def risk_level(self):
        """Return risk level."""

        return self.evaluation.risk_level

    @property
    def reason_text(self) -> str:
        """Return human-readable evaluation reasons."""

        return self.evaluation.reason_text

    @property
    def reason_messages(self) -> tuple[str, ...]:
        """Return evaluation reason messages."""

        return self.evaluation.reason_messages

    @property
    def valuation_result(self):
        """Return underlying single-option valuation result."""

        return self.batch_item.result

    def to_dict(self) -> dict[str, object]:
        """
        Export the complete scanner evaluation item.

        The dictionary is intended for UI/report/export layers.
        """

        valuation = self.batch_item.result.to_dict()
        evaluation = self.evaluation.to_dict()

        return {
            "symbol": self.symbol,
            "underlying": self.underlying,
            "option_type": self.option_type,
            "strike": self.strike,
            "volume": self.volume,
            "open_interest": self.open_interest,
            "option_price": self.option_price,
            "implied_volatility": (
                self.implied_volatility
            ),
            "decision": self.decision.value,
            "score": self.score,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "reason_text": self.reason_text,
            "reason_messages": list(
                self.reason_messages
            ),
            "valuation": valuation,
            "evaluation": evaluation,
        }


# ==========================================================
# Scanner Evaluation Result
# ==========================================================


@dataclass(frozen=True)
class ScannerEvaluationResult:
    """
    Complete comprehensive evaluation result for scanner
    batch valuation.
    """

    items: tuple[ScannerEvaluationItem, ...]

    @property
    def count(self) -> int:
        """Return total evaluated contract count."""

        return len(self.items)

    @property
    def symbols(self) -> tuple[str, ...]:
        """Return evaluated option symbols."""

        return tuple(
            item.symbol
            for item in self.items
        )

    @property
    def recommendations(self) -> tuple[
        ScannerEvaluationItem,
        ...
    ]:
        """
        Return RECOMMEND items.
        """

        return tuple(
            item
            for item in self.items
            if item.decision
            == ComprehensiveDecision.RECOMMEND
        )

    @property
    def watches(self) -> tuple[
        ScannerEvaluationItem,
        ...
    ]:
        """
        Return WATCH items.
        """

        return tuple(
            item
            for item in self.items
            if item.decision
            == ComprehensiveDecision.WATCH
        )

    @property
    def cautions(self) -> tuple[
        ScannerEvaluationItem,
        ...
    ]:
        """
        Return CAUTION items.
        """

        return tuple(
            item
            for item in self.items
            if item.decision
            == ComprehensiveDecision.CAUTION
        )

    @property
    def recommendation_count(self) -> int:
        """Return number of recommended contracts."""

        return len(
            self.recommendations
        )

    @property
    def watch_count(self) -> int:
        """Return number of watched contracts."""

        return len(
            self.watches
        )

    @property
    def caution_count(self) -> int:
        """Return number of caution contracts."""

        return len(
            self.cautions
        )

    @property
    def best(self) -> ScannerEvaluationItem | None:
        """
        Return the highest-scoring evaluated contract.

        Returns None when no result exists.
        """

        if not self.items:
            return None

        return max(
            self.items,
            key=lambda item: item.score,
        )

    def by_underlying(
        self,
    ) -> dict[
        str,
        list[ScannerEvaluationItem],
    ]:
        """
        Group evaluation results by underlying.
        """

        grouped: dict[
            str,
            list[ScannerEvaluationItem],
        ] = {}

        for item in self.items:
            grouped.setdefault(
                item.underlying,
                [],
            ).append(
                item
            )

        return grouped

    def filter_decision(
        self,
        decision: ComprehensiveDecision,
    ) -> tuple[
        ScannerEvaluationItem,
        ...
    ]:
        """
        Return items matching one business decision.
        """

        return tuple(
            item
            for item in self.items
            if item.decision == decision
        )

    def filter_score(
        self,
        *,
        minimum_score: float | None = None,
        maximum_score: float | None = None,
    ) -> tuple[
        ScannerEvaluationItem,
        ...
    ]:
        """
        Filter results by comprehensive score.

        Both boundaries are optional.
        """

        if minimum_score is not None:
            minimum_score = float(
                minimum_score
            )

        if maximum_score is not None:
            maximum_score = float(
                maximum_score
            )

        if (
            minimum_score is not None
            and maximum_score is not None
            and minimum_score > maximum_score
        ):
            raise ValueError(
                "minimum_score cannot be greater "
                "than maximum_score."
            )

        result: list[
            ScannerEvaluationItem
        ] = []

        for item in self.items:

            if (
                minimum_score is not None
                and item.score < minimum_score
            ):
                continue

            if (
                maximum_score is not None
                and item.score > maximum_score
            ):
                continue

            result.append(
                item
            )

        return tuple(result)

    def sort_by_score(
        self,
        *,
        descending: bool = True,
    ) -> "ScannerEvaluationResult":
        """
        Return a new result sorted by comprehensive score.

        The original result remains unchanged.
        """

        sorted_items = tuple(
            sorted(
                self.items,
                key=lambda item: item.score,
                reverse=descending,
            )
        )

        return ScannerEvaluationResult(
            items=sorted_items
        )

    def sort_by_volume(
        self,
        *,
        descending: bool = True,
    ) -> "ScannerEvaluationResult":
        """
        Return a new result sorted by trading volume.

        The original result remains unchanged.
        """

        sorted_items = tuple(
            sorted(
                self.items,
                key=lambda item: item.volume,
                reverse=descending,
            )
        )

        return ScannerEvaluationResult(
            items=sorted_items
        )

    def sort_by_risk(
        self,
        *,
        descending: bool = False,
    ) -> "ScannerEvaluationResult":
        """
        Return a new result sorted by risk score.

        By default, the lowest risk appears first.
        """

        sorted_items = tuple(
            sorted(
                self.items,
                key=lambda item: item.risk_score,
                reverse=descending,
            )
        )

        return ScannerEvaluationResult(
            items=sorted_items
        )

    def to_dict(self) -> list[dict[str, object]]:
        """
        Export all scanner evaluation items.
        """

        return [
            item.to_dict()
            for item in self.items
        ]


# ==========================================================
# Scanner Comprehensive Evaluator
# ==========================================================


class ScannerComprehensiveEvaluator:
    """
    Apply the existing ComprehensiveEvaluator to every
    result in a BatchValuationResult.

    This class is intentionally thin.

    It does not implement a second scoring model.

    It simply coordinates:

        BatchValuationResult
                    ↓
        ComprehensiveEvaluator
                    ↓
        ScannerEvaluationResult
    """

    def __init__(
        self,
        evaluator: ComprehensiveEvaluator | None = None,
    ) -> None:
        """
        Initialize scanner comprehensive evaluator.
        """

        self.evaluator = (
            evaluator
            if evaluator is not None
            else ComprehensiveEvaluator()
        )

    def evaluate_item(
        self,
        item: BatchValuationItem,
    ) -> ScannerEvaluationItem:
        """
        Evaluate one batch valuation item.
        """

        if not isinstance(
            item,
            BatchValuationItem,
        ):
            raise TypeError(
                "item must be a BatchValuationItem"
            )

        evaluation = self.evaluator.evaluate(
            item.result
        )

        return ScannerEvaluationItem(
            batch_item=item,
            evaluation=evaluation,
        )

    def evaluate_items(
        self,
        items: Iterable[BatchValuationItem],
    ) -> ScannerEvaluationResult:
        """
        Evaluate an iterable of batch valuation items.
        """

        evaluated = [
            self.evaluate_item(item)
            for item in items
        ]

        return ScannerEvaluationResult(
            items=tuple(
                evaluated
            )
        )

    def evaluate(
        self,
        batch_result: BatchValuationResult,
    ) -> ScannerEvaluationResult:
        """
        Evaluate a complete BatchValuationResult.
        """

        if not isinstance(
            batch_result,
            BatchValuationResult,
        ):
            raise TypeError(
                "batch_result must be a BatchValuationResult"
            )

        return self.evaluate_items(
            batch_result.items
        )

    def evaluate_and_sort(
        self,
        batch_result: BatchValuationResult,
        *,
        descending: bool = True,
    ) -> ScannerEvaluationResult:
        """
        Evaluate a batch result and return it sorted by score.
        """

        return self.evaluate(
            batch_result
        ).sort_by_score(
            descending=descending
        )


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "ScannerEvaluationItem",
    "ScannerEvaluationResult",
    "ScannerComprehensiveEvaluator",
]