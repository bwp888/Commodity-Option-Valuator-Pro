"""
Commodity Option Valuator Pro
=============================

Tests for Opportunity Analyzer.

Commit 0017
-----------

Author : Simon
Version : 0.5.1
"""

from __future__ import annotations

import pytest

from core.market_ranking import (
    RankingItem,
    RankingResult,
)

from core.opportunity_analyzer import (
    ACTION_AVOID,
    ACTION_BUY,
    ACTION_WATCH,
    LEVEL_MEDIUM,
    LEVEL_STRONG,
    LEVEL_WEAK,
    OpportunityAnalysisResult,
    OpportunityAnalyzer,
    OpportunitySignal,
)

from core.valuation_engine import (
    ValuationResult,
)

from models.option_scanner import (
    OptionContract,
    OptionDirection,
)


# ==========================================================
# Test Data
# ==========================================================


def make_contract(
    symbol: str = "TEST-C-100",
    direction: OptionDirection = OptionDirection.CALL,
) -> OptionContract:
    """Create a deterministic option contract."""

    return OptionContract(
        symbol=symbol,
        direction=direction,
        strike=100.0,
        price=5.0,
        volume=500,
        open_interest=1000,
        bid=4.9,
        ask=5.1,
    )


def make_valuation(
    symbol: str = "TEST-C-100",
) -> ValuationResult:
    """Create a deterministic valuation result."""

    return ValuationResult(
        symbol=symbol,
        direction=OptionDirection.CALL,
        premium=5.0,
        theoretical_price=8.0,
        delta=0.5,
        gamma=0.02,
        theta=-0.05,
        vega=0.10,
        difference=3.0,
        risk_score=1.0,
    )


def make_item(
    symbol: str = "TEST-C-100",
    direction: OptionDirection = OptionDirection.CALL,
    score: float = 3.0,
) -> RankingItem:
    """Create a deterministic ranking item."""

    return RankingItem(
        contract=make_contract(
            symbol=symbol,
            direction=direction,
        ),
        valuation=make_valuation(
            symbol=symbol,
        ),
        score=score,
    )


def make_result() -> RankingResult:
    """Create deterministic ranking result."""

    return RankingResult(
        items=(
            make_item(
                symbol="TEST-C-100",
                score=5.0,
            ),
            make_item(
                symbol="TEST-C-105",
                score=2.0,
            ),
            make_item(
                symbol="TEST-C-110",
                score=0.5,
            ),
        ),
        total_count=3,
    )


# ==========================================================
# Import
# ==========================================================


def test_analyzer_import() -> None:
    """Analyzer should be importable."""

    analyzer = OpportunityAnalyzer()

    assert analyzer is not None


def test_signal_is_available() -> None:
    """OpportunitySignal should be available."""

    signal = OpportunitySignal(
        symbol="TEST-C-100",
        direction="CALL",
        score=5.0,
        level=LEVEL_STRONG,
        action=ACTION_BUY,
        reason="test",
    )

    assert signal.symbol == "TEST-C-100"
    assert signal.direction == "CALL"
    assert signal.score == 5.0


def test_analysis_result_is_available() -> None:
    """OpportunityAnalysisResult should be available."""

    result = OpportunityAnalysisResult(
        signals=(),
        total_count=0,
    )

    assert result.total_count == 0
    assert result.top_signal is None


# ==========================================================
# Initialization
# ==========================================================


def test_default_thresholds() -> None:
    """Default thresholds should be stored."""

    analyzer = OpportunityAnalyzer()

    assert analyzer.strong_threshold == 3.0
    assert analyzer.medium_threshold == 1.0


def test_custom_thresholds() -> None:
    """Custom thresholds should be supported."""

    analyzer = OpportunityAnalyzer(
        strong_threshold=5.0,
        medium_threshold=2.0,
    )

    assert analyzer.strong_threshold == 5.0
    assert analyzer.medium_threshold == 2.0


def test_rejects_invalid_threshold_order() -> None:
    """Strong threshold must exceed medium threshold."""

    with pytest.raises(ValueError):
        OpportunityAnalyzer(
            strong_threshold=1.0,
            medium_threshold=2.0,
        )


def test_rejects_equal_thresholds() -> None:
    """Equal thresholds should be rejected."""

    with pytest.raises(ValueError):
        OpportunityAnalyzer(
            strong_threshold=2.0,
            medium_threshold=2.0,
        )


# ==========================================================
# Level Classification
# ==========================================================


def test_classify_strong() -> None:
    """High score should be STRONG."""

    analyzer = OpportunityAnalyzer()

    assert analyzer.classify_level(
        3.0
    ) == LEVEL_STRONG

    assert analyzer.classify_level(
        10.0
    ) == LEVEL_STRONG


def test_classify_medium() -> None:
    """Middle score should be MEDIUM."""

    analyzer = OpportunityAnalyzer()

    assert analyzer.classify_level(
        1.0
    ) == LEVEL_MEDIUM

    assert analyzer.classify_level(
        2.99
    ) == LEVEL_MEDIUM


def test_classify_weak() -> None:
    """Low score should be WEAK."""

    analyzer = OpportunityAnalyzer()

    assert analyzer.classify_level(
        0.99
    ) == LEVEL_WEAK

    assert analyzer.classify_level(
        -10.0
    ) == LEVEL_WEAK


# ==========================================================
# Action Mapping
# ==========================================================


def test_level_to_action_strong() -> None:
    """STRONG should map to BUY."""

    assert (
        OpportunityAnalyzer.level_to_action(
            LEVEL_STRONG
        )
        == ACTION_BUY
    )


def test_level_to_action_medium() -> None:
    """MEDIUM should map to WATCH."""

    assert (
        OpportunityAnalyzer.level_to_action(
            LEVEL_MEDIUM
        )
        == ACTION_WATCH
    )


def test_level_to_action_weak() -> None:
    """WEAK should map to AVOID."""

    assert (
        OpportunityAnalyzer.level_to_action(
            LEVEL_WEAK
        )
        == ACTION_AVOID
    )


def test_level_to_action_is_case_insensitive() -> None:
    """Level conversion should accept lowercase values."""

    assert (
        OpportunityAnalyzer.level_to_action(
            "strong"
        )
        == ACTION_BUY
    )


def test_level_to_action_rejects_invalid_level() -> None:
    """Invalid level should raise ValueError."""

    with pytest.raises(ValueError):
        OpportunityAnalyzer.level_to_action(
            "INVALID"
        )


# ==========================================================
# Single Item Analysis
# ==========================================================


def test_analyze_strong_item() -> None:
    """Strong item should produce BUY signal."""

    analyzer = OpportunityAnalyzer()

    signal = analyzer.analyze_item(
        make_item(
            score=5.0
        )
    )

    assert isinstance(
        signal,
        OpportunitySignal,
    )

    assert signal.symbol == "TEST-C-100"
    assert signal.direction == "CALL"
    assert signal.score == 5.0
    assert signal.level == LEVEL_STRONG
    assert signal.action == ACTION_BUY
    assert signal.reason


def test_analyze_medium_item() -> None:
    """Medium item should produce WATCH signal."""

    analyzer = OpportunityAnalyzer()

    signal = analyzer.analyze_item(
        make_item(
            score=2.0
        )
    )

    assert signal.level == LEVEL_MEDIUM
    assert signal.action == ACTION_WATCH


def test_analyze_weak_item() -> None:
    """Weak item should produce AVOID signal."""

    analyzer = OpportunityAnalyzer()

    signal = analyzer.analyze_item(
        make_item(
            score=0.5
        )
    )

    assert signal.level == LEVEL_WEAK
    assert signal.action == ACTION_AVOID


def test_analyze_put_direction() -> None:
    """PUT direction should be preserved."""

    analyzer = OpportunityAnalyzer()

    signal = analyzer.analyze_item(
        make_item(
            symbol="TEST-P-100",
            direction=OptionDirection.PUT,
            score=4.0,
        )
    )

    assert signal.symbol == "TEST-P-100"
    assert signal.direction == "PUT"


def test_analyze_preserves_score() -> None:
    """Ranking score should be preserved exactly."""

    analyzer = OpportunityAnalyzer()

    signal = analyzer.analyze_item(
        make_item(
            score=1.234567
        )
    )

    assert signal.score == pytest.approx(
        1.234567
    )


def test_analyze_item_rejects_invalid_type() -> None:
    """Invalid item type should be rejected."""

    analyzer = OpportunityAnalyzer()

    with pytest.raises(TypeError):
        analyzer.analyze_item(
            "invalid"  # type: ignore[arg-type]
        )


# ==========================================================
# Result Analysis
# ==========================================================


def test_analyze_result() -> None:
    """Complete ranking result should be analyzed."""

    analyzer = OpportunityAnalyzer()

    result = analyzer.analyze_result(
        make_result()
    )

    assert isinstance(
        result,
        OpportunityAnalysisResult,
    )

    assert result.total_count == 3
    assert len(result.signals) == 3


def test_analyze_result_preserves_order() -> None:
    """Original ranking order should be preserved."""

    analyzer = OpportunityAnalyzer()

    result = analyzer.analyze_result(
        make_result()
    )

    assert [
        signal.symbol
        for signal in result.signals
    ] == [
        "TEST-C-100",
        "TEST-C-105",
        "TEST-C-110",
    ]


def test_analyze_result_top_signal() -> None:
    """Top signal should correspond to first ranked item."""

    analyzer = OpportunityAnalyzer()

    result = analyzer.analyze_result(
        make_result()
    )

    assert result.top_signal is not None

    assert (
        result.top_signal.symbol
        == "TEST-C-100"
    )

    assert (
        result.top_signal.action
        == ACTION_BUY
    )


def test_analyze_result_rejects_invalid_type() -> None:
    """Invalid ranking result should be rejected."""

    analyzer = OpportunityAnalyzer()

    with pytest.raises(TypeError):
        analyzer.analyze_result(
            []  # type: ignore[arg-type]
        )


# ==========================================================
# Signal Collections
# ==========================================================


def test_buy_signals() -> None:
    """BUY signals should be exposed."""

    analyzer = OpportunityAnalyzer()

    result = analyzer.analyze_result(
        make_result()
    )

    assert len(
        result.buy_signals
    ) == 1

    assert (
        result.buy_signals[0].symbol
        == "TEST-C-100"
    )


def test_watch_signals() -> None:
    """WATCH signals should be exposed."""

    analyzer = OpportunityAnalyzer()

    result = analyzer.analyze_result(
        make_result()
    )

    assert len(
        result.watch_signals
    ) == 1

    assert (
        result.watch_signals[0].symbol
        == "TEST-C-105"
    )


def test_avoid_signals() -> None:
    """AVOID signals should be exposed."""

    analyzer = OpportunityAnalyzer()

    result = analyzer.analyze_result(
        make_result()
    )

    assert len(
        result.avoid_signals
    ) == 1

    assert (
        result.avoid_signals[0].symbol
        == "TEST-C-110"
    )


# ==========================================================
# Iterable API
# ==========================================================


def test_analyze_items() -> None:
    """Iterable items should be supported."""

    analyzer = OpportunityAnalyzer()

    result = analyzer.analyze_items(
        [
            make_item(
                symbol="TEST-C-100",
                score=5.0,
            ),
            make_item(
                symbol="TEST-C-105",
                score=2.0,
            ),
        ]
    )

    assert result.total_count == 2

    assert [
        signal.action
        for signal in result.signals
    ] == [
        ACTION_BUY,
        ACTION_WATCH,
    ]


def test_analyze_items_accepts_generator() -> None:
    """Generators should be supported."""

    analyzer = OpportunityAnalyzer()

    items = (
        item
        for item in make_result().items
    )

    result = analyzer.analyze_items(
        items
    )

    assert result.total_count == 3


def test_analyze_items_empty() -> None:
    """Empty iterable should return empty result."""

    analyzer = OpportunityAnalyzer()

    result = analyzer.analyze_items(
        []
    )

    assert result.total_count == 0
    assert result.signals == ()
    assert result.top_signal is None


# ==========================================================
# Immutability
# ==========================================================


def test_signal_is_frozen() -> None:
    """OpportunitySignal should be immutable."""

    signal = OpportunitySignal(
        symbol="TEST-C-100",
        direction="CALL",
        score=5.0,
        level=LEVEL_STRONG,
        action=ACTION_BUY,
        reason="test",
    )

    with pytest.raises(
        AttributeError
    ):
        signal.score = 10.0  # type: ignore[misc]


def test_analysis_result_is_frozen() -> None:
    """OpportunityAnalysisResult should be immutable."""

    result = OpportunityAnalysisResult(
        signals=(),
        total_count=0,
    )

    with pytest.raises(
        AttributeError
    ):
        result.total_count = 1  # type: ignore[misc]


# ==========================================================
# Custom Threshold Behavior
# ==========================================================


def test_custom_threshold_changes_classification() -> None:
    """Custom thresholds should affect classification."""

    analyzer = OpportunityAnalyzer(
        strong_threshold=10.0,
        medium_threshold=5.0,
    )

    assert analyzer.classify_level(
        10.0
    ) == LEVEL_STRONG

    assert analyzer.classify_level(
        5.0
    ) == LEVEL_MEDIUM

    assert analyzer.classify_level(
        4.99
    ) == LEVEL_WEAK


# ==========================================================
# Existing Ranking API Compatibility
# ==========================================================


def test_analyzer_does_not_modify_ranking_result() -> None:
    """Analysis should not modify the source ranking result."""

    analyzer = OpportunityAnalyzer()

    ranking_result = make_result()

    original_items = ranking_result.items

    analyzer.analyze_result(
        ranking_result
    )

    assert ranking_result.items == original_items


def test_analyzer_does_not_modify_ranking_scores() -> None:
    """Analysis should preserve source scores."""

    analyzer = OpportunityAnalyzer()

    ranking_result = make_result()

    original_scores = tuple(
        item.score
        for item in ranking_result.items
    )

    analyzer.analyze_result(
        ranking_result
    )

    assert tuple(
        item.score
        for item in ranking_result.items
    ) == original_scores