"""
Commodity Option Valuator Pro
=============================

Recommendation Presentation Layer.

Commit 0020
------------

Converts RecommendationWorkflowResult into
UI/report-friendly presentation structures.

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

Author : Simon
Version : 0.6.2
Python : 3.12
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.opportunity_analyzer import (
    OpportunityAnalysisResult,
)

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
# Presentation Action
# ==========================================================


class PresentationAction(str, Enum):
    """
    Presentation-level action.

    These values are intentionally stable because they may
    be consumed by UI and report layers.
    """

    BUY = "BUY"
    SELL = "SELL"
    WATCH = "WATCH"
    REJECT = "REJECT"


# ==========================================================
# Presentation Level
# ==========================================================


class PresentationLevel(str, Enum):
    """
    Presentation-level recommendation quality.
    """

    A = "A"
    B = "B"
    C = "C"
    D = "D"


# ==========================================================
# Action Display
# ==========================================================


@dataclass(frozen=True)
class ActionDisplay:
    """
    UI-friendly action information.
    """

    action: PresentationAction
    title: str
    description: str


# ==========================================================
# Level Display
# ==========================================================


@dataclass(frozen=True)
class LevelDisplay:
    """
    UI-friendly recommendation level information.
    """

    level: PresentationLevel
    title: str
    description: str


# ==========================================================
# Recommendation Presentation
# ==========================================================


@dataclass(frozen=True)
class RecommendationPresentation:
    """
    UI/report representation of one recommendation.
    """

    symbol: str

    action: PresentationAction

    action_title: str

    action_description: str

    level: PresentationLevel

    level_title: str

    level_description: str

    score: float

    risk_score: float

    reason: str

    risk_warning: str | None


# ==========================================================
# Recommendation Summary
# ==========================================================


@dataclass(frozen=True)
class RecommendationSummary:
    """
    Aggregate recommendation statistics.
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

    highest_score: float | None

    lowest_risk_score: float | None


# ==========================================================
# Presentation Result
# ==========================================================


@dataclass(frozen=True)
class RecommendationPresentationResult:
    """
    Complete presentation-layer result.
    """

    items: tuple[
        RecommendationPresentation,
        ...,
    ]

    summary: RecommendationSummary

    ranked_count: int

    @property
    def top(
        self,
    ) -> RecommendationPresentation | None:
        """
        Return the highest-priority presentation item.
        """

        if not self.items:
            return None

        return self.items[0]

    @property
    def total_count(self) -> int:
        """
        Return the number of presented recommendations.
        """

        return len(
            self.items
        )

    @property
    def symbols(self) -> tuple[str, ...]:
        """
        Return presented recommendation symbols.
        """

        return tuple(
            item.symbol
            for item in self.items
        )

    def top_n(
        self,
        n: int,
    ) -> tuple[
        RecommendationPresentation,
        ...,
    ]:
        """
        Return the first N presentation items.
        """

        if n <= 0:
            raise ValueError(
                "n must be greater than zero"
            )

        return self.items[:n]


# ==========================================================
# Recommendation Presenter
# ==========================================================


class RecommendationPresenter:
    """
    Convert recommendation workflow results into
    presentation-friendly immutable structures.

    This class deliberately contains no UI framework
    dependency.
    """

    # ======================================================
    # Action Mapping
    # ======================================================

    @staticmethod
    def action_display(
        action: RecommendationAction | str,
    ) -> ActionDisplay:
        """
        Convert recommendation action into display metadata.
        """

        normalized = (
            RecommendationPresenter._normalize_action(
                action
            )
        )

        mapping = {
            PresentationAction.BUY: ActionDisplay(
                action=PresentationAction.BUY,
                title="BUY",
                description=(
                    "Active bullish recommendation for "
                    "the selected CALL opportunity."
                ),
            ),
            PresentationAction.SELL: ActionDisplay(
                action=PresentationAction.SELL,
                title="SELL",
                description=(
                    "Active bearish recommendation for "
                    "the selected PUT opportunity."
                ),
            ),
            PresentationAction.WATCH: ActionDisplay(
                action=PresentationAction.WATCH,
                title="WATCH",
                description=(
                    "Opportunity remains observable but "
                    "does not meet the active recommendation "
                    "threshold."
                ),
            ),
            PresentationAction.REJECT: ActionDisplay(
                action=PresentationAction.REJECT,
                title="REJECT",
                description=(
                    "Opportunity does not currently satisfy "
                    "the recommendation conditions."
                ),
            ),
        }

        return mapping[normalized]

    # ======================================================
    # Level Mapping
    # ======================================================

    @staticmethod
    def level_display(
        level: RecommendationLevel | str,
    ) -> LevelDisplay:
        """
        Convert recommendation level into display metadata.
        """

        normalized = (
            RecommendationPresenter._normalize_level(
                level
            )
        )

        mapping = {
            PresentationLevel.A: LevelDisplay(
                level=PresentationLevel.A,
                title="A",
                description=(
                    "Strong opportunity with acceptable risk."
                ),
            ),
            PresentationLevel.B: LevelDisplay(
                level=PresentationLevel.B,
                title="B",
                description=(
                    "Moderate opportunity suitable for monitoring."
                ),
            ),
            PresentationLevel.C: LevelDisplay(
                level=PresentationLevel.C,
                title="C",
                description=(
                    "Low-score opportunity with limited "
                    "recommendation strength."
                ),
            ),
            PresentationLevel.D: LevelDisplay(
                level=PresentationLevel.D,
                title="D",
                description=(
                    "Risk level exceeds the acceptable threshold."
                ),
            ),
        }

        return mapping[normalized]

    # ======================================================
    # Normalization
    # ======================================================

    @staticmethod
    def _normalize_action(
        action: RecommendationAction | str,
    ) -> PresentationAction:
        """
        Normalize recommendation action.
        """

        if isinstance(
            action,
            RecommendationAction,
        ):
            value = action.value
        else:
            value = str(
                action
            ).strip().upper()

        try:
            return PresentationAction(
                value
            )
        except ValueError as exc:
            raise ValueError(
                f"invalid recommendation action: {value}"
            ) from exc

    @staticmethod
    def _normalize_level(
        level: RecommendationLevel | str,
    ) -> PresentationLevel:
        """
        Normalize recommendation level.
        """

        if isinstance(
            level,
            RecommendationLevel,
        ):
            value = level.value
        else:
            value = str(
                level
            ).strip().upper()

        try:
            return PresentationLevel(
                value
            )
        except ValueError as exc:
            raise ValueError(
                f"invalid recommendation level: {value}"
            ) from exc

    # ======================================================
    # Risk Warning
    # ======================================================

    @staticmethod
    def _risk_warning(
        recommendation: Recommendation,
    ) -> str | None:
        """
        Build a risk warning for presentation.

        The recommendation engine remains responsible for
        the actual decision. This method only creates
        presentation text.
        """

        if (
            recommendation.action
            == RecommendationAction.REJECT
        ):
            if recommendation.risk_score > 7.0:
                return (
                    "High risk: risk score exceeds the "
                    "default acceptable threshold."
                )

            if recommendation.score < 0.0:
                return (
                    "Low opportunity score: current "
                    "opportunity strength is insufficient."
                )

            return (
                "Recommendation rejected by the current "
                "decision rules."
            )

        if recommendation.risk_score >= 6.0:
            return (
                "Risk alert: recommendation is active but "
                "risk score is relatively high."
            )

        if recommendation.risk_score >= 4.0:
            return (
                "Risk notice: monitor risk exposure carefully."
            )

        return None

    # ======================================================
    # Single Recommendation
    # ======================================================

    def present(
        self,
        recommendation: Recommendation,
    ) -> RecommendationPresentation:
        """
        Convert one Recommendation into presentation data.
        """

        if not isinstance(
            recommendation,
            Recommendation,
        ):
            raise TypeError(
                "recommendation must be a Recommendation"
            )

        action = self.action_display(
            recommendation.action
        )

        level = self.level_display(
            recommendation.level
        )

        return RecommendationPresentation(
            symbol=recommendation.symbol,
            action=action.action,
            action_title=action.title,
            action_description=action.description,
            level=level.level,
            level_title=level.title,
            level_description=level.description,
            score=float(
                recommendation.score
            ),
            risk_score=float(
                recommendation.risk_score
            ),
            reason=recommendation.reason,
            risk_warning=self._risk_warning(
                recommendation
            ),
        )

    # ======================================================
    # Summary
    # ======================================================

    @staticmethod
    def summarize(
        result: RecommendationResult,
    ) -> RecommendationSummary:
        """
        Build aggregate recommendation statistics.
        """

        if not isinstance(
            result,
            RecommendationResult,
        ):
            raise TypeError(
                "result must be a RecommendationResult"
            )

        recommendations = result.recommendations

        buy_count = sum(
            item.action == RecommendationAction.BUY
            for item in recommendations
        )

        sell_count = sum(
            item.action == RecommendationAction.SELL
            for item in recommendations
        )

        watch_count = sum(
            item.action == RecommendationAction.WATCH
            for item in recommendations
        )

        reject_count = sum(
            item.action == RecommendationAction.REJECT
            for item in recommendations
        )

        level_a_count = sum(
            item.level == RecommendationLevel.A
            for item in recommendations
        )

        level_b_count = sum(
            item.level == RecommendationLevel.B
            for item in recommendations
        )

        level_c_count = sum(
            item.level == RecommendationLevel.C
            for item in recommendations
        )

        level_d_count = sum(
            item.level == RecommendationLevel.D
            for item in recommendations
        )

        scores = tuple(
            float(
                item.score
            )
            for item in recommendations
        )

        risks = tuple(
            float(
                item.risk_score
            )
            for item in recommendations
        )

        return RecommendationSummary(
            total_count=len(
                recommendations
            ),
            buy_count=buy_count,
            sell_count=sell_count,
            watch_count=watch_count,
            reject_count=reject_count,
            level_a_count=level_a_count,
            level_b_count=level_b_count,
            level_c_count=level_c_count,
            level_d_count=level_d_count,
            highest_score=(
                max(scores)
                if scores
                else None
            ),
            lowest_risk_score=(
                min(risks)
                if risks
                else None
            ),
        )

    # ======================================================
    # Result Presentation
    # ======================================================

    def present_result(
        self,
        result: RecommendationResult,
        ranked_count: int | None = None,
    ) -> RecommendationPresentationResult:
        """
        Convert a RecommendationResult into presentation data.
        """

        if not isinstance(
            result,
            RecommendationResult,
        ):
            raise TypeError(
                "result must be a RecommendationResult"
            )

        items = tuple(
            self.present(
                recommendation
            )
            for recommendation in result.recommendations
        )

        summary = self.summarize(
            result
        )

        if ranked_count is None:
            ranked_count = result.total_count

        if ranked_count < 0:
            raise ValueError(
                "ranked_count must not be negative"
            )

        return RecommendationPresentationResult(
            items=items,
            summary=summary,
            ranked_count=int(
                ranked_count
            ),
        )

    # ======================================================
    # Workflow Presentation
    # ======================================================

    def present_workflow(
        self,
        result: RecommendationWorkflowResult,
    ) -> RecommendationPresentationResult:
        """
        Convert a complete recommendation workflow result.
        """

        if not isinstance(
            result,
            RecommendationWorkflowResult,
        ):
            raise TypeError(
                "result must be a RecommendationWorkflowResult"
            )

        return self.present_result(
            result.recommendations,
            ranked_count=result.ranked_count,
        )


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "ActionDisplay",
    "LevelDisplay",
    "PresentationAction",
    "PresentationLevel",
    "RecommendationPresentation",
    "RecommendationPresentationResult",
    "RecommendationPresenter",
    "RecommendationSummary",
]