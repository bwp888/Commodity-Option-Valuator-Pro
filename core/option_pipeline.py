"""
Commodity Option Valuator Pro
=============================

Option Valuation Pipeline.

Commit 0010
-----------

Connects market data readers with the
valuation engine.

Pipeline
--------
Market Data File
        ↓
Market Data Reader
        ↓
OptionContract
        ↓
ValuationEngine
        ↓
ValuationResult

Author : Simon
Version : 0.2.2
Python : 3.12
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.valuation_engine import (
    ValuationEngine,
    ValuationResult,
)

from models.option_scanner import (
    OptionContract,
)

from data.excel_reader import (
    ExcelOptionReader,
)


# ==========================================================
# Pipeline Configuration
# ==========================================================


@dataclass(frozen=True)
class PipelineParameters:
    """
    Parameters used by the valuation pipeline.

    Parameters
    ----------
    underlying_price:
        Current underlying futures price.

    volatility:
        Annualized volatility.

    days:
        Remaining calendar days to expiration.

    risk_free_rate:
        Annualized risk-free interest rate.
    """

    underlying_price: float

    volatility: float

    days: int

    risk_free_rate: float = 0.025

    def validate(self) -> None:
        """
        Validate pipeline parameters.

        Raises
        ------
        ValueError
            If any parameter is invalid.
        """

        if self.underlying_price <= 0:
            raise ValueError(
                "underlying_price must be greater than zero"
            )

        if self.volatility <= 0:
            raise ValueError(
                "volatility must be greater than zero"
            )

        if self.days <= 0:
            raise ValueError(
                "days must be greater than zero"
            )

        if self.risk_free_rate < 0:
            raise ValueError(
                "risk_free_rate must not be negative"
            )


# ==========================================================
# Pipeline Result
# ==========================================================


@dataclass
class PipelineResult:
    """
    Complete result returned by the valuation pipeline.

    Attributes
    ----------
    contracts:
        Loaded market option contracts.

    valuations:
        Corresponding valuation results.
    """

    contracts: list[OptionContract]

    valuations: list[ValuationResult]

    @property
    def contract_count(self) -> int:
        """Return loaded contract count."""

        return len(
            self.contracts
        )

    @property
    def valuation_count(self) -> int:
        """Return valuation result count."""

        return len(
            self.valuations
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert pipeline result to dictionary.
        """

        return {
            "contract_count": self.contract_count,
            "valuation_count": self.valuation_count,
            "valuations": [
                {
                    "symbol": item.symbol,
                    "direction": item.direction.value,
                    "premium": item.premium,
                    "theoretical_price": item.theoretical_price,
                    "delta": item.delta,
                    "gamma": item.gamma,
                    "theta": item.theta,
                    "vega": item.vega,
                    "difference": item.difference,
                    "risk_score": item.risk_score,
                }
                for item in self.valuations
            ],
        }


# ==========================================================
# Option Pipeline
# ==========================================================


class OptionPipeline:
    """
    Main market-data-to-valuation pipeline.

    Responsibilities
    ----------------
    1. Load option market data.
    2. Normalize market records.
    3. Validate valuation parameters.
    4. Run valuation engine.
    5. Return structured results.

    The pipeline deliberately does not contain
    UI-specific logic.
    """

    def __init__(
        self,
        valuation_engine: ValuationEngine | None = None,
    ) -> None:
        """
        Initialize pipeline.

        Parameters
        ----------
        valuation_engine:
            Optional valuation engine.

            If omitted, a default engine with
            2.5% risk-free rate is created.
        """

        self.valuation_engine = (
            valuation_engine
            if valuation_engine is not None
            else ValuationEngine()
        )

        self.contracts: list[
            OptionContract
        ] = []

        self.results: list[
            ValuationResult
        ] = []

        self.source_path: Path | None = None

    # ======================================================
    # Properties
    # ======================================================

    @property
    def contract_count(self) -> int:
        """Return current market contract count."""

        return len(
            self.contracts
        )

    @property
    def result_count(self) -> int:
        """Return current valuation result count."""

        return len(
            self.results
        )

    @property
    def is_loaded(self) -> bool:
        """Return whether market data has been loaded."""

        return bool(
            self.contracts
        )

    @property
    def is_valuated(self) -> bool:
        """Return whether valuation results exist."""

        return bool(
            self.results
        )

    # ======================================================
    # Load Market Data
    # ======================================================

    def load_market_data(
        self,
        file_path: str | Path,
    ) -> list[OptionContract]:
        """
        Load option market data from Excel.

        Parameters
        ----------
        file_path:
            Path to the market data file.

        Returns
        -------
        list[OptionContract]
            Normalized option contracts.

        Raises
        ------
        FileNotFoundError
            If the file does not exist.

        ValueError
            If the reader returns invalid data.
        """

        path = Path(
            file_path
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Market data file not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Market data path is not a file: {path}"
            )

        reader = ExcelOptionReader()

        contracts = reader.read(
            path
        )

        if contracts is None:
            raise ValueError(
                "Market data reader returned None"
            )

        self.contracts = list(
            contracts
        )

        self.source_path = path

        self.results = []

        return list(
            self.contracts
        )

    # ======================================================
    # Set Market Data
    # ======================================================

    def set_contracts(
        self,
        contracts: list[OptionContract],
    ) -> None:
        """
        Set already-normalized option contracts.

        This method is useful when market data has
        already been loaded by another reader.

        Parameters
        ----------
        contracts:
            Normalized option contract list.
        """

        self.contracts = list(
            contracts
        )

        self.results = []

        self.source_path = None

    # ======================================================
    # Clear
    # ======================================================

    def clear(self) -> None:
        """
        Clear loaded market data and valuation results.
        """

        self.contracts = []

        self.results = []

        self.source_path = None

    # ======================================================
    # Validate Parameters
    # ======================================================

    def validate_parameters(
        self,
        parameters: PipelineParameters,
    ) -> None:
        """
        Validate pipeline parameters.
        """

        parameters.validate()

    # ======================================================
    # Evaluate
    # ======================================================

    def evaluate(
        self,
        parameters: PipelineParameters,
    ) -> list[ValuationResult]:
        """
        Evaluate all loaded option contracts.

        Parameters
        ----------
        parameters:
            Valuation parameters.

        Returns
        -------
        list[ValuationResult]
            Valuation results.

        Raises
        ------
        ValueError
            If no market data has been loaded or
            parameters are invalid.
        """

        self.validate_parameters(
            parameters
        )

        if not self.contracts:
            raise ValueError(
                "No option contracts loaded"
            )

        self.results = (
            self.valuation_engine.evaluate_batch(
                self.contracts,
                parameters.underlying_price,
                parameters.volatility,
                parameters.days,
            )
        )

        return list(
            self.results
        )

    # ======================================================
    # Evaluate Single Contract
    # ======================================================

    def evaluate_contract(
        self,
        contract: OptionContract,
        parameters: PipelineParameters,
    ) -> ValuationResult:
        """
        Evaluate one option contract.

        The contract does not need to be part of the
        currently loaded pipeline data.
        """

        self.validate_parameters(
            parameters
        )

        return self.valuation_engine.evaluate(
            contract,
            parameters.underlying_price,
            parameters.volatility,
            parameters.days,
        )

    # ======================================================
    # Run
    # ======================================================

    def run(
        self,
        file_path: str | Path,
        parameters: PipelineParameters,
    ) -> PipelineResult:
        """
        Execute the complete pipeline.

        Pipeline
        --------
        1. Load market data.
        2. Validate parameters.
        3. Evaluate contracts.
        4. Return structured result.
        """

        self.load_market_data(
            file_path
        )

        valuations = self.evaluate(
            parameters
        )

        return PipelineResult(
            contracts=list(
                self.contracts
            ),
            valuations=list(
                valuations
            ),
        )

    # ======================================================
    # Result Access
    # ======================================================

    def get_results(
        self,
    ) -> list[ValuationResult]:
        """
        Return current valuation results.
        """

        return list(
            self.results
        )

    def get_contracts(
        self,
    ) -> list[OptionContract]:
        """
        Return current market contracts.
        """

        return list(
            self.contracts
        )

    # ======================================================
    # Result Export
    # ======================================================

    def results_to_dict(
        self,
    ) -> list[dict[str, Any]]:
        """
        Convert current valuation results to dictionaries.
        """

        return [
            self.valuation_engine.result_to_dict(
                result
            )
            for result in self.results
        ]

    # ======================================================
    # String Representation
    # ======================================================

    def __str__(
        self,
    ) -> str:
        """Return human-readable representation."""

        return (
            "OptionPipeline("
            f"contracts={self.contract_count}, "
            f"results={self.result_count}"
            ")"
        )

    def __repr__(
        self,
    ) -> str:
        """Return developer representation."""

        return (
            "OptionPipeline("
            f"valuation_engine={self.valuation_engine!r}"
            ")"
        )


# ==========================================================
# Public Exports
# ==========================================================

__all__ = [
    "PipelineParameters",
    "PipelineResult",
    "OptionPipeline",
]