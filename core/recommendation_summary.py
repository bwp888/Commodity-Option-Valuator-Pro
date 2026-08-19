"""
Commodity Option Valuator Pro
=============================

Recommendation Summary.

Commit 0020
-----------

Provides a stable summary layer above the recommendation engine.

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
Recommendation Workflow
    ↓
Recommendation Summary

The summary layer is intentionally read-only. It does not change
recommendation rules or recommendation ordering.

Author : Simon
Version : 0.6.2
Python : 3.12
"""

from __future__ import annotations

from dataclasses import dataclass

from core.recommendation_engine import (
    Recommendation,
    RecommendationAction,
    RecommendationLevel,
    RecommendationResult,
)

from core.recommendation_workflow import (
    RecommendationWorkflowResult,
)


# ==========================================================
# Recommendation Summary
# ==========================================================


@dataclass(frozen=True)
class RecommendationSummary:
    """
    Stable summary of recommendation results.

    Attributes
    ----------
    total_count:
        Total number of recommendation records.

    buy_count:
        Number of BUY recommendations.

    sell_count:
        Number of SELL recommendations.

    watch_count:
        Number of WATCH recommendations.

    reject_count:
        Number of REJECT recommendations.

    level_a_count:
        Number of A-level recommendations.

    level_b_count:
        Number of B-level recommendations.

    level_c_count:
        Number of C-level recommendations.

    level_d_count:
        Number of D-level recommendations.

    top:
        Highest-priority recommendation, if available.
    """

    total_count: int

    buy_count: int

    sell_count: int

    watch_count: int

    reject_count: int

    level_a_count: int

    level_b_count: int

    level_c_count: int

    level_d_count: int

    top: Recommendation | None

    @property
    def active_count(self) -> int:
        """
        Return the number of active BUY or SELL recommendations.
        """

        return (
            self.buy_count
            + self.sell_count
        )

    @property
    def has_active_recommendation(self) -> bool:
        """
        Return whether at least one active recommendation exists.
        """

        return self.active_count > 0

    @property
    def action_counts(self) -> dict[str, int]:
        """
        Return action counts as a stable dictionary.

        Enum values are converted to strings so this result can be
        consumed directly by UI and reporting layers.
        """

        return {
            RecommendationAction.BUY.value: self.buy_count,
            RecommendationAction.SELL.value: self.sell_count,
            RecommendationAction.WATCH.value: self.watch_count,
            RecommendationAction.REJECT.value: self.reject_count,
        }

    @property
    def level_counts(self) -> dict[str, int]:
        """
        Return recommendation-level counts.
        """

        return {
            RecommendationLevel.A.value: self.level_a_count,
            RecommendationLevel.B.value: self.level_b_count,
            RecommendationLevel.C.value: self.level_c_count,
            RecommendationLevel.D.value: self.level_d_count,
        }

    @property
    def top_symbol(self) -> str | None:
        """
        Return the symbol of the top recommendation.
        """

        if self.top is None:
            return None

        return self.top.symbol

    @property
    def top_action(self) -> RecommendationAction | None:
        """
        Return the action of the top recommendation.
        """

        if self.top is None:
            return None

        return self.top.action

    @property
    def top_level(self) -> RecommendationLevel | None:
        """
        Return the level of the top recommendation.
        """

        if self.top is None:
            return None

        return self.top.level


# ==========================================================
# Recommendation Summary Builder
# ==========================================================


class RecommendationSummaryBuilder:
    """
    Build RecommendationSummary objects.

    The builder only reads existing recommendation results.
    It never changes recommendation decisions.
    """

    @staticmethod
    def _validate_result(
        result: RecommendationResult,
    ) -> None:
        """
        Validate a RecommendationResult.
        """

        if not isinstance(
            result,
            RecommendationResult,
        ):
            raise TypeError(
                "result must be a RecommendationResult"
            )

    @classmethod
    def from_result(
        cls,
        result: RecommendationResult,
    ) -> RecommendationSummary:
        """
        Build a summary from RecommendationResult.
        """

        cls._validate_result(
            result
        )

        buy_count = 0
        sell_count = 0
        watch_count = 0
        reject_count = 0

        level_a_count = 0
        level_b_count = 0
        level_c_count = 0
        level_d_count = 0

        for recommendation in result.recommendations:
            if not isinstance(
                recommendation,
                Recommendation,
            ):
                raise TypeError(
                    "result.recommendations must contain Recommendation"
                )

            if recommendation.action == RecommendationAction.BUY:
                buy_count += 1

            elif recommendation.action == RecommendationAction.SELL:
                sell_count += 1

            elif recommendation.action == RecommendationAction.WATCH:
                watch_count += 1

            elif recommendation.action == RecommendationAction.REJECT:
                reject_count += 1

            if recommendation.level == RecommendationLevel.A:
                level_a_count += 1

            elif recommendation.level == RecommendationLevel.B:
                level_b_count += 1

            elif recommendation.level == RecommendationLevel.C:
                level_c_count += 1

            elif recommendation.level == RecommendationLevel.D:
                level_d_count += 1

            else:
                raise ValueError(
                    "recommendation has invalid level"
                )

        if result.total_count != len(
            result.recommendations
        ):
            raise ValueError(
                "recommendation result total_count "
                "does not match recommendations length"
            )

        return RecommendationSummary(
            total_count=result.total_count,
            buy_count=buy_count,
            sell_count=sell_count,
            watch_count=watch_count,
            reject_count=reject_count,
            level_a_count=level_a_count,
            level_b_count=level_b_count,
            level_c_count=level_c_count,
            level_d_count=level_d_count,
            top=result.top,
        )

    @classmethod
    def from_workflow(
        cls,
        workflow_result: RecommendationWorkflowResult,
    ) -> RecommendationSummary:
        """
        Build a summary from RecommendationWorkflowResult.
        """

        if not isinstance(
            workflow_result,
            RecommendationWorkflowResult,
        ):
            raise TypeError(
                "workflow_result must be a "
                "RecommendationWorkflowResult"
            )

        return cls.from_result(
            workflow_result.recommendations
        )


# ==========================================================
# Public Convenience Functions
# ==========================================================


def summarize_recommendations(
    result: RecommendationResult,
) -> RecommendationSummary:
    """
    Build a summary from RecommendationResult.
    """

    return RecommendationSummaryBuilder.from_result(
        result
    )


def summarize_workflow(
    workflow_result: RecommendationWorkflowResult,
) -> RecommendationSummary:
    """
    Build a summary from RecommendationWorkflowResult.
    """

    return RecommendationSummaryBuilder.from_workflow(
        workflow_result
    )


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "RecommendationSummary",
    "RecommendationSummaryBuilder",
    "summarize_recommendations",
    "summarize_workflow",
]