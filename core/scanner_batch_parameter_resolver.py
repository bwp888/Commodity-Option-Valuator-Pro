"""
Commodity Option Valuator Pro
=============================

Scanner Batch Valuation Parameter Resolver.

Commit 0032
-----------

Resolves and validates the underlying-level parameter coverage
required by ScannerBatchValuator.

Architecture
------------

OptionQuote
    ↓
ScannerCandidate / selected quotes
    ↓
ScannerBatchParameterResolver
    ↓
Required underlying set
    ↓
BatchValuationParameters
    ↓
ScannerBatchValuator

Important
---------
This module does NOT:
- calculate option prices
- calculate Greeks
- calculate IV
- calculate target IV
- infer futures prices from option symbols
- infer expiry from option symbols
- modify ScannerBatchValuator
- modify SingleOptionValuator
- modify ComprehensiveEvaluator

It only establishes the parameter coverage boundary for
automatic scanner batch valuation.

The resolver deliberately uses OptionQuote.underlying as the
唯一标的标识来源.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from core.scanner_batch_valuation import (
    BatchValuationParameters,
)
from core.scanner_valuation_bridge import (
    ScannerCandidate,
)
from data.option_chain import (
    OptionQuote,
)


# ==========================================================
# Parameter Coverage
# ==========================================================


@dataclass(frozen=True)
class ScannerBatchParameterCoverage:
    """
    Parameter coverage for scanner-selected underlyings.

    Attributes
    ----------
    required_underlyings:
        Underlyings represented by the selected scanner quotes.

    missing_current_futures_prices:
        Underlyings without current futures prices.

    missing_target_futures_prices:
        Underlyings without target futures prices.

    missing_remaining_days:
        Underlyings without remaining-day information.

    missing_reference_volatility:
        Underlyings without reference-volatility scenarios.
    """

    required_underlyings: tuple[str, ...]

    missing_current_futures_prices: tuple[str, ...]

    missing_target_futures_prices: tuple[str, ...]

    missing_remaining_days: tuple[str, ...]

    missing_reference_volatility: tuple[str, ...]

    @property
    def is_complete(self) -> bool:
        """Return whether all required parameters are present."""

        return not any(
            (
                self.missing_current_futures_prices,
                self.missing_target_futures_prices,
                self.missing_remaining_days,
                self.missing_reference_volatility,
            )
        )

    @property
    def missing_underlyings(self) -> tuple[str, ...]:
        """
        Return the union of all underlyings with missing parameters.
        """

        values: set[str] = set()

        values.update(
            self.missing_current_futures_prices
        )
        values.update(
            self.missing_target_futures_prices
        )
        values.update(
            self.missing_remaining_days
        )
        values.update(
            self.missing_reference_volatility
        )

        return tuple(
            underlying
            for underlying in self.required_underlyings
            if underlying in values
        )

    def to_dict(self) -> dict[str, object]:
        """Return coverage information as a dictionary."""

        return {
            "required_underlyings": (
                self.required_underlyings
            ),
            "missing_current_futures_prices": (
                self.missing_current_futures_prices
            ),
            "missing_target_futures_prices": (
                self.missing_target_futures_prices
            ),
            "missing_remaining_days": (
                self.missing_remaining_days
            ),
            "missing_reference_volatility": (
                self.missing_reference_volatility
            ),
            "is_complete": self.is_complete,
            "missing_underlyings": self.missing_underlyings,
        }


# ==========================================================
# Resolver
# ==========================================================


class ScannerBatchParameterResolver:
    """
    Resolve parameter coverage for scanner batch valuation.

    This class intentionally does not invent market data.

    It answers two questions:

    1. Which underlyings are actually present in the scanner
       selection?
    2. Does BatchValuationParameters contain all required
       values for those underlyings?
    """

    # ------------------------------------------------------
    # Quote Validation
    # ------------------------------------------------------

    @staticmethod
    def validate_quotes(
        quotes: Iterable[OptionQuote],
    ) -> tuple[OptionQuote, ...]:
        """
        Validate and materialize scanner quotes.
        """

        materialized = tuple(quotes)

        for quote in materialized:
            if not isinstance(
                quote,
                OptionQuote,
            ):
                raise TypeError(
                    "quotes must contain OptionQuote."
                )

            if not str(
                quote.underlying
            ).strip():
                raise ValueError(
                    "OptionQuote.underlying "
                    "cannot be empty."
                )

        return materialized

    # ------------------------------------------------------
    # Underlying Discovery
    # ------------------------------------------------------

    @classmethod
    def required_underlyings(
        cls,
        quotes: Iterable[OptionQuote],
    ) -> tuple[str, ...]:
        """
        Discover the unique underlyings represented by quotes.

        The explicit OptionQuote.underlying field is the only
        source used.

        No symbol parsing is performed.
        """

        validated = cls.validate_quotes(
            quotes
        )

        underlyings = {
            str(
                quote.underlying
            ).strip()
            for quote in validated
        }

        return tuple(
            sorted(
                underlyings
            )
        )

    @classmethod
    def required_underlyings_from_candidates(
        cls,
        candidates: Iterable[ScannerCandidate],
    ) -> tuple[str, ...]:
        """
        Discover unique underlyings from ScannerCandidate objects.
        """

        materialized = tuple(
            candidates
        )

        for candidate in materialized:
            if not isinstance(
                candidate,
                ScannerCandidate,
            ):
                raise TypeError(
                    "candidates must contain ScannerCandidate."
                )

        return tuple(
            sorted(
                {
                    str(
                        candidate.underlying
                    ).strip()
                    for candidate in materialized
                }
            )
        )

    # ------------------------------------------------------
    # Mapping Coverage
    # ------------------------------------------------------

    @staticmethod
    def _missing_keys(
        required: tuple[str, ...],
        values: Mapping[str, object],
    ) -> tuple[str, ...]:
        """Return required keys absent from a mapping."""

        return tuple(
            underlying
            for underlying in required
            if underlying not in values
            or values[underlying] is None
        )

    # ------------------------------------------------------
    # Parameter Coverage
    # ------------------------------------------------------

    @classmethod
    def inspect(
        cls,
        quotes: Iterable[OptionQuote],
        parameters: BatchValuationParameters,
    ) -> ScannerBatchParameterCoverage:
        """
        Inspect parameter coverage for scanner quotes.
        """

        if not isinstance(
            parameters,
            BatchValuationParameters,
        ):
            raise TypeError(
                "parameters must be "
                "BatchValuationParameters."
            )

        required = cls.required_underlyings(
            quotes
        )

        return ScannerBatchParameterCoverage(
            required_underlyings=required,
            missing_current_futures_prices=(
                cls._missing_keys(
                    required,
                    parameters.current_futures_prices,
                )
            ),
            missing_target_futures_prices=(
                cls._missing_keys(
                    required,
                    parameters.target_futures_prices,
                )
            ),
            missing_remaining_days=(
                cls._missing_keys(
                    required,
                    parameters.remaining_days,
                )
            ),
            missing_reference_volatility=(
                cls._missing_keys(
                    required,
                    parameters.reference_volatility,
                )
            ),
        )

    # ------------------------------------------------------
    # Completeness
    # ------------------------------------------------------

    @classmethod
    def validate_complete(
        cls,
        quotes: Iterable[OptionQuote],
        parameters: BatchValuationParameters,
    ) -> ScannerBatchParameterCoverage:
        """
        Validate that all selected underlyings have complete
        batch valuation parameters.

        Returns
        -------
        ScannerBatchParameterCoverage
            Complete coverage information.

        Raises
        ------
        ValueError
            If one or more required parameters are missing.
        """

        parameters.validate()

        coverage = cls.inspect(
            quotes,
            parameters,
        )

        if coverage.is_complete:
            return coverage

        missing_messages: list[str] = []

        if coverage.missing_current_futures_prices:
            missing_messages.append(
                "current_futures_prices="
                + ", ".join(
                    coverage.missing_current_futures_prices
                )
            )

        if coverage.missing_target_futures_prices:
            missing_messages.append(
                "target_futures_prices="
                + ", ".join(
                    coverage.missing_target_futures_prices
                )
            )

        if coverage.missing_remaining_days:
            missing_messages.append(
                "remaining_days="
                + ", ".join(
                    coverage.missing_remaining_days
                )
            )

        if coverage.missing_reference_volatility:
            missing_messages.append(
                "reference_volatility="
                + ", ".join(
                    coverage.missing_reference_volatility
                )
            )

        raise ValueError(
            "Scanner batch valuation parameters are incomplete: "
            + "; ".join(
                missing_messages
            )
        )

    # ------------------------------------------------------
    # Candidate Coverage
    # ------------------------------------------------------

    @classmethod
    def validate_candidates_complete(
        cls,
        candidates: Iterable[ScannerCandidate],
        parameters: BatchValuationParameters,
    ) -> ScannerBatchParameterCoverage:
        """
        Validate parameter coverage for already-selected
        ScannerCandidate objects.
        """

        materialized = tuple(
            candidates
        )

        for candidate in materialized:
            if not isinstance(
                candidate,
                ScannerCandidate,
            ):
                raise TypeError(
                    "candidates must contain "
                    "ScannerCandidate."
                )

        parameters.validate()

        required = cls.required_underlyings_from_candidates(
            materialized
        )

        coverage = ScannerBatchParameterCoverage(
            required_underlyings=required,
            missing_current_futures_prices=(
                cls._missing_keys(
                    required,
                    parameters.current_futures_prices,
                )
            ),
            missing_target_futures_prices=(
                cls._missing_keys(
                    required,
                    parameters.target_futures_prices,
                )
            ),
            missing_remaining_days=(
                cls._missing_keys(
                    required,
                    parameters.remaining_days,
                )
            ),
            missing_reference_volatility=(
                cls._missing_keys(
                    required,
                    parameters.reference_volatility,
                )
            ),
        )

        if not coverage.is_complete:
            raise ValueError(
                cls._format_incomplete_message(
                    coverage
                )
            )

        return coverage

    # ------------------------------------------------------
    # Error Formatting
    # ------------------------------------------------------

    @staticmethod
    def _format_incomplete_message(
        coverage: ScannerBatchParameterCoverage,
    ) -> str:
        """Build a deterministic validation message."""

        missing_messages: list[str] = []

        if coverage.missing_current_futures_prices:
            missing_messages.append(
                "current_futures_prices="
                + ", ".join(
                    coverage.missing_current_futures_prices
                )
            )

        if coverage.missing_target_futures_prices:
            missing_messages.append(
                "target_futures_prices="
                + ", ".join(
                    coverage.missing_target_futures_prices
                )
            )

        if coverage.missing_remaining_days:
            missing_messages.append(
                "remaining_days="
                + ", ".join(
                    coverage.missing_remaining_days
                )
            )

        if coverage.missing_reference_volatility:
            missing_messages.append(
                "reference_volatility="
                + ", ".join(
                    coverage.missing_reference_volatility
                )
            )

        return (
            "Scanner batch valuation parameters are incomplete: "
            + "; ".join(
                missing_messages
            )
        )


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "ScannerBatchParameterCoverage",
    "ScannerBatchParameterResolver",
]