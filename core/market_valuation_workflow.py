"""
Commodity Option Valuator Pro
=============================

Market Valuation Workflow.

Commit 0015
------------

Connect market data with the option valuation pipeline.

Author : Simon
Version : 0.4.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from core.option_pipeline import (
    OptionPipeline,
    PipelineParameters,
)

from core.valuation_engine import (
    ValuationResult,
)

from data.market_data_adapter import (
    MarketDataAdapter,
)

from models.option_scanner import (
    OptionContract,
    OptionDirection,
)


# ==========================================================
# Workflow Result
# ==========================================================


@dataclass(frozen=True)
class MarketValuationItem:
    """
    One market contract with its valuation result.
    """

    contract: OptionContract
    result: ValuationResult


@dataclass(frozen=True)
class MarketValuationWorkflowResult:
    """
    Result returned by the market valuation workflow.

    Attributes
    ----------
    items:
        Successfully valued contracts.

    total_contracts:
        Number of normalized contracts received.

    selected_contracts:
        Number of contracts selected for valuation.

    successful_count:
        Number of successful valuations.
    """

    items: tuple[MarketValuationItem, ...]
    total_contracts: int
    selected_contracts: int
    successful_count: int

    @property
    def results(
        self,
    ) -> tuple[ValuationResult, ...]:
        """Return valuation results only."""

        return tuple(
            item.result
            for item in self.items
        )

    @property
    def contracts(
        self,
    ) -> tuple[OptionContract, ...]:
        """Return valued contracts only."""

        return tuple(
            item.contract
            for item in self.items
        )


# ==========================================================
# Workflow
# ==========================================================


class MarketValuationWorkflow:
    """
    Connect market data with OptionPipeline.

    Responsibilities
    ----------------
    - Normalize external market records.
    - Validate normalized contracts.
    - Select contracts for valuation.
    - Build pipeline parameters.
    - Execute the valuation pipeline.
    - Return a stable workflow result.

    The workflow deliberately keeps market-data reading
    separate from valuation logic.
    """

    def __init__(
        self,
        adapter: MarketDataAdapter | None = None,
        pipeline: OptionPipeline | None = None,
    ) -> None:

        self.adapter = (
            adapter
            if adapter is not None
            else MarketDataAdapter()
        )

        self.pipeline = (
            pipeline
            if pipeline is not None
            else OptionPipeline()
        )

    # ======================================================
    # Market Data
    # ======================================================

    def normalize_records(
        self,
        records: Iterable[Mapping[str, Any]],
    ) -> list[OptionContract]:
        """
        Normalize external records into OptionContract objects.
        """

        return self.adapter.normalize_records(
            records
        )

    def normalize_record(
        self,
        record: Mapping[str, Any],
    ) -> OptionContract:
        """
        Normalize one external market record.
        """

        return self.adapter.normalize_record(
            record
        )

    # ======================================================
    # Contract Selection
    # ======================================================

    @staticmethod
    def select_contracts(
        contracts: Iterable[OptionContract],
        direction: OptionDirection | str | None = None,
        min_volume: int = 0,
        top_n: int | None = None,
    ) -> list[OptionContract]:
        """
        Select contracts for valuation.

        Parameters
        ----------
        contracts:
            Normalized option contracts.

        direction:
            Optional CALL / PUT filter.

        min_volume:
            Minimum trading volume.

        top_n:
            Optional maximum number of contracts.

        Returns
        -------
        list[OptionContract]
            Selected contracts ordered by volume
            descending.
        """

        if min_volume < 0:
            raise ValueError(
                "最低成交量不能小于 0。"
            )

        if top_n is not None and top_n <= 0:
            raise ValueError(
                "TOP N 必须大于 0。"
            )

        normalized_direction: (
            OptionDirection | None
        )

        if direction is None:

            normalized_direction = None

        elif isinstance(
            direction,
            OptionDirection,
        ):

            normalized_direction = direction

        else:

            try:

                normalized_direction = (
                    OptionDirection(
                        str(direction)
                        .strip()
                        .upper()
                    )
                )

            except ValueError as exc:

                raise ValueError(
                    "无效的期权方向。"
                ) from exc

        selected = [
            contract
            for contract in contracts
            if contract.volume >= min_volume
        ]

        if normalized_direction is not None:

            selected = [
                contract
                for contract in selected
                if contract.direction
                == normalized_direction
            ]

        selected.sort(
            key=lambda contract: (
                contract.volume,
                contract.open_interest,
            ),
            reverse=True,
        )

        if top_n is not None:

            selected = selected[
                :top_n
            ]

        return selected

    # ======================================================
    # Pipeline Parameter Construction
    # ======================================================

    @staticmethod
    def build_pipeline_parameters(
        contract: OptionContract,
        underlying_price: float,
        days: int,
        volatility: float,
        risk_free_rate: float = 0.025,
    ) -> PipelineParameters:
        """
        Build PipelineParameters for one contract.
        """

        return PipelineParameters(
            underlying_price=float(
                underlying_price
            ),
            days=int(
                days
            ),
            volatility=float(
                volatility
            ),
            risk_free_rate=float(
                risk_free_rate
            ),
            option=contract,
        )

    # ======================================================
    # Single Contract Valuation
    # ======================================================

    def evaluate_contract(
        self,
        contract: OptionContract,
        underlying_price: float,
        days: int,
        volatility: float,
        risk_free_rate: float = 0.025,
    ) -> ValuationResult:
        """
        Evaluate one normalized option contract.

        Returns the underlying ValuationResult directly.
        """

        parameters = (
            self.build_pipeline_parameters(
                contract=contract,
                underlying_price=underlying_price,
                days=days,
                volatility=volatility,
                risk_free_rate=risk_free_rate,
            )
        )

        return self.pipeline.evaluate_contract(
            contract=contract,
            parameters=parameters,
        )

    # ======================================================
    # Batch Valuation
    # ======================================================

    def evaluate_contracts(
        self,
        contracts: Iterable[OptionContract],
        underlying_price: float,
        days: int,
        volatility: float,
        risk_free_rate: float = 0.025,
    ) -> MarketValuationWorkflowResult:
        """
        Evaluate multiple normalized contracts.
        """

        contract_list = list(
            contracts
        )

        items: list[
            MarketValuationItem
        ] = []

        for contract in contract_list:

            result = self.evaluate_contract(
                contract=contract,
                underlying_price=underlying_price,
                days=days,
                volatility=volatility,
                risk_free_rate=risk_free_rate,
            )

            items.append(
                MarketValuationItem(
                    contract=contract,
                    result=result,
                )
            )

        return MarketValuationWorkflowResult(
            items=tuple(
                items
            ),
            total_contracts=len(
                contract_list
            ),
            selected_contracts=len(
                contract_list
            ),
            successful_count=len(
                items
            ),
        )

    # ======================================================
    # Complete Workflow
    # ======================================================

    def run(
        self,
        records: Iterable[Mapping[str, Any]],
        underlying_price: float,
        days: int,
        volatility: float,
        risk_free_rate: float = 0.025,
        direction: OptionDirection | str | None = None,
        min_volume: int = 0,
        top_n: int | None = None,
    ) -> MarketValuationWorkflowResult:
        """
        Execute the complete market valuation workflow.

        Workflow
        --------
        1. Normalize external records.
        2. Select contracts.
        3. Build pipeline parameters.
        4. Evaluate selected contracts.
        5. Return unified results.
        """

        contracts = self.normalize_records(
            records
        )

        selected = self.select_contracts(
            contracts=contracts,
            direction=direction,
            min_volume=min_volume,
            top_n=top_n,
        )

        valuation_result = (
            self.evaluate_contracts(
                contracts=selected,
                underlying_price=underlying_price,
                days=days,
                volatility=volatility,
                risk_free_rate=risk_free_rate,
            )
        )

        return MarketValuationWorkflowResult(
            items=valuation_result.items,
            total_contracts=len(
                contracts
            ),
            selected_contracts=len(
                selected
            ),
            successful_count=(
                valuation_result.successful_count
            ),
        )


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "MarketValuationItem",
    "MarketValuationWorkflow",
    "MarketValuationWorkflowResult",
]