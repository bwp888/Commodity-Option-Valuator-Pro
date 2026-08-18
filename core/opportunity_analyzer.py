"""
Commodity Option Valuator Pro
=============================

Opportunity Analyzer.

Commit 0017
-----------

Analyzes ranked option opportunities and converts
ranking results into strategy-oriented signals.

Workflow
--------
ValuationResult
        ↓
MarketRankingEngine
        ↓
RankingResult
        ↓
OpportunityAnalyzer
        ↓
OpportunitySignal
        ↓
Strategy-Oriented Analysis

Author : Simon
Version : 0.5.1
Python : 3.12
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.market_ranking import (
    RankingItem,
    RankingResult,
)


# ==========================================================
# Constants
# ==========================================================

ACTION_BUY = "BUY"
ACTION_WATCH = "WATCH"
ACTION_AVOID = "AVOID"

LEVEL_STRONG = "STRONG"
LEVEL_MEDIUM = "MEDIUM"
LEVEL_WEAK = "WEAK"


# ==========================================================
# Opportunity Signal
# ==========================================================


@dataclass(frozen=True)
class OpportunitySignal:
    """
    Strategy-oriented analysis result for one ranked option.

    Attributes
    ----------
    symbol:
        Option symbol.

    direction:
        Option direction, represented by the original
        OptionDirection value string.

    score:
        Original market ranking score.

    level:
        Opportunity strength.

    action:
        Strategy-oriented action.

    reason:
        Human-readable explanation.
    """

    symbol: str

    direction: str

    score: float

    level: str

    action: str

    reason: str


# ==========================================================
# Opportunity Analysis Result
# ==========================================================


@dataclass(frozen=True)
class OpportunityAnalysisResult:
    """
    Complete opportunity analysis result.

    Attributes
    ----------
    signals:
        Analyzed opportunity signals.

    total_count:
        Number of analyzed ranking items.
    """

    signals: tuple[OpportunitySignal, ...]

    total_count: int

    @property
    def top_signal(
        self,
    ) -> OpportunitySignal | None:
        """
        Return the highest-ranked opportunity signal.
        """

        if not self.signals:
            return None

        return self.signals[0]

    @property
    def buy_signals(
        self,
    ) -> tuple[OpportunitySignal, ...]:
        """
        Return BUY signals.
        """

        return tuple(
            signal
            for signal in self.signals
            if signal.action == ACTION_BUY
        )

    @property
    def watch_signals(
        self,
    ) -> tuple[OpportunitySignal, ...]:
        """
        Return WATCH signals.
        """

        return tuple(
            signal
            for signal in self.signals
            if signal.action == ACTION_WATCH
        )

    @property
    def avoid_signals(
        self,
    ) -> tuple[OpportunitySignal, ...]:
        """
        Return AVOID signals.
        """

        return tuple(
            signal
            for signal in self.signals
            if signal.action == ACTION_AVOID
        )


# ==========================================================
# Opportunity Analyzer
# ==========================================================


class OpportunityAnalyzer:
    """
    Analyze ranked option opportunities.

    The analyzer deliberately operates above the valuation
    and ranking layers.

    It does not modify:
        - OptionContract
        - ValuationResult
        - RankingItem
        - RankingResult

    Classification
    --------------

    STRONG
        High ranking score.

    MEDIUM
        Moderate ranking score.

    WEAK
        Low ranking score.

    Action mapping
    --------------

    STRONG -> BUY
    MEDIUM -> WATCH
    WEAK   -> AVOID

    Thresholds are configurable so that later strategy
    modules can replace the default rules without changing
    the public result structures.
    """

    def __init__(
        self,
        strong_threshold: float = 3.0,
        medium_threshold: float = 1.0,
    ) -> None:
        """
        Initialize analyzer.

        Parameters
        ----------
        strong_threshold:
            Minimum score for STRONG classification.

        medium_threshold:
            Minimum score for MEDIUM classification.

        Raises
        ------
        ValueError
            If thresholds are invalid.
        """

        if strong_threshold <= medium_threshold:
            raise ValueError(
                "strong_threshold must be greater than "
                "medium_threshold"
            )

        self.strong_threshold = float(
            strong_threshold
        )

        self.medium_threshold = float(
            medium_threshold
        )

    # ======================================================
    # Classification
    # ======================================================

    def classify_level(
        self,
        score: float,
    ) -> str:
        """
        Classify opportunity strength from ranking score.
        """

        value = float(
            score
        )

        if value >= self.strong_threshold:
            return LEVEL_STRONG

        if value >= self.medium_threshold:
            return LEVEL_MEDIUM

        return LEVEL_WEAK

    # ======================================================
    # Action
    # ======================================================

    @staticmethod
    def level_to_action(
        level: str,
    ) -> str:
        """
        Convert opportunity level into action.
        """

        normalized = str(
            level
        ).upper()

        if normalized == LEVEL_STRONG:
            return ACTION_BUY

        if normalized == LEVEL_MEDIUM:
            return ACTION_WATCH

        if normalized == LEVEL_WEAK:
            return ACTION_AVOID

        raise ValueError(
            f"invalid opportunity level: {level}"
        )

    # ======================================================
    # Reason
    # ======================================================

    @staticmethod
    def build_reason(
        level: str,
        action: str,
        score: float,
    ) -> str:
        """
        Build a human-readable explanation.
        """

        if level == LEVEL_STRONG:
            return (
                f"排名得分 {score:.4f}，机会强度较高，"
                "建议重点关注。"
            )

        if level == LEVEL_MEDIUM:
            return (
                f"排名得分 {score:.4f}，机会强度中等，"
                "建议继续观察。"
            )

        if level == LEVEL_WEAK:
            return (
                f"排名得分 {score:.4f}，机会强度较弱，"
                "当前不建议优先考虑。"
            )

        return (
            f"排名得分 {score:.4f}，"
            f"当前信号为 {action}。"
        )

    # ======================================================
    # Analyze One Item
    # ======================================================

    def analyze_item(
        self,
        item: RankingItem,
    ) -> OpportunitySignal:
        """
        Analyze one RankingItem.

        Parameters
        ----------
        item:
            Ranked opportunity.

        Returns
        -------
        OpportunitySignal
            Strategy-oriented signal.
        """

        if not isinstance(
            item,
            RankingItem,
        ):
            raise TypeError(
                "item must be a RankingItem"
            )

        score = float(
            item.score
        )

        level = self.classify_level(
            score
        )

        action = self.level_to_action(
            level
        )

        direction = item.contract.direction

        direction_value = getattr(
            direction,
            "value",
            str(direction),
        )

        reason = self.build_reason(
            level=level,
            action=action,
            score=score,
        )

        return OpportunitySignal(
            symbol=item.contract.symbol,
            direction=str(
                direction_value
            ),
            score=score,
            level=level,
            action=action,
            reason=reason,
        )

    # ======================================================
    # Analyze Ranking Result
    # ======================================================

    def analyze_result(
        self,
        result: RankingResult,
    ) -> OpportunityAnalysisResult:
        """
        Analyze a complete RankingResult.

        The original ranking order is preserved.
        """

        if not isinstance(
            result,
            RankingResult,
        ):
            raise TypeError(
                "result must be a RankingResult"
            )

        signals = tuple(
            self.analyze_item(
                item
            )
            for item in result.items
        )

        return OpportunityAnalysisResult(
            signals=signals,
            total_count=len(
                signals
            ),
        )

    # ======================================================
    # Analyze Items
    # ======================================================

    def analyze_items(
        self,
        items: Iterable[RankingItem],
    ) -> OpportunityAnalysisResult:
        """
        Analyze an iterable of RankingItem objects.

        Generators are supported.
        """

        signals = tuple(
            self.analyze_item(
                item
            )
            for item in items
        )

        return OpportunityAnalysisResult(
            signals=signals,
            total_count=len(
                signals
            ),
        )


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "ACTION_AVOID",
    "ACTION_BUY",
    "ACTION_WATCH",
    "LEVEL_MEDIUM",
    "LEVEL_STRONG",
    "LEVEL_WEAK",
    "OpportunityAnalysisResult",
    "OpportunityAnalyzer",
    "OpportunitySignal",
]