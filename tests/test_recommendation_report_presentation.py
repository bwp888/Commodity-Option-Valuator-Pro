"""
Commodity Option Valuator Pro
=============================

Tests for Recommendation Report Presentation.

Commit 0022
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
)

from core.recommendation_report_presentation import (
    RecommendationReportPresentation,
    RecommendationReportPresentationRow,
    RecommendationReportPresenter,
    present_recommendation_report,
)

from core.recommendation_summary import (
    RecommendationSummary,
)


# ==========================================================
# Test Data
# ==========================================================


GENERATED_AT = datetime(
    2026,
    8,
    19,
    10,
    30,
    0,
)


def make_summary(
    total_count: int = 1,
    buy_count: int = 1,
    sell_count: int = 0,
    watch_count: int = 0,
    reject_count: int = 0,
) -> RecommendationSummary:
    """
    Create deterministic summary data.
    """

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
    risk_warning: str | None = None,
) -> RecommendationPresentation:
    """
    Create deterministic presentation data.
    """

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
        risk_warning=risk_warning,
    )


def make_result(
    items: tuple[
        RecommendationPresentation,
        ...,
    ],
    ranked_count: int | None = None,
) -> RecommendationPresentationResult:
    """
    Create deterministic presentation result.
    """

    if ranked_count is None:
        ranked_count = len(
            items
        )

    buy_count = sum(
        item.action
        == PresentationAction.BUY
        for item in items
    )

    sell_count = sum(
        item.action
        == PresentationAction.SELL
        for item in items
    )

    watch_count = sum(
        item.action
        == PresentationAction.WATCH
        for item in items
    )

    reject_count = sum(
        item.action
        == PresentationAction.REJECT
        for item in items
    )

    summary = RecommendationSummary(
        total_count=len(items),
        buy_count=buy_count,
        sell_count=sell_count,
        watch_count=watch_count,
        reject_count=reject_count,
        level_a_count=sum(
            item.level
            == PresentationLevel.A
            for item in items
        ),
        level_b_count=sum(
            item.level
            == PresentationLevel.B
            for item in items
        ),
        level_c_count=sum(
            item.level
            == PresentationLevel.C
            for item in items
        ),
        level_d_count=sum(
            item.level
            == PresentationLevel.D
            for item in items
        ),
        highest_score=(
            max(
                item.score
                for item in items
            )
            if items
            else None
        ),
        lowest_risk_score=(
            min(
                item.risk_score
                for item in items
            )
            if items
            else None
        ),
        top=None,
    )

    return RecommendationPresentationResult(
        items=items,
        summary=summary,
        ranked_count=ranked_count,
    )


def make_report(
    items: tuple[
        RecommendationPresentation,
        ...,
    ] = (
        make_item(),
    ),
    ranked_count: int | None = None,
) -> RecommendationReport:
    """
    Create a deterministic report.
    """

    if ranked_count is None:
        ranked_count = len(
            items
        )

    return RecommendationReport.from_presentation(
        make_result(
            items,
            ranked_count=ranked_count,
        ),
        generated_at=GENERATED_AT,
    )


# ==========================================================
# Import
# ==========================================================


def test_report_presentation_import() -> None:
    """
    Presentation model should be importable.
    """

    presentation = RecommendationReportPresenter.empty()

    assert presentation is not None


# ==========================================================
# Formatting
# ==========================================================


def test_format_datetime() -> None:
    """
    Datetime formatting should be stable.
    """

    assert (
        RecommendationReportPresenter.format_datetime(
            GENERATED_AT
        )
        == "2026-08-19 10:30:00"
    )


def test_format_datetime_rejects_invalid_value() -> None:
    """
    Invalid datetime should be rejected.
    """

    with pytest.raises(
        TypeError,
        match="value must be a datetime",
    ):
        RecommendationReportPresenter.format_datetime(
            "invalid"  # type: ignore[arg-type]
        )


def test_format_score() -> None:
    """
    Score formatting should use two decimals.
    """

    assert (
        RecommendationReportPresenter.format_score(
            5
        )
        == "5.00"
    )


def test_format_none_score() -> None:
    """
    None score should be displayed as --.
    """

    assert (
        RecommendationReportPresenter.format_score(
            None
        )
        == "--"
    )


def test_format_count() -> None:
    """
    Count formatting should return a string.
    """

    assert (
        RecommendationReportPresenter.format_count(
            10
        )
        == "10"
    )


def test_format_count_rejects_invalid_value() -> None:
    """
    Invalid count should be rejected.
    """

    with pytest.raises(
        TypeError,
        match="value must be an int",
    ):
        RecommendationReportPresenter.format_count(
            "10"  # type: ignore[arg-type]
        )


def test_format_risk_warning() -> None:
    """
    Risk warning should be normalized.
    """

    assert (
        RecommendationReportPresenter.format_risk_warning(
            "  High Risk  "
        )
        == "High Risk"
    )


def test_format_missing_risk_warning() -> None:
    """
    Missing warning should become an empty string.
    """

    assert (
        RecommendationReportPresenter.format_risk_warning(
            None
        )
        == ""
    )


# ==========================================================
# Action / Level
# ==========================================================


@pytest.mark.parametrize(
    "action",
    [
        "BUY",
        "SELL",
        "WATCH",
        "REJECT",
        "buy",
        "sell",
    ],
)
def test_action_title_accepts_valid_actions(
    action: str,
) -> None:
    """
    Valid actions should be normalized.
    """

    assert (
        RecommendationReportPresenter.action_title(
            action
        )
        == action.upper()
    )


def test_action_title_rejects_invalid_action() -> None:
    """
    Invalid action should be rejected.
    """

    with pytest.raises(
        ValueError,
        match="invalid recommendation action",
    ):
        RecommendationReportPresenter.action_title(
            "INVALID"
        )


@pytest.mark.parametrize(
    "level",
    [
        "A",
        "B",
        "C",
        "D",
        "a",
        "b",
    ],
)
def test_level_title_accepts_valid_levels(
    level: str,
) -> None:
    """
    Valid levels should be normalized.
    """

    assert (
        RecommendationReportPresenter.level_title(
            level
        )
        == level.upper()
    )


def test_level_title_rejects_invalid_level() -> None:
    """
    Invalid level should be rejected.
    """

    with pytest.raises(
        ValueError,
        match="invalid recommendation level",
    ):
        RecommendationReportPresenter.level_title(
            "Z"
        )


# ==========================================================
# Single Row
# ==========================================================


def test_present_item() -> None:
    """
    A report item should be converted into one presentation row.
    """

    item = make_item(
        symbol="TEST",
        score=8.25,
        risk_score=3.5,
    )

    report = make_report(
        (
            item,
        )
    )

    row = RecommendationReportPresenter.present_item(
        report.items[0]
    )

    assert isinstance(
        row,
        RecommendationReportPresentationRow,
    )

    assert row.symbol == "TEST"
    assert row.action == "BUY"
    assert row.level == "A"
    assert row.score == 8.25
    assert row.risk_score == 3.5
    assert row.score_text == "8.25"
    assert row.risk_score_text == "3.50"
    assert row.reason == "test reason"


def test_present_item_preserves_warning() -> None:
    """
    Risk warning should be preserved.
    """

    item = make_item(
        risk_warning="High risk warning"
    )

    report = make_report(
        (
            item,
        )
    )

    row = RecommendationReportPresenter.present_item(
        report.items[0]
    )

    assert row.risk_warning == "High risk warning"
    assert row.risk_warning_text == "High risk warning"


def test_present_item_without_warning() -> None:
    """
    Missing risk warning should produce empty display text.
    """

    report = make_report()

    row = RecommendationReportPresenter.present_item(
        report.items[0]
    )

    assert row.risk_warning is None
    assert row.risk_warning_text == ""


def test_present_item_rejects_invalid_input() -> None:
    """
    Invalid report item should be rejected.
    """

    with pytest.raises(
        TypeError,
        match="item must be a RecommendationReportItem",
    ):
        RecommendationReportPresenter.present_item(
            "invalid"  # type: ignore[arg-type]
        )


# ==========================================================
# Complete Presentation
# ==========================================================


def test_present_report() -> None:
    """
    Complete report should be converted correctly.
    """

    report = make_report(
        (
            make_item(
                symbol="ONE",
                score=8.0,
                risk_score=2.0,
            ),
            make_item(
                symbol="TWO",
                action=PresentationAction.WATCH,
                level=PresentationLevel.B,
                score=5.0,
                risk_score=4.0,
            ),
        ),
        ranked_count=10,
    )

    presentation = RecommendationReportPresenter.present(
        report
    )

    assert isinstance(
        presentation,
        RecommendationReportPresentation,
    )

    assert presentation.title == (
        "Commodity Option Recommendation Report"
    )

    assert presentation.generated_at == GENERATED_AT
    assert presentation.generated_at_text == (
        "2026-08-19 10:30:00"
    )

    assert presentation.ranked_count == 10
    assert presentation.ranked_count_text == "10"

    assert presentation.total_count == 2
    assert presentation.total_count_text == "2"

    assert presentation.active_count == 1
    assert presentation.active_count_text == "1"

    assert presentation.has_active_recommendation is True
    assert presentation.has_high_risk is False

    assert presentation.highest_score == 8.0
    assert presentation.highest_score_text == "8.00"

    assert presentation.lowest_risk_score == 2.0
    assert presentation.lowest_risk_score_text == "2.00"

    assert presentation.top_symbol == "ONE"
    assert presentation.top_action == "BUY"
    assert presentation.top_level == "A"

    assert len(
        presentation.rows
    ) == 2

    assert presentation.rows[0].symbol == "ONE"
    assert presentation.rows[1].symbol == "TWO"


def test_present_report_preserves_order() -> None:
    """
    Presentation order must match report order.
    """

    report = make_report(
        (
            make_item("FIRST"),
            make_item("SECOND"),
            make_item("THIRD"),
        )
    )

    presentation = RecommendationReportPresenter.present(
        report
    )

    assert tuple(
        row.symbol
        for row in presentation.rows
    ) == (
        "FIRST",
        "SECOND",
        "THIRD",
    )


def test_present_report_preserves_action_counts() -> None:
    """
    Summary action counts should be exposed unchanged.
    """

    report = make_report(
        (
            make_item(
                action=PresentationAction.BUY
            ),
            make_item(
                symbol="SELL",
                action=PresentationAction.SELL,
            ),
            make_item(
                symbol="WATCH",
                action=PresentationAction.WATCH,
                level=PresentationLevel.B,
            ),
        )
    )

    presentation = RecommendationReportPresenter.present(
        report
    )

    assert presentation.action_counts == {
        "BUY": 1,
        "SELL": 1,
        "WATCH": 1,
        "REJECT": 0,
    }


def test_present_report_preserves_level_counts() -> None:
    """
    Summary level counts should be exposed unchanged.
    """

    report = make_report(
        (
            make_item(
                level=PresentationLevel.A
            ),
            make_item(
                symbol="B",
                level=PresentationLevel.B,
                action=PresentationAction.WATCH,
            ),
        )
    )

    presentation = RecommendationReportPresenter.present(
        report
    )

    assert presentation.level_counts == {
        "A": 1,
        "B": 1,
        "C": 0,
        "D": 0,
    }


# ==========================================================
# Empty Report
# ==========================================================


def test_present_empty_report() -> None:
    """
    Empty report should produce a valid empty presentation.
    """

    report = RecommendationReport.empty(
        generated_at=GENERATED_AT
    )

    presentation = RecommendationReportPresenter.present(
        report
    )

    assert presentation.total_count == 0
    assert presentation.total_count_text == "0"
    assert presentation.ranked_count == 0
    assert presentation.ranked_count_text == "0"

    assert presentation.active_count == 0
    assert presentation.active_count_text == "0"

    assert presentation.has_active_recommendation is False
    assert presentation.has_high_risk is False

    assert presentation.highest_score is None
    assert presentation.highest_score_text == "--"

    assert presentation.lowest_risk_score is None
    assert presentation.lowest_risk_score_text == "--"

    assert presentation.top_symbol is None
    assert presentation.top_action is None
    assert presentation.top_level is None

    assert presentation.rows == ()

    assert presentation.action_counts == {
        "BUY": 0,
        "SELL": 0,
        "WATCH": 0,
        "REJECT": 0,
    }

    assert presentation.level_counts == {
        "A": 0,
        "B": 0,
        "C": 0,
        "D": 0,
    }


def test_empty_convenience_method() -> None:
    """
    Presenter.empty should create a valid presentation.
    """

    presentation = RecommendationReportPresenter.empty()

    assert isinstance(
        presentation,
        RecommendationReportPresentation,
    )

    assert presentation.total_count == 0


# ==========================================================
# High Risk
# ==========================================================


def test_high_risk_is_exposed() -> None:
    """
    High-risk reports should expose the flag.
    """

    report = make_report(
        (
            make_item(
                action=PresentationAction.REJECT,
                level=PresentationLevel.D,
                risk_score=9.0,
                risk_warning="High risk warning",
            ),
        )
    )

    presentation = RecommendationReportPresenter.present(
        report
    )

    assert presentation.has_high_risk is True


# ==========================================================
# Convenience Function
# ==========================================================


def test_present_recommendation_report() -> None:
    """
    Convenience function should delegate to the presenter.
    """

    report = make_report()

    presentation = present_recommendation_report(
        report
    )

    assert isinstance(
        presentation,
        RecommendationReportPresentation,
    )

    assert presentation.top_symbol == "TEST-C-100"


# ==========================================================
# Immutability
# ==========================================================


def test_presentation_is_frozen() -> None:
    """
    Presentation model should be immutable.
    """

    presentation = RecommendationReportPresenter.empty()

    with pytest.raises(
        AttributeError
    ):
        presentation.title = "changed"  # type: ignore[misc]


def test_row_is_frozen() -> None:
    """
    Presentation row should be immutable.
    """

    report = make_report()

    row = RecommendationReportPresenter.present_item(
        report.items[0]
    )

    with pytest.raises(
        AttributeError
    ):
        row.symbol = "changed"  # type: ignore[misc]


# ==========================================================
# Invalid Report
# ==========================================================


def test_present_rejects_invalid_report() -> None:
    """
    Invalid report should be rejected.
    """

    with pytest.raises(
        TypeError,
        match="report must be a RecommendationReport",
    ):
        RecommendationReportPresenter.present(
            "invalid"  # type: ignore[arg-type]
        )


def test_convenience_function_rejects_invalid_report() -> None:
    """
    Convenience function should reject invalid input.
    """

    with pytest.raises(
        TypeError,
        match="report must be a RecommendationReport",
    ):
        present_recommendation_report(
            "invalid"  # type: ignore[arg-type]
        )