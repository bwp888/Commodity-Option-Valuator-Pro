"""
Commodity Option Valuator Pro
=============================

Automatic Option Chain Scanner.

Commit 0025
------------

Connects the existing TongDaXin option-chain reader with the
existing recommendation workflow.

Architecture
------------

TDX exported file
    ↓
TDXOptionReader
    ↓
OptionQuote
    ↓
AutoOptionScanner
    ↓
RecommendationWorkflow
    ↓
RecommendationWorkflowResult

Important
---------
This module deliberately does not modify:

- TDXOptionReader
- OptionQuote
- MarketDataAdapter
- MarketValuationWorkflow
- RecommendationWorkflow
- UI components

The scanner only acts as an orchestration boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.recommendation_workflow import (
    RecommendationWorkflow,
    RecommendationWorkflowResult,
)
from data.option_chain import OptionQuote
from data.tdx_reader import TDXOptionReader
from models.option_scanner import OptionDirection


@dataclass(frozen=True)
class AutoOptionScanParameters:
    """
    Parameters required for one automatic option-chain scan.

    The scanner intentionally requires the caller to provide
    underlying price, remaining days, and volatility.

    These values are not inferred from the TDX option-chain file.
    """

    underlying_price: float
    days: int
    volatility: float
    risk_free_rate: float = 0.025

    direction: OptionDirection | str | None = None

    min_volume: int = 0
    top_n: int | None = None

    def validate(self) -> None:
        """Validate scan parameters."""

        if self.underlying_price <= 0:
            raise ValueError(
                "underlying_price must be greater than zero"
            )

        if self.days <= 0:
            raise ValueError(
                "days must be greater than zero"
            )

        if self.volatility <= 0:
            raise ValueError(
                "volatility must be greater than zero"
            )

        if self.min_volume < 0:
            raise ValueError(
                "min_volume cannot be negative"
            )

        if self.top_n is not None and self.top_n <= 0:
            raise ValueError(
                "top_n must be greater than zero"
            )


class AutoOptionScanner:
    """
    Automatic option-chain scanner.

    Responsibilities
    ----------------
    1. Read a TDX option-chain export.
    2. Convert OptionQuote objects into the existing market-record format.
    3. Pass those records into RecommendationWorkflow.
    4. Return the existing RecommendationWorkflowResult.

    The scanner contains no valuation logic of its own.
    """

    SOURCE = "TDX"

    def __init__(
        self,
        workflow: RecommendationWorkflow | None = None,
    ) -> None:
        """
        Initialize the automatic scanner.

        Parameters
        ----------
        workflow:
            Optional existing RecommendationWorkflow.

            Dependency injection is supported so this class can
            be tested without executing the complete valuation
            stack.
        """

        self.workflow = (
            workflow
            if workflow is not None
            else RecommendationWorkflow()
        )

    # ==========================================================
    # OptionQuote → Market Record
    # ==========================================================

    @staticmethod
    def quote_to_record(
        quote: OptionQuote,
    ) -> dict[str, object]:
        """
        Convert one OptionQuote into the market-record structure
        already accepted by MarketDataAdapter.

        No new market-data schema is introduced here.
        """

        if not isinstance(quote, OptionQuote):
            raise TypeError(
                "quote must be an OptionQuote"
            )

        return {
            "symbol": quote.symbol,
            "direction": quote.option_type,
            "strike": quote.strike,
            "price": quote.last_price,
            "volume": quote.volume,
            "open_interest": quote.open_interest,
            "bid": (
                quote.bid_price
                if quote.bid_price is not None
                else 0.0
            ),
            "ask": (
                quote.ask_price
                if quote.ask_price is not None
                else 0.0
            ),
        }

    @classmethod
    def quotes_to_records(
        cls,
        quotes: Iterable[OptionQuote],
    ) -> list[dict[str, object]]:
        """
        Convert an iterable of OptionQuote objects into market
        records accepted by RecommendationWorkflow.
        """

        records: list[dict[str, object]] = []

        for quote in quotes:
            records.append(
                cls.quote_to_record(quote)
            )

        return records

    # ==========================================================
    # Reading
    # ==========================================================

    @staticmethod
    def read_quotes(
        file_path: str | Path,
    ) -> list[OptionQuote]:
        """
        Read normalized option quotes from a TDX export file.
        """

        reader = TDXOptionReader(
            file_path=file_path,
        )

        return reader.read_quotes()

    # ==========================================================
    # Scan
    # ==========================================================

    def scan_quotes(
        self,
        quotes: Iterable[OptionQuote],
        *,
        parameters: AutoOptionScanParameters,
    ) -> RecommendationWorkflowResult:
        """
        Scan an already-loaded collection of OptionQuote objects.

        This method is useful for callers that already have market
        data and want to avoid reading the file again.
        """

        parameters.validate()

        records = self.quotes_to_records(
            quotes
        )

        return self.workflow.run(
            records=records,
            underlying_price=parameters.underlying_price,
            days=parameters.days,
            volatility=parameters.volatility,
            risk_free_rate=parameters.risk_free_rate,
            direction=parameters.direction,
            min_volume=parameters.min_volume,
            top_n=parameters.top_n,
        )

    def scan(
        self,
        file_path: str | Path,
        *,
        underlying_price: float,
        days: int,
        volatility: float,
        risk_free_rate: float = 0.025,
        direction: OptionDirection | str | None = None,
        min_volume: int = 0,
        top_n: int | None = None,
    ) -> RecommendationWorkflowResult:
        """
        Read a TDX option-chain export and execute the complete
        recommendation scan.

        Parameters
        ----------
        file_path:
            Path to the TDX exported option-chain file.

        underlying_price:
            Current underlying futures price.

        days:
            Remaining calendar days.

        volatility:
            Annualized volatility.

        risk_free_rate:
            Annualized risk-free rate.

        direction:
            Optional CALL / PUT filter.

        min_volume:
            Minimum trading volume.

        top_n:
            Optional maximum number of contracts selected by
            the existing recommendation workflow.

        Returns
        -------
        RecommendationWorkflowResult
            Existing recommendation workflow result.
        """

        parameters = AutoOptionScanParameters(
            underlying_price=underlying_price,
            days=days,
            volatility=volatility,
            risk_free_rate=risk_free_rate,
            direction=direction,
            min_volume=min_volume,
            top_n=top_n,
        )

        # Validate all parameters before touching the input file.
        #
        # This is intentionally performed here rather than relying
        # on scan_quotes(), because scan() must reject invalid input
        # before read_quotes() is called.
        parameters.validate()

        quotes = self.read_quotes(
            file_path
        )

        return self.scan_quotes(
            quotes,
            parameters=parameters,
        )


__all__ = [
    "AutoOptionScanParameters",
    "AutoOptionScanner",
]