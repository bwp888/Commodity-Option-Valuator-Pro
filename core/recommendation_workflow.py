"""
Commodity Option Valuator Pro
=============================

Recommendation Workflow.

Commit 0019
------------

Connects opportunity analysis with recommendation generation.

Workflow
--------
Market Data
    ↓
Market Valuation Workflow
    ↓
Market Ranking
    ↓
Opportunity Analysis
    ↓
Recommendation Engine
    ↓
RecommendationResult

Author : Simon
Version : 0.6.1
Python : 3.12
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from core.market_ranking import (
    RankingItem,
    RankingResult,
)

from core.market_valuation_workflow import (
    MarketValuationWorkflow,
    MarketValuationWorkflowResult,
)

from core.opportunity_analyzer import (
    OpportunityAnalysisResult,
    OpportunityAnalyzer,
)

from core.recommendation_engine import (
    RecommendationEngine,
    RecommendationResult,
)

from models.option_scanner import (
    OptionDirection,
)


# ==========================================================
# Workflow Result
# ==========================================================


@dataclass(frozen=True)
class RecommendationWorkflowResult:
    """
    Complete recommendation workflow result.

    Attributes
    ----------
    analysis:
        Opportunity analysis result.

    recommendations:
        Structured recommendation result.

    ranked_count:
        Number of ranked opportunities entering the workflow.
    """

    analysis: OpportunityAnalysisResult

    recommendations: RecommendationResult

    ranked_count: int

    @property
    def top(self):
        """
        Return the highest-priority recommendation.
        """

        return self.recommendations.top

    @property
    def total_count(self) -> int:
        """
        Return the number of recommendations.
        """

        return self.recommendations.total_count

    @property
    def symbols(self) -> tuple[str, ...]:
        """
        Return recommendation symbols.
        """

        return self.recommendations.symbols


# ==========================================================
# Recommendation Workflow
# ==========================================================


class RecommendationWorkflow:
    """
    Orchestrate ranking, opportunity analysis, and
    recommendation generation.

    Responsibilities
    ----------------
    1. Accept an existing RankingResult.
    2. Analyze ranked opportunities.
    3. Preserve ranking information.
    4. Provide risk information to the recommendation layer.
    5. Generate RecommendationResult.
    6. Optionally execute the complete market valuation
       workflow before ranking and recommendation.

    The workflow deliberately does not modify:
        - MarketValuationWorkflow
        - MarketRankingEngine
        - OpportunityAnalyzer
        - RecommendationEngine
        - RankingResult
        - OpportunityAnalysisResult
        - RecommendationResult
    """

    def __init__(
        self,
        valuation_workflow: MarketValuationWorkflow | None = None,
        opportunity_analyzer: OpportunityAnalyzer | None = None,
        recommendation_engine: RecommendationEngine | None = None,
    ) -> None:
        """
        Initialize recommendation workflow.

        Parameters
        ----------
        valuation_workflow:
            Optional market valuation workflow.

        opportunity_analyzer:
            Optional opportunity analyzer.

        recommendation_engine:
            Optional recommendation engine.
        """

        self.valuation_workflow = (
            valuation_workflow
            if valuation_workflow is not None
            else MarketValuationWorkflow()
        )

        self.opportunity_analyzer = (
            opportunity_analyzer
            if opportunity_analyzer is not None
            else OpportunityAnalyzer()
        )

        self.recommendation_engine = (
            recommendation_engine
            if recommendation_engine is not None
            else RecommendationEngine()
        )

    # ======================================================
    # Analysis
    # ======================================================

    def analyze_result(
        self,
        ranking_result: RankingResult,
    ) -> OpportunityAnalysisResult:
        """
        Analyze an existing ranking result.

        The ranking result itself is never modified.
        """

        if not isinstance(
            ranking_result,
            RankingResult,
        ):
            raise TypeError(
                "ranking_result must be a RankingResult"
            )

        return self.opportunity_analyzer.analyze_result(
            ranking_result
        )

    # ======================================================
    # Recommendation Input Construction
    # ======================================================

    @staticmethod
    def _build_opportunities(
        ranking_result: RankingResult,
        analysis: OpportunityAnalysisResult,
    ) -> list[dict[str, object]]:
        """
        Build recommendation-engine input records.

        RecommendationEngine intentionally accepts simple
        dictionaries. The risk score is recovered from the
        original RankingItem valuation so that the workflow
        does not require changing OpportunitySignal.

        The positional relationship between RankingResult.items
        and OpportunityAnalysisResult.signals is preserved by
        OpportunityAnalyzer.
        """

        if not isinstance(
            ranking_result,
            RankingResult,
        ):
            raise TypeError(
                "ranking_result must be a RankingResult"
            )

        if not isinstance(
            analysis,
            OpportunityAnalysisResult,
        ):
            raise TypeError(
                "analysis must be an OpportunityAnalysisResult"
            )

        if len(ranking_result.items) != len(
            analysis.signals
        ):
            raise ValueError(
                "ranking result and analysis result "
                "must contain the same number of items"
            )

        opportunities: list[
            dict[str, object]
        ] = []

        for item, signal in zip(
            ranking_result.items,
            analysis.signals,
        ):
            if not isinstance(
                item,
                RankingItem,
            ):
                raise TypeError(
                    "ranking_result.items must contain RankingItem"
                )

            opportunities.append(
                {
                    "symbol": signal.symbol,
                    "score": signal.score,
                    "risk_score": float(
                        item.valuation.risk_score
                    ),
                    "direction": signal.direction,
                }
            )

        return opportunities

    # ======================================================
    # Recommendation
    # ======================================================

    def recommend_result(
        self,
        ranking_result: RankingResult,
    ) -> RecommendationWorkflowResult:
        """
        Analyze and recommend an existing ranking result.

        Workflow
        --------
        RankingResult
            ↓
        OpportunityAnalysisResult
            ↓
        RecommendationResult
        """

        if not isinstance(
            ranking_result,
            RankingResult,
        ):
            raise TypeError(
                "ranking_result must be a RankingResult"
            )

        analysis = self.analyze_result(
            ranking_result
        )

        opportunities = self._build_opportunities(
            ranking_result,
            analysis,
        )

        recommendations = (
            self.recommendation_engine.recommend_all(
                opportunities
            )
        )

        return RecommendationWorkflowResult(
            analysis=analysis,
            recommendations=recommendations,
            ranked_count=len(
                ranking_result.items
            ),
        )

    # ======================================================
    # Direct Ranking Items
    # ======================================================

    def recommend_items(
        self,
        items: Iterable[RankingItem],
    ) -> RecommendationWorkflowResult:
        """
        Analyze and recommend ranking items directly.

        Generators are supported.

        Every item must be a RankingItem.
        """

        ranking_items = tuple(items)

        for item in ranking_items:
            if not isinstance(
                item,
                RankingItem,
            ):
                raise TypeError(
                    "ranking_result.items must contain RankingItem"
                )

        ranking_result = RankingResult(
            items=ranking_items,
            total_count=len(
                ranking_items
            ),
        )

        return self.recommend_result(
            ranking_result
        )

    # ======================================================
    # Top N Recommendation
    # ======================================================

    def recommend_top(
        self,
        ranking_result: RankingResult,
        n: int,
    ) -> RecommendationWorkflowResult:
        """
        Return recommendations for the top N ranked items.

        ``n`` is applied to the ranking result before
        opportunity analysis and recommendation generation.
        """

        if n <= 0:
            raise ValueError(
                "n must be greater than zero"
            )

        if not isinstance(
            ranking_result,
            RankingResult,
        ):
            raise TypeError(
                "ranking_result must be a RankingResult"
            )

        selected_items = ranking_result.items[:n]

        selected_result = RankingResult(
            items=selected_items,
            total_count=len(
                selected_items
            ),
        )

        return self.recommend_result(
            selected_result
        )

    # ======================================================
    # Market Valuation + Ranking
    # ======================================================

    def rank_market_data(
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
        Execute market valuation and ranking.

        This method delegates valuation and ranking to the
        existing MarketValuationWorkflow.
        """

        return self.valuation_workflow.run_and_rank(
            records=records,
            underlying_price=underlying_price,
            days=days,
            volatility=volatility,
            risk_free_rate=risk_free_rate,
            direction=direction,
            min_volume=min_volume,
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
    ) -> RecommendationWorkflowResult:
        """
        Execute the complete recommendation workflow.

        Workflow
        --------
        1. Normalize market records.
        2. Select contracts.
        3. Evaluate contracts.
        4. Rank valuation opportunities.
        5. Analyze opportunities.
        6. Generate recommendations.

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
        RecommendationWorkflowResult
            Complete recommendation workflow result.

        Notes
        -----
        ``top_n`` is passed to MarketValuationWorkflow.run_and_rank()
        and therefore applies at the ranking stage.
        """

        ranking_result = self.rank_market_data(
            records=records,
            underlying_price=underlying_price,
            days=days,
            volatility=volatility,
            risk_free_rate=risk_free_rate,
            direction=direction,
            min_volume=min_volume,
            top_n=top_n,
        )

        return self.recommend_result(
            ranking_result
        )

    # ======================================================
    # Existing Valuation Result
    # ======================================================

    def recommend_valuation_result(
        self,
        valuation_result: MarketValuationWorkflowResult,
        top_n: int | None = None,
    ) -> RecommendationWorkflowResult:
        """
        Continue from an already completed valuation workflow.

        This method avoids re-running valuation.
        """

        if not isinstance(
            valuation_result,
            MarketValuationWorkflowResult,
        ):
            raise TypeError(
                "valuation_result must be a "
                "MarketValuationWorkflowResult"
            )

        ranking_result = (
            self.valuation_workflow.rank_result(
                valuation_result,
                top_n=top_n,
            )
        )

        return self.recommend_result(
            ranking_result
        )


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "RecommendationWorkflow",
    "RecommendationWorkflowResult",
]