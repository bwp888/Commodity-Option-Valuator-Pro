"""
Commodity Option Valuator Pro
=============================

Recommendation Engine.

Commit 0018
-----------

Converts opportunity-analysis results into
structured recommendation results.

Workflow
--------
Market Data
    ↓
Valuation
    ↓
Ranking
    ↓
Opportunity Analysis
    ↓
Recommendation Engine
    ↓
RecommendationResult

Author : Simon
Version : 0.6.0
Python : 3.12
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


# ==========================================================
# Recommendation Action
# ==========================================================


class RecommendationAction(str, Enum):
    """
    Recommended action for an opportunity.
    """

    BUY = "BUY"
    SELL = "SELL"
    WATCH = "WATCH"
    REJECT = "REJECT"


# ==========================================================
# Recommendation Level
# ==========================================================


class RecommendationLevel(str, Enum):
    """
    Recommendation quality level.
    """

    A = "A"
    B = "B"
    C = "C"
    D = "D"


# ==========================================================
# Recommendation
# ==========================================================


@dataclass(frozen=True)
class Recommendation:
    """
    Structured recommendation for one opportunity.

    Attributes
    ----------
    symbol:
        Option contract symbol.

    action:
        Recommended action.

    level:
        Recommendation quality level.

    score:
        Opportunity score.

    risk_score:
        Risk score.

    reason:
        Human-readable recommendation reason.
    """

    symbol: str

    action: RecommendationAction

    level: RecommendationLevel

    score: float

    risk_score: float

    reason: str


# ==========================================================
# Recommendation Result
# ==========================================================


@dataclass(frozen=True)
class RecommendationResult:
    """
    Collection of recommendation results.
    """

    recommendations: tuple[Recommendation, ...]

    total_count: int

    @property
    def top(self) -> Recommendation | None:
        """
        Return the highest-priority recommendation.
        """

        if not self.recommendations:
            return None

        return self.recommendations[0]

    @property
    def symbols(self) -> tuple[str, ...]:
        """
        Return recommendation symbols.
        """

        return tuple(
            item.symbol
            for item in self.recommendations
        )

    def top_n(
        self,
        n: int,
    ) -> tuple[Recommendation, ...]:
        """
        Return the first N recommendations.
        """

        if n <= 0:
            raise ValueError(
                "n must be greater than zero"
            )

        return self.recommendations[:n]


# ==========================================================
# Recommendation Engine
# ==========================================================


class RecommendationEngine:
    """
    Convert opportunity-analysis records into
    structured recommendations.

    The engine deliberately accepts simple dictionaries
    instead of depending on the OpportunityAnalyzer
    implementation details.

    Required input fields
    ---------------------
    symbol:
        Option symbol.

    score:
        Opportunity score.

    risk_score:
        Risk score.

    direction:
        Option direction.

        Supported values include:

        CALL
        PUT

    Decision rules
    --------------
    High score + acceptable risk:
        BUY / SELL

    Moderate score:
        WATCH

    Low score or excessive risk:
        REJECT

    Thresholds are configurable through the constructor.
    """

    def __init__(
        self,
        strong_score: float = 2.0,
        watch_score: float = 0.0,
        max_risk_score: float = 7.0,
    ) -> None:
        """
        Initialize recommendation engine.

        Parameters
        ----------
        strong_score:
            Minimum score required for an active
            BUY or SELL recommendation.

        watch_score:
            Minimum score required to remain under
            observation instead of being rejected.

        max_risk_score:
            Maximum acceptable risk score.
        """

        if strong_score <= watch_score:
            raise ValueError(
                "strong_score must be greater than watch_score"
            )

        if max_risk_score < 0:
            raise ValueError(
                "max_risk_score must not be negative"
            )

        self.strong_score = float(
            strong_score
        )

        self.watch_score = float(
            watch_score
        )

        self.max_risk_score = float(
            max_risk_score
        )

    # ======================================================
    # Direction
    # ======================================================

    @staticmethod
    def _normalize_direction(
        direction: object,
    ) -> str:
        """
        Normalize option direction.

        Raises
        ------
        ValueError
            If the direction is invalid.
        """

        if hasattr(
            direction,
            "value",
        ):
            value = getattr(
                direction,
                "value",
            )
        else:
            value = direction

        normalized = str(
            value
        ).strip().upper()

        if normalized not in {
            "CALL",
            "PUT",
        }:
            raise ValueError(
                "invalid option direction"
            )

        return normalized

    # ======================================================
    # Action
    # ======================================================

    @staticmethod
    def _active_action(
        direction: str,
    ) -> RecommendationAction:
        """
        Convert option direction into active recommendation.
        """

        if direction == "CALL":
            return RecommendationAction.BUY

        return RecommendationAction.SELL

    # ======================================================
    # Level
    # ======================================================

    def _level(
        self,
        score: float,
        risk_score: float,
    ) -> RecommendationLevel:
        """
        Determine recommendation level.
        """

        if (
            score >= self.strong_score
            and risk_score <= self.max_risk_score
        ):
            return RecommendationLevel.A

        if (
            score >= self.watch_score
            and risk_score <= self.max_risk_score
        ):
            return RecommendationLevel.B

        if risk_score <= self.max_risk_score:
            return RecommendationLevel.C

        return RecommendationLevel.D

    # ======================================================
    # Reason
    # ======================================================

    def _reason(
        self,
        action: RecommendationAction,
        level: RecommendationLevel,
        score: float,
        risk_score: float,
    ) -> str:
        """
        Build a deterministic recommendation reason.
        """

        if action == RecommendationAction.BUY:
            return (
                "CALL opportunity has sufficient score "
                "and acceptable risk"
            )

        if action == RecommendationAction.SELL:
            return (
                "PUT opportunity has sufficient score "
                "and acceptable risk"
            )

        if action == RecommendationAction.WATCH:
            return (
                "Opportunity score is positive but "
                "does not meet the active recommendation threshold"
            )

        if (
            risk_score > self.max_risk_score
        ):
            return (
                "Risk score exceeds the maximum "
                "acceptable risk threshold"
            )

        if score < self.watch_score:
            return (
                "Opportunity score is below the "
                "minimum observation threshold"
            )

        return (
            f"Recommendation level {level.value} "
            "does not qualify for an active position"
        )

    # ======================================================
    # Single Recommendation
    # ======================================================

    def recommend(
        self,
        opportunity: dict[str, object],
    ) -> Recommendation:
        """
        Convert one opportunity record into a recommendation.

        Required keys
        -------------
        symbol
        score
        risk_score
        direction
        """

        if not isinstance(
            opportunity,
            dict,
        ):
            raise TypeError(
                "opportunity must be a dictionary"
            )

        required_fields = (
            "symbol",
            "score",
            "risk_score",
            "direction",
        )

        for field in required_fields:
            if field not in opportunity:
                raise ValueError(
                    f"missing opportunity field: {field}"
                )

        symbol = str(
            opportunity["symbol"]
        ).strip()

        if not symbol:
            raise ValueError(
                "symbol must not be empty"
            )

        score = float(
            opportunity["score"]
        )

        risk_score = float(
            opportunity["risk_score"]
        )

        direction = self._normalize_direction(
            opportunity["direction"]
        )

        level = self._level(
            score,
            risk_score,
        )

        if (
            risk_score > self.max_risk_score
        ):
            action = RecommendationAction.REJECT

        elif score >= self.strong_score:
            action = self._active_action(
                direction
            )

        elif score >= self.watch_score:
            action = RecommendationAction.WATCH

        else:
            action = RecommendationAction.REJECT

        reason = self._reason(
            action,
            level,
            score,
            risk_score,
        )

        return Recommendation(
            symbol=symbol,
            action=action,
            level=level,
            score=score,
            risk_score=risk_score,
            reason=reason,
        )

    # ======================================================
    # Batch Recommendation
    # ======================================================

    def recommend_all(
        self,
        opportunities: Iterable[
            dict[str, object]
        ],
    ) -> RecommendationResult:
        """
        Convert multiple opportunities.

        Results are sorted by:

        1. Recommendation level
        2. Score
        3. Lower risk
        """

        recommendations = [
            self.recommend(
                opportunity
            )
            for opportunity in opportunities
        ]

        level_priority = {
            RecommendationLevel.A: 0,
            RecommendationLevel.B: 1,
            RecommendationLevel.C: 2,
            RecommendationLevel.D: 3,
        }

        recommendations.sort(
            key=lambda item: (
                level_priority[item.level],
                -item.score,
                item.risk_score,
            )
        )

        return RecommendationResult(
            recommendations=tuple(
                recommendations
            ),
            total_count=len(
                recommendations
            ),
        )

    # ======================================================
    # Top N
    # ======================================================

    def recommend_top(
        self,
        opportunities: Iterable[
            dict[str, object]
        ],
        n: int,
    ) -> RecommendationResult:
        """
        Recommend and return the top N opportunities.
        """

        if n <= 0:
            raise ValueError(
                "n must be greater than zero"
            )

        result = self.recommend_all(
            opportunities
        )

        return RecommendationResult(
            recommendations=(
                result.recommendations[:n]
            ),
            total_count=min(
                n,
                result.total_count,
            ),
        )


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "Recommendation",
    "RecommendationAction",
    "RecommendationEngine",
    "RecommendationLevel",
    "RecommendationResult",
]