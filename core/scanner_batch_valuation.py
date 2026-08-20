"""
Commodity Option Valuator Pro
=============================

Batch Scanner Valuation Workflow.

Commit 0027 - Phase 2
---------------------

Connects the scanner-selected option contracts with the
existing SingleOptionValuator in batch mode.

Architecture
------------

OptionQuote
    ↓
ScannerValuationBridge
    ↓
TOP N CALL / PUT per underlying
    ↓
Batch Scanner Valuation
    ↓
SingleOptionValuationInput
    ↓
SingleOptionValuator
    ↓
SingleOptionValuationResult

Important
---------

This module does not modify:

- OptionQuote
- ScannerValuationBridge
- SingleOptionValuationInput
- SingleOptionValuator
- BlackScholes
- Greeks
- TaylorValuator

The batch layer only coordinates existing components.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

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


# ==========================================================
# Batch Valuation Parameters
# ==========================================================


@dataclass(frozen=True)
class BatchValuationParameters:
    """
    Parameters shared by a batch scanner valuation.

    Values are supplied per underlying futures contract.

    Parameters
    ----------
    current_futures_prices:
        Current futures price for each underlying.

    target_futures_prices:
        Target futures price for each underlying.

    remaining_days:
        Remaining days for each underlying option series.

    reference_volatility:
        Reference-volatility scenario for each underlying.

    risk_free_rate:
        Internal model risk-free rate.

    direction:
        Existing LONG / SHORT option direction.

    Notes
    -----
    The option-specific values are NOT supplied here.

    The following values come directly from each selected
    OptionQuote:

    - symbol
    - strike
    - current option price
    - current option IV
    - CALL / PUT
    - volume
    - open interest

    This prevents the user from having to enter parameters
    separately for every scanned contract.
    """

    current_futures_prices: Mapping[str, float]
    target_futures_prices: Mapping[str, float]
    remaining_days: Mapping[str, int]
    reference_volatility: Mapping[
        str,
        ReferenceVolatilityScenario,
    ]

    risk_free_rate: float = 0.025

    direction: OptionDirection | str = (
        OptionDirection.LONG
    )

    def validate(self) -> None:
        """Validate batch valuation parameters."""

        if self.risk_free_rate < 0:
            raise ValueError(
                "risk_free_rate cannot be negative."
            )

        self._validate_mapping(
            self.current_futures_prices,
            "current_futures_prices",
        )

        self._validate_mapping(
            self.target_futures_prices,
            "target_futures_prices",
        )

        self._validate_mapping(
            self.remaining_days,
            "remaining_days",
        )

        self._validate_reference_volatility()

        self._validate_direction()

    @staticmethod
    def _validate_mapping(
        values: Mapping[str, object],
        name: str,
    ) -> None:
        """Validate that mapping keys are non-empty."""

        for key in values:

            if not str(key).strip():
                raise ValueError(
                    f"{name} contains an empty underlying."
                )

    def _validate_reference_volatility(
        self,
    ) -> None:
        """Validate all reference-volatility scenarios."""

        for (
            underlying,
            scenario,
        ) in self.reference_volatility.items():

            if not str(underlying).strip():
                raise ValueError(
                    "reference_volatility contains "
                    "an empty underlying."
                )

            if not isinstance(
                scenario,
                ReferenceVolatilityScenario,
            ):
                raise TypeError(
                    "reference_volatility values must be "
                    "ReferenceVolatilityScenario."
                )

            scenario.validate()

    def _validate_direction(self) -> None:
        """Validate option direction."""

        if isinstance(
            self.direction,
            OptionDirection,
        ):
            return

        try:
            OptionDirection(
                str(
                    self.direction
                ).upper()
            )

        except ValueError as exc:

            raise ValueError(
                "direction must be LONG or SHORT."
            ) from exc


# ==========================================================
# Batch Valuation Item
# ==========================================================


@dataclass(frozen=True)
class BatchValuationItem:
    """
    One scanner candidate and its valuation result.
    """

    candidate: ScannerCandidate
    result: SingleOptionValuationResult

    @property
    def symbol(self) -> str:
        """Return option symbol."""

        return self.candidate.symbol

    @property
    def underlying(self) -> str:
        """Return underlying futures contract."""

        return self.candidate.underlying

    @property
    def option_type(self) -> str:
        """Return CALL / PUT."""

        return self.candidate.option_type

    @property
    def volume(self) -> int:
        """Return trading volume."""

        return self.candidate.volume


# ==========================================================
# Batch Valuation Result
# ==========================================================


@dataclass(frozen=True)
class BatchValuationResult:
    """
    Complete result of scanner batch valuation.

    Results preserve the scanner's selected-contract order.
    """

    items: tuple[BatchValuationItem, ...]

    @property
    def results(
        self,
    ) -> tuple[SingleOptionValuationResult, ...]:
        """Return valuation results."""

        return tuple(
            item.result
            for item in self.items
        )

    @property
    def count(self) -> int:
        """Return number of evaluated contracts."""

        return len(self.items)

    @property
    def symbols(self) -> tuple[str, ...]:
        """Return evaluated symbols."""

        return tuple(
            item.symbol
            for item in self.items
        )

    def by_underlying(
        self,
    ) -> dict[
        str,
        list[BatchValuationItem],
    ]:
        """
        Group results by underlying futures contract.
        """

        grouped: dict[
            str,
            list[BatchValuationItem],
        ] = {}

        for item in self.items:

            grouped.setdefault(
                item.underlying,
                [],
            ).append(
                item
            )

        return grouped

    def to_dict(
        self,
    ) -> list[
        dict[str, object]
    ]:
        """Return batch results as dictionaries."""

        return [
            {
                "symbol": item.symbol,
                "underlying": item.underlying,
                "option_type": item.option_type,
                "volume": item.volume,
                **item.result.to_dict(),
            }
            for item in self.items
        ]


# ==========================================================
# Scanner Batch Valuator
# ==========================================================


class ScannerBatchValuator:
    """
    Batch valuation service for scanner-selected options.

    Responsibilities
    ----------------
    1. Select TOP N contracts per underlying and type.
    2. Resolve batch valuation parameters.
    3. Create SingleOptionValuationInput objects.
    4. Reuse SingleOptionValuator.
    5. Return structured batch results.

    No pricing formula is implemented here.
    """

    def __init__(
        self,
        bridge: ScannerValuationBridge | None = None,
        valuator: SingleOptionValuator | None = None,
    ) -> None:
        """
        Initialize batch valuation service.

        Parameters
        ----------
        bridge:
            Existing scanner-to-valuation bridge.

        valuator:
            Existing single-option valuator.
        """

        self.bridge = (
            bridge
            if bridge is not None
            else ScannerValuationBridge()
        )

        self.valuator = (
            valuator
            if valuator is not None
            else SingleOptionValuator()
        )

    # ======================================================
    # Selection
    # ======================================================

    def select_candidates(
        self,
        quotes: Iterable[OptionQuote],
        *,
        top_n: int,
    ) -> list[ScannerCandidate]:
        """
        Select TOP N CALL / PUT contracts independently
        for every underlying.

        Selection is performed by trading volume only.
        """

        grouped = (
            self.bridge.select_top_by_underlying_and_type(
                quotes,
                top_n=top_n,
            )
        )

        selected: list[ScannerCandidate] = []

        for candidates in grouped.values():

            selected.extend(
                candidates
            )

        return selected

    # ======================================================
    # Build Input
    # ======================================================

    def create_valuation_input(
        self,
        candidate: ScannerCandidate,
        parameters: BatchValuationParameters,
    ) -> SingleOptionValuationInput:
        """
        Create one valuation input from a scanner candidate.

        All underlying-level parameters are resolved from
        BatchValuationParameters.
        """

        underlying = candidate.underlying

        current_futures_price = (
            self._get_required_mapping_value(
                parameters.current_futures_prices,
                underlying,
                "current_futures_prices",
            )
        )

        target_futures_price = (
            self._get_required_mapping_value(
                parameters.target_futures_prices,
                underlying,
                "target_futures_prices",
            )
        )

        remaining_days = (
            self._get_required_mapping_value(
                parameters.remaining_days,
                underlying,
                "remaining_days",
            )
        )

        reference_volatility = (
            self._get_required_mapping_value(
                parameters.reference_volatility,
                underlying,
                "reference_volatility",
            )
        )

        return self.bridge.create_valuation_input(
            candidate,
            current_futures_price=(
                float(
                    current_futures_price
                )
            ),
            remaining_days=int(
                remaining_days
            ),
            target_futures_price=(
                float(
                    target_futures_price
                )
            ),
            reference_volatility=(
                reference_volatility
            ),
            risk_free_rate=(
                parameters.risk_free_rate
            ),
            direction=(
                parameters.direction
            ),
        )

    # ======================================================
    # Build Inputs
    # ======================================================

    def create_valuation_inputs(
        self,
        candidates: Iterable[ScannerCandidate],
        parameters: BatchValuationParameters,
    ) -> list[SingleOptionValuationInput]:
        """
        Create valuation inputs for all selected candidates.
        """

        parameters.validate()

        return [
            self.create_valuation_input(
                candidate,
                parameters,
            )
            for candidate in candidates
        ]

    # ======================================================
    # Evaluate One
    # ======================================================

    def evaluate_candidate(
        self,
        candidate: ScannerCandidate,
        parameters: BatchValuationParameters,
    ) -> BatchValuationItem:
        """
        Evaluate one scanner candidate.
        """

        valuation_input = (
            self.create_valuation_input(
                candidate,
                parameters,
            )
        )

        result = self.valuator.evaluate(
            valuation_input
        )

        return BatchValuationItem(
            candidate=candidate,
            result=result,
        )

    # ======================================================
    # Evaluate Selected
    # ======================================================

    def evaluate_candidates(
        self,
        candidates: Iterable[ScannerCandidate],
        parameters: BatchValuationParameters,
    ) -> BatchValuationResult:
        """
        Evaluate already-selected scanner candidates.
        """

        parameters.validate()

        items = [
            self.evaluate_candidate(
                candidate,
                parameters,
            )
            for candidate in candidates
        ]

        return BatchValuationResult(
            items=tuple(
                items
            )
        )

    # ======================================================
    # Scan And Evaluate
    # ======================================================

    def scan_and_evaluate(
        self,
        quotes: Iterable[OptionQuote],
        *,
        top_n: int,
        parameters: BatchValuationParameters,
    ) -> BatchValuationResult:
        """
        Select scanner candidates and evaluate them.

        Flow
        ----

        OptionQuote
            ↓
        TOP N by underlying + CALL / PUT
            ↓
        SingleOptionValuationInput
            ↓
        SingleOptionValuator
            ↓
        BatchValuationResult
        """

        candidates = self.select_candidates(
            quotes,
            top_n=top_n,
        )

        return self.evaluate_candidates(
            candidates,
            parameters,
        )

    # ======================================================
    # Helpers
    # ======================================================

    @staticmethod
    def _get_required_mapping_value(
        mapping: Mapping[str, object],
        underlying: str,
        mapping_name: str,
    ) -> object:
        """Return a required underlying-level parameter."""

        if underlying not in mapping:
            raise ValueError(
                f"{mapping_name} is missing "
                f"underlying: {underlying}"
            )

        value = mapping[
            underlying
        ]

        if value is None:
            raise ValueError(
                f"{mapping_name} contains an empty "
                f"value for underlying: {underlying}"
            )

        return value


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "BatchValuationParameters",
    "BatchValuationItem",
    "BatchValuationResult",
    "ScannerBatchValuator",
]