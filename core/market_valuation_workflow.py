"""
Commodity Option Valuator Pro
=============================

Market Valuation Workflow.

Commit 0016
------------

Connect market data with the option valuation pipeline
and market ranking engine.

Workflow
--------
Market Data
    ↓
MarketDataAdapter
    ↓
OptionContract
    ↓
Contract Selection
    ↓
OptionPipeline
    ↓
ValuationResult
    ↓
MarketRankingEngine
    ↓
RankingResult

Author : Simon
Version : 0.5.0
Python : 3.12
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from core.market_ranking import (
    MarketRankingEngine,
    RankingResult,
)

from core.option_pipeline import (
    OptionPipeline,
    PipelineParameters,
)

from data.market_data_adapter import (
    MarketDataAdapter,
)

from models.option_scanner import (
    OptionContract,
    OptionDirection,
)

from core.valuation_engine import (
    ValuationResult,
)


# ==========================================================
# Workflow Result
# ==========================================================


@dataclass(frozen=True)
class MarketValuationItem:
    """
    One market contract with its valuation result.

    Attributes
    ----------
    contract:
        Normalized option contract.

    result:
        Valuation result produced by the option pipeline.
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
        """
        Return valuation results only.
        """

        return tuple(
            item.result
            for item in self.items
        )

    @property
    def contracts(
        self,
    ) -> tuple[OptionContract, ...]:
        """
        Return valued contracts only.
        """

        return tuple(
            item.contract
            for item in self.items
        )


# ==========================================================
# Workflow
# ==========================================================


class MarketValuationWorkflow:
    """
    Connect market data with valuation and ranking engines.

    Responsibilities
    ----------------
    1. Normalize external market records.
    2. Validate normalized contracts.
    3. Select contracts for valuation.
    4. Build pipeline parameters.
    5. Execute the valuation pipeline.
    6. Rank valuation opportunities.
    7. Return stable workflow results.

    The workflow deliberately keeps market-data reading,
    valuation logic, ranking logic, and UI logic separated.
    """

    def __init__(
        self,
        adapter: MarketDataAdapter | None = None,
        pipeline: OptionPipeline | None = None,
        ranking_engine: MarketRankingEngine | None = None,
    ) -> None:
        """
        Initialize market valuation workflow.

        Parameters
        ----------
        adapter:
            Optional market data adapter.

        pipeline:
            Optional option valuation pipeline.

        ranking_engine:
            Optional market ranking engine.

        Notes
        -----
        Default components are created automatically when
        corresponding arguments are omitted.
        """

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

        self.ranking_engine = (
            ranking_engine
            if ranking_engine is not None
            else MarketRankingEngine()
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

        Parameters
        ----------
        records:
            External market records.

        Returns
        -------
        list[OptionContract]
            Normalized contracts.
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

        Parameters
        ----------
        record:
            External market record.

        Returns
        -------
        OptionContract
            Normalized contract.
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
            Selected contracts ordered by volume descending.

        Raises
        ------
        ValueError
            If direction, min_volume, or top_n is invalid.
        """

        if min_volume < 0:
            raise ValueError(
                "最低成交量不能小于 0"
            )

        if top_n is not None and top_n <= 0:
            raise ValueError(
                "TOP N 必须大于零"
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
                        str(
                            direction
                        )
                        .strip()
                        .upper()
                    )
                )

            except ValueError as exc:

                raise ValueError(
                    "无效的期权方向"
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

        The contract is preserved inside PipelineParameters
        through the optional ``option`` field.
        """

        return PipelineParameters(
            underlying_price=float(
                underlying_price
            ),
            volatility=float(
                volatility
            ),
            days=int(
                days
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

        Parameters
        ----------
        contract:
            Normalized option contract.

        underlying_price:
            Current underlying futures price.

        days:
            Remaining calendar days.

        volatility:
            Annualized volatility.

        risk_free_rate:
            Annualized risk-free rate.

        Returns
        -------
        ValuationResult
            Valuation result for the contract.
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

        Parameters
        ----------
        contracts:
            Normalized option contracts.

        underlying_price:
            Current underlying futures price.

        days:
            Remaining calendar days.

        volatility:
            Annualized volatility.

        risk_free_rate:
            Annualized risk-free rate.

        Returns
        -------
        MarketValuationWorkflowResult
            Structured valuation results.
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
    # Ranking
    # ======================================================

    def rank_result(
        self,
        result: MarketValuationWorkflowResult,
        top_n: int | None = None,
    ) -> RankingResult:
        """
        Rank a completed valuation workflow result.

        Parameters
        ----------
        result:
            Completed market valuation workflow result.

        top_n:
            Optional maximum number of ranked opportunities.

        Returns
        -------
        RankingResult
            Ranked market opportunities.

        Notes
        -----
        The original workflow result is never modified.
        """

        pairs = (
            (
                item.contract,
                self._extract_valuation(
                    item.result
                ),
            )
            for item in result.items
        )

        return self.ranking_engine.rank(
            pairs,
            top_n=top_n,
        )

    def rank_items(
        self,
        items: Iterable[MarketValuationItem],
        top_n: int | None = None,
    ) -> RankingResult:
        """
        Rank workflow items directly.

        Parameters
        ----------
        items:
            Iterable of MarketValuationItem objects.

        top_n:
            Optional maximum number of ranked opportunities.

        Returns
        -------
        RankingResult
            Ranked market opportunities.
        """

        pairs = (
            (
                item.contract,
                self._extract_valuation(
                    item.result
                ),
            )
            for item in items
        )

        return self.ranking_engine.rank(
            pairs,
            top_n=top_n,
        )

    @staticmethod
    def _extract_valuation(
        result: ValuationResult,
    ) -> ValuationResult:
        """
        Return the valuation result associated with one
        MarketValuationItem.

        Current pipeline contract
        -------------------------
        OptionPipeline.evaluate_contract() returns one
        ValuationResult directly.

        Therefore no nested ``valuations`` collection exists
        at this workflow layer.

        This method is intentionally kept as a small boundary
        adapter so ranking code does not need to know how the
        workflow stores valuation results.
        """

        if not isinstance(
            result,
            ValuationResult,
        ):
            raise TypeError(
                "MarketValuationItem.result must be "
                "a ValuationResult"
            )

        return result

    # ======================================================
    # Complete Valuation + Ranking Workflow
    # ======================================================

    def run_and_rank(
        self,
        records: Iterable[Mapping[str, Any]],
        underlying_price: float,
        days: int,
        volatility: float,
        risk_free_rate: float = 0.025,
        direction: OptionDirection | str | None = None,
        min_volume: int = 0,
        top_n: int | None = None,
    ) -> RankingResult:
        """
        Execute valuation workflow and ranking workflow.

        Workflow
        --------
        1. Normalize market records.
        2. Select contracts.
        3. Evaluate selected contracts.
        4. Rank valuation opportunities.
        5. Return RankingResult.

        Parameters
        ----------
        records:
            External market records.

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
            Optional maximum ranked result count.

        Returns
        -------
        RankingResult
            Ranked opportunities.

        Notes
        -----
        ``top_n`` is intentionally applied at the ranking
        stage here. The normal ``run()`` API keeps its own
        selection-stage ``top_n`` behavior unchanged.
        """

        valuation_result = self.run(
            records=records,
            underlying_price=underlying_price,
            days=days,
            volatility=volatility,
            risk_free_rate=risk_free_rate,
            direction=direction,
            min_volume=min_volume,
        )

        return self.rank_result(
            valuation_result,
            top_n=top_n,
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

        Notes
        -----
        ``top_n`` applies to contract selection before valuation.
        Ranking-specific TOP N is handled by ``run_and_rank``.
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