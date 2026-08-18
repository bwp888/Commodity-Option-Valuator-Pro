"""
Commodity Option Valuator Pro
=============================

Market Ranking Engine.

Commit 0016
------------

Rank valuation opportunities from
market valuation workflow results.

Workflow
--------
ValuationResult
        ↓
MarketRankingEngine
        ↓
RankingResult
        ↓
Top N Opportunities

Author : Simon
Version : 0.5.0
Python : 3.12
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from models.option_scanner import (
    OptionContract,
)

from core.valuation_engine import (
    ValuationResult,
)


# ==========================================================
# Ranking Item
# ==========================================================


@dataclass(frozen=True)
class RankingItem:
    """
    One ranked option opportunity.

    Attributes
    ----------
    contract:
        Option contract information.

    valuation:
        Valuation result.

    score:
        Ranking score.
    """

    contract: OptionContract

    valuation: ValuationResult

    score: float


# ==========================================================
# Ranking Result
# ==========================================================


@dataclass(frozen=True)
class RankingResult:
    """
    Ranking output.

    Attributes
    ----------
    items:
        Ranked opportunities.

    total_count:
        Total ranked contracts.
    """

    items: tuple[RankingItem, ...]

    total_count: int

    @property
    def top_symbol(self) -> str | None:
        """
        Return highest ranked symbol.
        """

        if not self.items:
            return None

        return self.items[0].contract.symbol

    @property
    def scores(self) -> tuple[float, ...]:
        """
        Return ranking scores.
        """

        return tuple(
            item.score
            for item in self.items
        )

    def top(
        self,
        n: int,
    ) -> tuple[RankingItem, ...]:
        """
        Return top N items.
        """

        if n <= 0:
            raise ValueError(
                "n must be greater than zero"
            )

        return self.items[:n]


# ==========================================================
# Ranking Engine
# ==========================================================


class MarketRankingEngine:
    """
    Rank option valuation opportunities.

    Ranking logic
    -------------
    Default score:

        valuation difference
        -
        risk penalty
        +
        liquidity factor


    Higher score means better opportunity.
    """

    def __init__(
        self,
        risk_weight: float = 1.0,
        liquidity_weight: float = 0.001,
    ) -> None:

        if risk_weight < 0:
            raise ValueError(
                "risk_weight must not be negative"
            )

        if liquidity_weight < 0:
            raise ValueError(
                "liquidity_weight must not be negative"
            )

        self.risk_weight = float(
            risk_weight
        )

        self.liquidity_weight = float(
            liquidity_weight
        )

    # ======================================================
    # Score
    # ======================================================

    def calculate_score(
        self,
        contract: OptionContract,
        valuation: ValuationResult,
    ) -> float:
        """
        Calculate ranking score.

        Formula:

        difference
        - risk_score * weight
        + liquidity * weight
        """

        difference = float(
            valuation.difference
        )

        risk_penalty = (
            float(
                valuation.risk_score
            )
            * self.risk_weight
        )

        liquidity = (
            contract.volume
            +
            contract.open_interest
        )

        liquidity_bonus = (
            float(liquidity)
            *
            self.liquidity_weight
        )

        return (
            difference
            - risk_penalty
            + liquidity_bonus
        )

    # ======================================================
    # Rank
    # ======================================================

    def rank(
        self,
        items: Iterable[
            tuple[
                OptionContract,
                ValuationResult,
            ]
        ],
        top_n: int | None = None,
    ) -> RankingResult:
        """
        Rank valuation results.

        Parameters
        ----------
        items:
            Contract and valuation pairs.

        top_n:
            Optional maximum result count.

        Returns
        -------
        RankingResult
        """

        if (
            top_n is not None
            and top_n <= 0
        ):
            raise ValueError(
                "top_n must be greater than zero"
            )

        ranked: list[RankingItem] = []

        for contract, valuation in items:

            score = self.calculate_score(
                contract,
                valuation,
            )

            ranked.append(
                RankingItem(
                    contract=contract,
                    valuation=valuation,
                    score=score,
                )
            )

        ranked.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        if top_n is not None:
            ranked = ranked[:top_n]

        return RankingResult(
            items=tuple(ranked),
            total_count=len(ranked),
        )

    # ======================================================
    # Convenience
    # ======================================================

    def rank_from_result(
        self,
        contracts: Iterable[OptionContract],
        valuations: Iterable[ValuationResult],
        top_n: int | None = None,
    ) -> RankingResult:
        """
        Rank directly from workflow outputs.
        """

        pairs = zip(
            contracts,
            valuations,
        )

        return self.rank(
            pairs,
            top_n=top_n,
        )


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "MarketRankingEngine",
    "RankingItem",
    "RankingResult",
]