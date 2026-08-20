"""
Commodity Option Valuator Pro
=============================

Scanner → Single Option Valuation Bridge.

Commit 0027
------------

Connects the existing option-chain market data with the
existing SingleOptionValuation workflow.

Architecture
------------

TDXOptionReader
    ↓
OptionQuote
    ↓
ScannerValuationBridge
    ↓
Volume-ranked candidates
    ↓
Selected OptionQuote
    ↓
SingleOptionValuationInput
    ↓
SingleOptionValuator

Important
---------

This module deliberately does not modify:

- OptionQuote
- TDXOptionReader
- AutoOptionScanner
- SingleOptionValuator
- SingleOptionValuationInput
- RecommendationWorkflow
- UI components

The bridge only connects existing data structures and
valuation workflow boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.single_option_valuation import (
    ReferenceVolatilityScenario,
    SingleOptionValuationInput,
)
from data.option_chain import OptionQuote
from models.option import (
    OptionDirection,
    OptionType,
)


# ==========================================================
# Scanner Candidate
# ==========================================================


@dataclass(frozen=True)
class ScannerCandidate:
    """
    One option contract available for single-option valuation.

    This is a lightweight presentation-independent wrapper
    around the existing OptionQuote.

    No valuation is performed here.
    """

    quote: OptionQuote

    @property
    def symbol(self) -> str:
        """Return option contract symbol."""

        return self.quote.symbol

    @property
    def underlying(self) -> str:
        """Return underlying futures contract."""

        return self.quote.underlying

    @property
    def option_type(self) -> str:
        """Return CALL / PUT."""

        return self.quote.option_type

    @property
    def strike(self) -> float:
        """Return option strike price."""

        return self.quote.strike

    @property
    def option_price(self) -> float:
        """Return current option market price."""

        return self.quote.last_price

    @property
    def volume(self) -> int:
        """Return current trading volume."""

        return self.quote.volume

    @property
    def open_interest(self) -> int:
        """Return current open interest."""

        return self.quote.open_interest

    @property
    def implied_volatility(self) -> float | None:
        """Return current single-option implied volatility."""

        return self.quote.implied_volatility


# ==========================================================
# Scanner → Valuation Bridge
# ==========================================================


class ScannerValuationBridge:
    """
    Bridge between option-chain scanning and single-option
    valuation.

    Responsibilities
    ----------------
    1. Accept existing OptionQuote objects.
    2. Group contracts by underlying and CALL / PUT.
    3. Rank contracts by trading volume.
    4. Return the top N contracts in each group.
    5. Convert one selected OptionQuote into
       SingleOptionValuationInput.

    The bridge does not calculate option prices or Greeks.
    """

    # ======================================================
    # Candidate Conversion
    # ======================================================

    @staticmethod
    def to_candidate(
        quote: OptionQuote,
    ) -> ScannerCandidate:
        """
        Convert one OptionQuote into a ScannerCandidate.
        """

        if not isinstance(
            quote,
            OptionQuote,
        ):
            raise TypeError(
                "quote must be an OptionQuote"
            )

        return ScannerCandidate(
            quote=quote,
        )

    @classmethod
    def to_candidates(
        cls,
        quotes: Iterable[OptionQuote],
    ) -> list[ScannerCandidate]:
        """
        Convert an iterable of OptionQuote objects into
        ScannerCandidate objects.
        """

        return [
            cls.to_candidate(quote)
            for quote in quotes
        ]

    # ======================================================
    # Candidate Selection
    # ======================================================

    @staticmethod
    def select_top_by_volume(
        quotes: Iterable[OptionQuote],
        *,
        top_n: int,
        underlying: str | None = None,
        option_type: str | None = None,
    ) -> list[ScannerCandidate]:
        """
        Select the highest-volume option contracts.

        Parameters
        ----------
        quotes:
            Existing normalized option quotes.

        top_n:
            Number of contracts to return.

        underlying:
            Optional underlying futures contract filter.

        option_type:
            Optional CALL / PUT filter.

        Notes
        -----
        Ranking is based only on trading volume.

        This deliberately does not use:
        - minimum volume
        - risk score
        - recommendation score
        - theoretical valuation

        The purpose is to select the most active contracts
        before entering single-option valuation.
        """

        if top_n <= 0:
            raise ValueError(
                "top_n must be greater than zero"
            )

        normalized_option_type: str | None = None

        if option_type is not None:
            normalized_option_type = (
                str(option_type).upper()
            )

            if normalized_option_type not in {
                "CALL",
                "PUT",
            }:
                raise ValueError(
                    "option_type must be CALL or PUT"
                )

        filtered: list[OptionQuote] = []

        for quote in quotes:

            if not isinstance(
                quote,
                OptionQuote,
            ):
                raise TypeError(
                    "quotes must contain OptionQuote"
                )

            if (
                underlying is not None
                and quote.underlying
                != underlying
            ):
                continue

            if (
                normalized_option_type is not None
                and quote.option_type
                != normalized_option_type
            ):
                continue

            filtered.append(
                quote
            )

        filtered.sort(
            key=lambda quote: quote.volume,
            reverse=True,
        )

        return [
            ScannerCandidate(
                quote=quote
            )
            for quote in filtered[:top_n]
        ]

    # ======================================================
    # Grouped Selection
    # ======================================================

    @staticmethod
    def select_top_by_underlying_and_type(
        quotes: Iterable[OptionQuote],
        *,
        top_n: int,
    ) -> dict[
        tuple[str, str],
        list[ScannerCandidate],
    ]:
        """
        Select TOP N contracts separately for each
        underlying and option type.

        Grouping:

            (underlying, CALL)
            (underlying, PUT)

        Example
        -------

        AU2608 + CALL
            → TOP N by volume

        AU2608 + PUT
            → TOP N by volume

        Another underlying
            → independently ranked again.

        This is the core selection behavior intended
        for the automatic scanner.
        """

        if top_n <= 0:
            raise ValueError(
                "top_n must be greater than zero"
            )

        grouped: dict[
            tuple[str, str],
            list[OptionQuote],
        ] = {}

        for quote in quotes:

            if not isinstance(
                quote,
                OptionQuote,
            ):
                raise TypeError(
                    "quotes must contain OptionQuote"
                )

            key = (
                quote.underlying,
                quote.option_type,
            )

            grouped.setdefault(
                key,
                [],
            ).append(
                quote
            )

        result: dict[
            tuple[str, str],
            list[ScannerCandidate],
        ] = {}

        for key, group in grouped.items():

            group.sort(
                key=lambda quote: quote.volume,
                reverse=True,
            )

            result[key] = [
                ScannerCandidate(
                    quote=quote
                )
                for quote in group[:top_n]
            ]

        return result

    # ======================================================
    # Find Selected Contract
    # ======================================================

    @staticmethod
    def find_candidate(
        quotes: Iterable[OptionQuote],
        symbol: str,
    ) -> ScannerCandidate:
        """
        Find one option contract by symbol.

        Raises
        ------
        ValueError
            If no matching contract exists.
        """

        if not symbol:
            raise ValueError(
                "symbol cannot be empty"
            )

        for quote in quotes:

            if not isinstance(
                quote,
                OptionQuote,
            ):
                raise TypeError(
                    "quotes must contain OptionQuote"
                )

            if quote.symbol == symbol:

                return ScannerCandidate(
                    quote=quote
                )

        raise ValueError(
            f"option contract not found: {symbol}"
        )

    # ======================================================
    # Option Type
    # ======================================================

    @staticmethod
    def _parse_option_type(
        value: str,
    ) -> OptionType:
        """
        Convert CALL / PUT string into existing OptionType.
        """

        try:
            return OptionType(
                str(value).upper()
            )
        except ValueError as exc:

            raise ValueError(
                "option_type must be CALL or PUT"
            ) from exc

    # ======================================================
    # Single Option Valuation Input
    # ======================================================

    @classmethod
    def create_valuation_input(
        cls,
        candidate: ScannerCandidate,
        *,
        current_futures_price: float,
        remaining_days: int,
        target_futures_price: float,
        reference_volatility: ReferenceVolatilityScenario,
        risk_free_rate: float = 0.025,
        direction: OptionDirection | str = (
            OptionDirection.LONG
        ),
    ) -> SingleOptionValuationInput:
        """
        Convert one scanner candidate into the existing
        SingleOptionValuationInput.

        Parameters
        ----------
        candidate:
            Selected option contract.

        current_futures_price:
            Current underlying futures price.

        remaining_days:
            Remaining days until option expiry.

        target_futures_price:
            Target underlying futures price for scenario
            analysis.

        reference_volatility:
            Reference volatility scenario.

        risk_free_rate:
            Internal model risk-free rate.

        direction:
            Existing LONG / SHORT direction.

        Important
        ---------
        The current option IV comes directly from the selected
        OptionQuote.

        The bridge does not calculate or modify the IV.

        Target IV is calculated later by
        SingleOptionValuator according to the reference
        volatility scenario.
        """

        if not isinstance(
            candidate,
            ScannerCandidate,
        ):
            raise TypeError(
                "candidate must be a ScannerCandidate"
            )

        current_option_iv = (
            candidate.implied_volatility
        )

        if current_option_iv is None:
            raise ValueError(
                "selected option does not contain "
                "implied volatility"
            )

        if current_option_iv <= 0:
            raise ValueError(
                "selected option implied volatility "
                "must be greater than zero"
            )

        return SingleOptionValuationInput(
            symbol=candidate.symbol,
            option_type=cls._parse_option_type(
                candidate.option_type
            ),
            current_futures_price=(
                current_futures_price
            ),
            strike=candidate.strike,
            current_option_price=(
                candidate.option_price
            ),
            current_option_iv=(
                current_option_iv
            ),
            remaining_days=remaining_days,
            target_futures_price=(
                target_futures_price
            ),
            reference_volatility=(
                reference_volatility
            ),
            risk_free_rate=risk_free_rate,
            direction=direction,
        )


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "ScannerCandidate",
    "ScannerValuationBridge",
]