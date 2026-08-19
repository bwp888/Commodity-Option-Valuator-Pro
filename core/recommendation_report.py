"""
Commodity Option Valuator Pro
=============================

Recommendation Report Model.

Commit 0021
-----------

Provides a stable report-oriented data model built on top of
the recommendation presentation and summary layers.

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
Recommendation Presentation
    ↓
Recommendation Summary
    ↓
Recommendation Report

Author : Simon
Version : 0.6.3
Python : 3.12
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from core.recommendation_presentation import (
    RecommendationPresentation,
    RecommendationPresentationResult,
)
from core.recommendation_summary import (
    RecommendationSummary,
)


# ==========================================================
# Recommendation Report Item
# ==========================================================


@dataclass(frozen=True)
class RecommendationReportItem:
    """
    Report-ready representation of one recommendation.

    The report item intentionally keeps the presentation
    fields required by downstream UI and report exporters.
    """

    symbol: str

    action: str

    level: str

    score: float

    risk_score: float

    reason: str

    risk_warning: str | None

    action_title: str

    action_description: str

    level_title: str

    level_description: str

    @classmethod
    def from_presentation(
        cls,
        item: RecommendationPresentation,
    ) -> RecommendationReportItem:
        """
        Create a report item from one presentation item.
        """

        if not isinstance(
            item,
            RecommendationPresentation,
        ):
            raise TypeError(
                "item must be a RecommendationPresentation"
            )

        return cls(
            symbol=item.symbol,
            action=item.action.value,
            level=item.level.value,
            score=float(item.score),
            risk_score=float(item.risk_score),
            reason=item.reason,
            risk_warning=item.risk_warning,
            action_title=item.action_title,
            action_description=item.action_description,
            level_title=item.level_title,
            level_description=item.level_description,
        )


# ==========================================================
# Recommendation Report
# ==========================================================


@dataclass(frozen=True)
class RecommendationReport:
    """
    Complete recommendation report model.

    This is a pure data model. It contains no UI, file I/O,
    plotting, or export implementation.

    Attributes
    ----------
    title:
        Human-readable report title.

    generated_at:
        Report creation timestamp.

    ranked_count:
        Number of ranked opportunities entering the workflow.

    summary:
        Aggregate recommendation statistics.

    items:
        Report-ready recommendation items.
    """

    title: str

    generated_at: datetime

    ranked_count: int

    summary: RecommendationSummary

    items: tuple[RecommendationReportItem, ...]

    # ======================================================
    # Basic Properties
    # ======================================================

    @property
    def total_count(self) -> int:
        """
        Return the number of recommendations in the report.
        """

        return len(
            self.items
        )

    @property
    def symbols(self) -> tuple[str, ...]:
        """
        Return report recommendation symbols.
        """

        return tuple(
            item.symbol
            for item in self.items
        )

    @property
    def top(
        self,
    ) -> RecommendationReportItem | None:
        """
        Return the highest-priority report item.
        """

        if not self.items:
            return None

        return self.items[0]

    @property
    def has_active_recommendation(self) -> bool:
        """
        Return whether at least one BUY or SELL exists.
        """

        return any(
            item.action in {
                "BUY",
                "SELL",
            }
            for item in self.items
        )

    @property
    def has_high_risk(self) -> bool:
        """
        Return whether the report contains a risk warning.
        """

        return any(
            item.risk_warning is not None
            for item in self.items
        )

    # ======================================================
    # Selection
    # ======================================================

    def top_n(
        self,
        n: int,
    ) -> tuple[RecommendationReportItem, ...]:
        """
        Return the first N report items.
        """

        if n <= 0:
            raise ValueError(
                "n must be greater than zero"
            )

        return self.items[:n]

    # ======================================================
    # Construction
    # ======================================================

    @classmethod
    def from_presentation(
        cls,
        result: RecommendationPresentationResult,
        *,
        title: str = "Commodity Option Recommendation Report",
        generated_at: datetime | None = None,
    ) -> RecommendationReport:
        """
        Build a report from a presentation result.

        Parameters
        ----------
        result:
            Recommendation presentation result.

        title:
            Report title.

        generated_at:
            Optional report timestamp. If omitted, the current
            local datetime is used.
        """

        if not isinstance(
            result,
            RecommendationPresentationResult,
        ):
            raise TypeError(
                "result must be a "
                "RecommendationPresentationResult"
            )

        normalized_title = str(
            title
        ).strip()

        if not normalized_title:
            raise ValueError(
                "title must not be empty"
            )

        if result.ranked_count < 0:
            raise ValueError(
                "ranked_count must not be negative"
            )

        timestamp = (
            generated_at
            if generated_at is not None
            else datetime.now()
        )

        if not isinstance(
            timestamp,
            datetime,
        ):
            raise TypeError(
                "generated_at must be a datetime"
            )

        if not isinstance(
            result.summary,
            RecommendationSummary,
        ):
            raise TypeError(
                "result.summary must be a "
                "RecommendationSummary"
            )

        items = tuple(
            RecommendationReportItem.from_presentation(
                item
            )
            for item in result.items
        )

        return cls(
            title=normalized_title,
            generated_at=timestamp,
            ranked_count=int(
                result.ranked_count
            ),
            summary=result.summary,
            items=items,
        )

    @classmethod
    def empty(
        cls,
        *,
        title: str = "Commodity Option Recommendation Report",
        generated_at: datetime | None = None,
    ) -> RecommendationReport:
        """
        Create an empty recommendation report.

        The method is useful for UI initialization and for
        markets where no eligible contracts are available.
        """

        normalized_title = str(
            title
        ).strip()

        if not normalized_title:
            raise ValueError(
                "title must not be empty"
            )

        timestamp = (
            generated_at
            if generated_at is not None
            else datetime.now()
        )

        if not isinstance(
            timestamp,
            datetime,
        ):
            raise TypeError(
                "generated_at must be a datetime"
            )

        summary = RecommendationSummary(
            total_count=0,
            buy_count=0,
            sell_count=0,
            watch_count=0,
            reject_count=0,
            level_a_count=0,
            level_b_count=0,
            level_c_count=0,
            level_d_count=0,
            highest_score=None,
            lowest_risk_score=None,
            top=None,
        )

        return cls(
            title=normalized_title,
            generated_at=timestamp,
            ranked_count=0,
            summary=summary,
            items=(),
        )

    # ======================================================
    # Filtering
    # ======================================================

    def filter_actions(
        self,
        actions: Iterable[str],
    ) -> tuple[RecommendationReportItem, ...]:
        """
        Return items matching the requested actions.

        Action matching is case-insensitive.
        """

        normalized_actions = {
            str(action).strip().upper()
            for action in actions
        }

        if not normalized_actions:
            return ()

        valid_actions = {
            "BUY",
            "SELL",
            "WATCH",
            "REJECT",
        }

        invalid_actions = (
            normalized_actions
            - valid_actions
        )

        if invalid_actions:
            raise ValueError(
                "invalid recommendation action"
            )

        return tuple(
            item
            for item in self.items
            if item.action in normalized_actions
        )

    def filter_levels(
        self,
        levels: Iterable[str],
    ) -> tuple[RecommendationReportItem, ...]:
        """
        Return items matching the requested levels.

        Level matching is case-insensitive.
        """

        normalized_levels = {
            str(level).strip().upper()
            for level in levels
        }

        if not normalized_levels:
            return ()

        valid_levels = {
            "A",
            "B",
            "C",
            "D",
        }

        invalid_levels = (
            normalized_levels
            - valid_levels
        )

        if invalid_levels:
            raise ValueError(
                "invalid recommendation level"
            )

        return tuple(
            item
            for item in self.items
            if item.level in normalized_levels
        )


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "RecommendationReport",
    "RecommendationReportItem",
]