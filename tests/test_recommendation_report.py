"""
Commodity Option Valuator Pro
=============================

Tests for Recommendation Report Model.

Commit 0021
-----------

Author : Simon
Version : 0.6.3
"""

from __future__ import annotations

from datetime import datetime

import pytest

from core.recommendation_presentation import (
    PresentationAction,
    PresentationLevel,
    RecommendationPresentation,
    RecommendationPresentationResult,
)
from core.recommendation_report import (
    RecommendationReport,
    RecommendationReportItem,
)
from core.recommendation_summary import (
    RecommendationSummary,
)


# ==========================================================
# Test Data
# ==========================================================


def make_summary(
    total_count: int = 1,
    buy_count: int = 1,
    sell_count: int = 0,
    watch_count: int = 0,
    reject_count: int = 0,
) -> RecommendationSummary:
    """Create deterministic summary data."""

    return RecommendationSummary(
        total_count=total_count,
        buy_count=buy_count,
        sell_count=sell_count,
        watch_count=watch_count,
        reject_count=reject_count,
        level_a_count=buy_count,
        level_b_count=watch_count,
        level_c_count=0,
        level_d_count=reject_count,
        highest_score=5.0 if total_count else None,
        lowest_risk_score=2.0 if total_count else None,
        top=None,
    )


def make_item(
    symbol: str = "TEST-C-100",
    action: PresentationAction = PresentationAction.BUY,
    level: PresentationLevel = PresentationLevel.A,
    score: float = 5.0,
    risk_score: float = 2.0,
) -> RecommendationPresentation:
    """Create a deterministic presentation item."""

    return RecommendationPresentation(
        symbol=symbol,
        action=action,
        action_title=action.value,
        action_description="test action",
        level=level,
        level_title=level.value,
        level_description="test level",
        score=score,
        risk_score=risk_score,
        reason="test reason",
        risk_warning=None,
    )


def make_presentation_result(
    items: tuple[
        RecommendationPresentation,
        ...,
    ],
    ranked_count: int | None = None,
) -> RecommendationPresentationResult:
    """Create a deterministic presentation result."""

    if ranked_count is None:
        ranked_count = len(items)

    summary = make_summary(
        total_count=len(items),
        buy_count=sum(
            item.action == PresentationAction.BUY
            for item in items
        ),
        sell_count=sum(
            item.action == PresentationAction.SELL
            for item in items
        ),
        watch_count=sum(
            item.action == PresentationAction.WATCH
            for item in items
        ),
        reject_count=sum(
            item.action == PresentationAction.REJECT
            for item in items
        ),
    )

    return RecommendationPresentationResult(
        items=items,
        summary=summary,
        ranked_count=ranked_count,
    )


# ==========================================================
# Import
# ==========================================================


def test_recommendation_report_import() -> None:
    """Report model should be importable."""

    report = RecommendationReport.empty()

    assert report is not None


# ==========================================================
# Item
# ==========================================================


def test_report_item_structure() -> None:
    """Report item should expose all required fields."""

    presentation = make_item()

    item = RecommendationReportItem.from_presentation(
        presentation
    )

    assert item.symbol == "TEST-C-100"
    assert item.action == "BUY"
    assert item.level == "A"
    assert item.score == 5.0
    assert item.risk_score == 2.0
    assert item.reason == "test reason"


def test_report_item_preserves_warning() -> None:
    """Risk warning should be preserved."""

    presentation = RecommendationPresentation(
        symbol="TEST",
        action=PresentationAction.REJECT,
        action_title="REJECT",
        action_description="reject",
        level=PresentationLevel.D,
        level_title="D",
        level_description="high risk",
        score=5.0,
        risk_score=9.0,
        reason="high risk",
        risk_warning="High risk warning",
    )

    item = RecommendationReportItem.from_presentation(
        presentation
    )

    assert item.risk_warning == "High risk warning"


def test_report_item_rejects_invalid_input() -> None:
    """Invalid presentation input should be rejected."""

    with pytest.raises(
        TypeError,
        match="item must be a RecommendationPresentation",
    ):
        RecommendationReportItem.from_presentation(
            "invalid"  # type: ignore[arg-type]
        )


# ==========================================================
# Construction
# ==========================================================


def test_report_from_presentation() -> None:
    """Report should be constructed from presentation result."""

    generated_at = datetime(
        2026,
        8,
        19,
        10,
        30,
        0,
    )

    result = make_presentation_result(
        (
            make_item(),
        ),
        ranked_count=7,
    )

    report = RecommendationReport.from_presentation(
        result,
        generated_at=generated_at,
    )

    assert report.ranked_count == 7
    assert report.total_count == 1
    assert report.symbols == (
        "TEST-C-100",
    )
    assert report.generated_at == generated_at


def test_report_title_is_preserved() -> None:
    """Custom report title should be preserved."""

    result = make_presentation_result(
        ()
    )

    report = RecommendationReport.from_presentation(
        result,
        title="Daily Option Report",
    )

    assert report.title == "Daily Option Report"


def test_report_title_is_trimmed() -> None:
    """Report title should be normalized."""

    result = make_presentation_result(
        ()
    )

    report = RecommendationReport.from_presentation(
        result,
        title="  Daily Report  ",
    )

    assert report.title == "Daily Report"


def test_empty_title_is_rejected() -> None:
    """Empty title should be rejected."""

    result = make_presentation_result(
        ()
    )

    with pytest.raises(
        ValueError,
        match="title must not be empty",
    ):
        RecommendationReport.from_presentation(
            result,
            title="   ",
        )


def test_invalid_presentation_result_is_rejected() -> None:
    """Invalid presentation result should be rejected."""

    with pytest.raises(
        TypeError,
        match="result must be a RecommendationPresentationResult",
    ):
        RecommendationReport.from_presentation(
            "invalid"  # type: ignore[arg-type]
        )


def test_invalid_generated_at_is_rejected() -> None:
    """Invalid timestamp should be rejected."""

    result = make_presentation_result(
        ()
    )

    with pytest.raises(
        TypeError,
        match="generated_at must be a datetime",
    ):
        RecommendationReport.from_presentation(
            result,
            generated_at="invalid"  # type: ignore[arg-type]
        )


# ==========================================================
# Empty Report
# ==========================================================


def test_empty_report() -> None:
    """Empty report should be supported."""

    generated_at = datetime(
        2026,
        8,
        19,
        10,
        0,
        0,
    )

    report = RecommendationReport.empty(
        generated_at=generated_at
    )

    assert report.ranked_count == 0
    assert report.total_count == 0
    assert report.items == ()
    assert report.top is None
    assert report.symbols == ()
    assert report.has_active_recommendation is False
    assert report.has_high_risk is False
    assert report.generated_at == generated_at


def test_empty_report_summary() -> None:
    """Empty report should contain zero summary."""

    report = RecommendationReport.empty()

    assert report.summary.total_count == 0
    assert report.summary.buy_count == 0
    assert report.summary.sell_count == 0
    assert report.summary.watch_count == 0
    assert report.summary.reject_count == 0
    assert report.summary.highest_score is None
    assert report.summary.lowest_risk_score is None
    assert report.summary.top is None


# ==========================================================
# Properties
# ==========================================================


def test_top_returns_first_item() -> None:
    """Top should return the first item."""

    first = make_item(
        symbol="FIRST"
    )

    second = make_item(
        symbol="SECOND"
    )

    report = RecommendationReport.from_presentation(
        make_presentation_result(
            (
                first,
                second,
            )
        )
    )

    assert report.top is not None
    assert report.top.symbol == "FIRST"


def test_total_count_matches_items() -> None:
    """Total count should match report items."""

    report = RecommendationReport.from_presentation(
        make_presentation_result(
            (
                make_item("ONE"),
                make_item("TWO"),
                make_item("THREE"),
            )
        )
    )

    assert report.total_count == 3


def test_symbols_returns_ordered_symbols() -> None:
    """Symbols should preserve presentation order."""

    report = RecommendationReport.from_presentation(
        make_presentation_result(
            (
                make_item("ONE"),
                make_item("TWO"),
            )
        )
    )

    assert report.symbols == (
        "ONE",
        "TWO",
    )


# ==========================================================
# Active Recommendation
# ==========================================================


def test_has_active_recommendation_for_buy() -> None:
    """BUY should mark the report as active."""

    report = RecommendationReport.from_presentation(
        make_presentation_result(
            (
                make_item(
                    action=PresentationAction.BUY
                ),
            )
        )
    )

    assert report.has_active_recommendation is True


def test_has_active_recommendation_for_sell() -> None:
    """SELL should mark the report as active."""

    report = RecommendationReport.from_presentation(
        make_presentation_result(
            (
                make_item(
                    action=PresentationAction.SELL
                ),
            )
        )
    )

    assert report.has_active_recommendation is True


def test_watch_only_is_not_active() -> None:
    """WATCH alone should not be active."""

    report = RecommendationReport.from_presentation(
        make_presentation_result(
            (
                make_item(
                    action=PresentationAction.WATCH,
                    level=PresentationLevel.B,
                ),
            )
        )
    )

    assert report.has_active_recommendation is False


def test_reject_only_is_not_active() -> None:
    """REJECT alone should not be active."""

    report = RecommendationReport.from_presentation(
        make_presentation_result(
            (
                make_item(
                    action=PresentationAction.REJECT,
                    level=PresentationLevel.D,
                ),
            )
        )
    )

    assert report.has_active_recommendation is False


# ==========================================================
# Risk
# ==========================================================


def test_has_high_risk_when_warning_exists() -> None:
    """Risk warning should mark report as high risk."""

    presentation = RecommendationPresentation(
        symbol="RISK",
        action=PresentationAction.REJECT,
        action_title="REJECT",
        action_description="reject",
        level=PresentationLevel.D,
        level_title="D",
        level_description="high risk",
        score=5.0,
        risk_score=9.0,
        reason="high risk",
        risk_warning="High risk warning",
    )

    report = RecommendationReport.from_presentation(
        make_presentation_result(
            (
                presentation,
            )
        )
    )

    assert report.has_high_risk is True


def test_no_high_risk_without_warning() -> None:
    """No warning should mean no high-risk flag."""

    report = RecommendationReport.from_presentation(
        make_presentation_result(
            (
                make_item(),
            )
        )
    )

    assert report.has_high_risk is False


# ==========================================================
# Top N
# ==========================================================


def test_top_n_returns_requested_items() -> None:
    """top_n should return requested items."""

    report = RecommendationReport.from_presentation(
        make_presentation_result(
            (
                make_item("ONE"),
                make_item("TWO"),
                make_item("THREE"),
            )
        )
    )

    result = report.top_n(2)

    assert len(result) == 2
    assert result[0].symbol == "ONE"
    assert result[1].symbol == "TWO"


def test_top_n_larger_than_available() -> None:
    """top_n larger than available should return all."""

    report = RecommendationReport.from_presentation(
        make_presentation_result(
            (
                make_item("ONE"),
            )
        )
    )

    result = report.top_n(10)

    assert len(result) == 1


def test_top_n_rejects_zero() -> None:
    """top_n should reject zero."""

    report = RecommendationReport.empty()

    with pytest.raises(
        ValueError,
        match="n must be greater than zero",
    ):
        report.top_n(0)


def test_top_n_rejects_negative() -> None:
    """top_n should reject negative values."""

    report = RecommendationReport.empty()

    with pytest.raises(
        ValueError,
        match="n must be greater than zero",
    ):
        report.top_n(-1)


# ==========================================================
# Filtering
# ==========================================================


def test_filter_actions() -> None:
    """Action filtering should work."""

    report = RecommendationReport.from_presentation(
        make_presentation_result(
            (
                make_item(
                    symbol="BUY",
                    action=PresentationAction.BUY,
                ),
                make_item(
                    symbol="WATCH",
                    action=PresentationAction.WATCH,
                    level=PresentationLevel.B,
                ),
                make_item(
                    symbol="SELL",
                    action=PresentationAction.SELL,
                ),
            )
        )
    )

    result = report.filter_actions(
        ["BUY", "SELL"]
    )

    assert tuple(
        item.symbol
        for item in result
    ) == (
        "BUY",
        "SELL",
    )


def test_filter_actions_is_case_insensitive() -> None:
    """Action filtering should ignore case."""

    report = RecommendationReport.from_presentation(
        make_presentation_result(
            (
                make_item(
                    symbol="BUY",
                    action=PresentationAction.BUY,
                ),
            )
        )
    )

    result = report.filter_actions(
        ["buy"]
    )

    assert len(result) == 1
    assert result[0].symbol == "BUY"


def test_filter_actions_empty_returns_empty() -> None:
    """Empty action selection should return empty."""

    report = RecommendationReport.from_presentation(
        make_presentation_result(
            (
                make_item(),
            )
        )
    )

    assert report.filter_actions([]) == ()


def test_filter_actions_rejects_invalid_action() -> None:
    """Invalid action should be rejected."""

    report = RecommendationReport.empty()

    with pytest.raises(
        ValueError,
        match="invalid recommendation action",
    ):
        report.filter_actions(
            ["INVALID"]
        )


def test_filter_levels() -> None:
    """Level filtering should work."""

    report = RecommendationReport.from_presentation(
        make_presentation_result(
            (
                make_item(
                    symbol="A",
                    level=PresentationLevel.A,
                ),
                make_item(
                    symbol="B",
                    level=PresentationLevel.B,
                    action=PresentationAction.WATCH,
                ),
            )
        )
    )

    result = report.filter_levels(
        ["A"]
    )

    assert tuple(
        item.symbol
        for item in result
    ) == (
        "A",
    )


def test_filter_levels_is_case_insensitive() -> None:
    """Level filtering should ignore case."""

    report = RecommendationReport.from_presentation(
        make_presentation_result(
            (
                make_item(
                    symbol="A",
                    level=PresentationLevel.A,
                ),
            )
        )
    )

    result = report.filter_levels(
        ["a"]
    )

    assert len(result) == 1


def test_filter_levels_empty_returns_empty() -> None:
    """Empty level selection should return empty."""

    report = RecommendationReport.empty()

    assert report.filter_levels([]) == ()


def test_filter_levels_rejects_invalid_level() -> None:
    """Invalid level should be rejected."""

    report = RecommendationReport.empty()

    with pytest.raises(
        ValueError,
        match="invalid recommendation level",
    ):
        report.filter_levels(
            ["Z"]
        )


# ==========================================================
# Immutability
# ==========================================================


def test_report_is_frozen() -> None:
    """Report should be immutable."""

    report = RecommendationReport.empty()

    with pytest.raises(
        AttributeError
    ):
        report.title = "changed"  # type: ignore[misc]


def test_report_item_is_frozen() -> None:
    """Report item should be immutable."""

    item = RecommendationReportItem.from_presentation(
        make_item()
    )

    with pytest.raises(
        AttributeError
    ):
        item.symbol = "changed"  # type: ignore[misc]


# ==========================================================
# Ranked Count
# ==========================================================


def test_ranked_count_can_exceed_recommendation_count() -> None:
    """Ranked count should be independent of report count."""

    report = RecommendationReport.from_presentation(
        make_presentation_result(
            (
                make_item(),
            ),
            ranked_count=10,
        )
    )

    assert report.ranked_count == 10
    assert report.total_count == 1


def test_negative_ranked_count_is_rejected() -> None:
    """Negative ranked count should be rejected."""

    result = make_presentation_result(
        (
            make_item(),
        ),
        ranked_count=-1,
    )

    with pytest.raises(
        ValueError,
        match="ranked_count must not be negative",
    ):
        RecommendationReport.from_presentation(
            result
        )


# ==========================================================
# Summary Preservation
# ==========================================================


def test_summary_is_preserved() -> None:
    """Report should preserve presentation summary."""

    summary = RecommendationSummary(
        total_count=2,
        buy_count=1,
        sell_count=1,
        watch_count=0,
        reject_count=0,
        level_a_count=2,
        level_b_count=0,
        level_c_count=0,
        level_d_count=0,
        highest_score=8.0,
        lowest_risk_score=1.0,
        top=None,
    )

    result = RecommendationPresentationResult(
        items=(
            make_item(
                symbol="BUY",
                action=PresentationAction.BUY,
            ),
            make_item(
                symbol="SELL",
                action=PresentationAction.SELL,
            ),
        ),
        summary=summary,
        ranked_count=5,
    )

    report = RecommendationReport.from_presentation(
        result
    )

    assert report.summary is summary
    assert report.summary.total_count == 2
    assert report.summary.highest_score == 8.0
    assert report.summary.lowest_risk_score == 1.0
    assert report.summary.top is None