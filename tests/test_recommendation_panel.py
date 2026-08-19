"""
Commodity Option Valuator Pro
=============================

Tests for Recommendation Panel.

Commit 0023
-----------

Tests the CustomTkinter recommendation panel integration.

Author : Simon
Version : 0.6.3
Python : 3.12
"""

from __future__ import annotations

from datetime import datetime

import customtkinter as ctk
import pytest

from core.recommendation_report_presentation import (
    RecommendationReportPresentation,
    RecommendationReportPresentationRow,
)
from ui.recommendation_panel import (
    RecommendationPanel,
    create_recommendation_panel,
)


# ==========================================================
# Test Data
# ==========================================================


def make_row(
    symbol: str = "TEST-C-100",
    action: str = "BUY",
    level: str = "A",
    score: float = 5.0,
    risk_score: float = 2.0,
    reason: str = "test reason",
    risk_warning: str | None = None,
) -> RecommendationReportPresentationRow:
    """
    Create deterministic presentation-row data.
    """

    return RecommendationReportPresentationRow(
        symbol=symbol,
        action=action,
        action_title=action,
        level=level,
        level_title=level,
        score=score,
        risk_score=risk_score,
        score_text=f"{score:.2f}",
        risk_score_text=f"{risk_score:.2f}",
        reason=reason,
        risk_warning=risk_warning,
        risk_warning_text=(
            risk_warning
            if risk_warning is not None
            else ""
        ),
        action_description=action,
        level_description=(
            f"Level {level}"
        ),
    )


def make_presentation(
    rows: tuple[
        RecommendationReportPresentationRow,
        ...,
    ] = (),
    *,
    has_high_risk: bool = False,
) -> RecommendationReportPresentation:
    """
    Create deterministic presentation data.
    """

    total_count = len(
        rows
    )

    return RecommendationReportPresentation(
        title="Test Recommendation Report",
        generated_at=datetime(
            2026,
            8,
            19,
            10,
            30,
            0,
        ),
        generated_at_text="2026-08-19 10:30:00",
        ranked_count=10,
        ranked_count_text="10",
        total_count=total_count,
        total_count_text=str(
            total_count
        ),
        active_count=(
            sum(
                1
                for row in rows
                if row.action in {
                    "BUY",
                    "SELL",
                }
            )
        ),
        active_count_text=str(
            sum(
                1
                for row in rows
                if row.action in {
                    "BUY",
                    "SELL",
                }
            )
        ),
        has_active_recommendation=any(
            row.action in {
                "BUY",
                "SELL",
            }
            for row in rows
        ),
        has_high_risk=has_high_risk,
        highest_score=(
            max(
                row.score
                for row in rows
            )
            if rows
            else None
        ),
        highest_score_text=(
            f"{max(row.score for row in rows):.2f}"
            if rows
            else "--"
        ),
        lowest_risk_score=(
            min(
                row.risk_score
                for row in rows
            )
            if rows
            else None
        ),
        lowest_risk_score_text=(
            f"{min(row.risk_score for row in rows):.2f}"
            if rows
            else "--"
        ),
        top_symbol=(
            rows[0].symbol
            if rows
            else None
        ),
        top_action=(
            rows[0].action
            if rows
            else None
        ),
        top_level=(
            rows[0].level
            if rows
            else None
        ),
        rows=rows,
        action_counts={
            "BUY": sum(
                row.action == "BUY"
                for row in rows
            ),
            "SELL": sum(
                row.action == "SELL"
                for row in rows
            ),
            "WATCH": sum(
                row.action == "WATCH"
                for row in rows
            ),
            "REJECT": sum(
                row.action == "REJECT"
                for row in rows
            ),
        },
        level_counts={
            "A": sum(
                row.level == "A"
                for row in rows
            ),
            "B": sum(
                row.level == "B"
                for row in rows
            ),
            "C": sum(
                row.level == "C"
                for row in rows
            ),
            "D": sum(
                row.level == "D"
                for row in rows
            ),
        },
    )


# ==========================================================
# Fixture
# ==========================================================


@pytest.fixture
def root() -> ctk.CTk() | None:
    """
    Create a CustomTkinter root for UI tests.

    Some CI environments do not provide a display server.
    Such environments skip the UI tests cleanly.
    """

    try:
        root = ctk.CTk()
    except Exception as exc:
        pytest.skip(
            f"CustomTkinter display unavailable: {exc}"
        )

    root.withdraw()

    yield root

    try:
        root.destroy()
    except Exception:
        pass


# ==========================================================
# Import
# ==========================================================


def test_recommendation_panel_import() -> None:
    """
    RecommendationPanel should be importable.
    """

    assert RecommendationPanel is not None
    assert create_recommendation_panel is not None


# ==========================================================
# Construction
# ==========================================================


def test_panel_can_be_created(
    root: ctk.CTk,
) -> None:
    """
    Panel should be constructible.
    """

    panel = RecommendationPanel(
        root
    )

    assert isinstance(
        panel,
        RecommendationPanel,
    )

    panel.destroy()


def test_convenience_factory_creates_panel(
    root: ctk.CTk,
) -> None:
    """
    Convenience factory should create a panel.
    """

    panel = create_recommendation_panel(
        root
    )

    assert isinstance(
        panel,
        RecommendationPanel,
    )

    panel.destroy()


# ==========================================================
# Empty State
# ==========================================================


def test_panel_starts_empty(
    root: ctk.CTk,
) -> None:
    """
    Panel should start without presentation data.
    """

    panel = RecommendationPanel(
        root
    )

    assert panel.presentation is None

    panel.destroy()


def test_clear_removes_presentation(
    root: ctk.CTk,
) -> None:
    """
    clear() should remove the current presentation.
    """

    presentation = make_presentation(
        (
            make_row(),
        )
    )

    panel = RecommendationPanel(
        root,
        presentation=presentation,
    )

    assert panel.presentation is presentation

    panel.clear()

    assert panel.presentation is None

    panel.destroy()


# ==========================================================
# Presentation
# ==========================================================


def test_set_presentation(
    root: ctk.CTk,
) -> None:
    """
    set_presentation() should store and render data.
    """

    presentation = make_presentation(
        (
            make_row(),
        )
    )

    panel = RecommendationPanel(
        root
    )

    panel.set_presentation(
        presentation
    )

    assert panel.presentation is presentation
    assert (
        panel.title_label.cget(
            "text"
        )
        == "Test Recommendation Report"
    )
    assert (
        panel.generated_at_label.cget(
            "text"
        )
        == "Generated: 2026-08-19 10:30:00"
    )

    panel.destroy()


def test_constructor_accepts_presentation(
    root: ctk.CTk,
) -> None:
    """
    Constructor should accept initial presentation data.
    """

    presentation = make_presentation(
        (
            make_row(),
        )
    )

    panel = RecommendationPanel(
        root,
        presentation=presentation,
    )

    assert panel.presentation is presentation

    panel.destroy()


def test_invalid_presentation_is_rejected(
    root: ctk.CTk,
) -> None:
    """
    Invalid presentation input should raise TypeError.
    """

    panel = RecommendationPanel(
        root
    )

    with pytest.raises(
        TypeError,
        match="presentation must be a "
        "RecommendationReportPresentation",
    ):
        panel.set_presentation(
            "invalid"  # type: ignore[arg-type]
        )

    panel.destroy()


# ==========================================================
# Metrics
# ==========================================================


def test_metrics_are_rendered(
    root: ctk.CTk,
) -> None:
    """
    Main report metrics should be rendered.
    """

    presentation = make_presentation(
        (
            make_row(
                score=8.75,
                risk_score=1.25,
            ),
        )
    )

    panel = RecommendationPanel(
        root,
        presentation=presentation,
    )

    assert (
        panel.ranked_metric["value"].cget(
            "text"
        )
        == "10"
    )

    assert (
        panel.total_metric["value"].cget(
            "text"
        )
        == "1"
    )

    assert (
        panel.active_metric["value"].cget(
            "text"
        )
        == "1"
    )

    assert (
        panel.highest_score_metric["value"].cget(
            "text"
        )
        == "8.75"
    )

    assert (
        panel.lowest_risk_metric["value"].cget(
            "text"
        )
        == "1.25"
    )

    panel.destroy()


# ==========================================================
# Action / Level Summary
# ==========================================================


def test_action_summary_is_rendered(
    root: ctk.CTk,
) -> None:
    """
    Action counts should be rendered.
    """

    presentation = make_presentation(
        (
            make_row(
                action="BUY"
            ),
            make_row(
                symbol="SELL",
                action="SELL",
                level="B",
            ),
            make_row(
                symbol="WATCH",
                action="WATCH",
                level="C",
            ),
            make_row(
                symbol="REJECT",
                action="REJECT",
                level="D",
            ),
        )
    )

    panel = RecommendationPanel(
        root,
        presentation=presentation,
    )

    assert (
        panel.action_label.cget(
            "text"
        )
        == "BUY 1   SELL 1   WATCH 1   REJECT 1"
    )

    assert (
        panel.level_label.cget(
            "text"
        )
        == "A 1   B 1   C 1   D 1"
    )

    panel.destroy()


# ==========================================================
# Top Recommendation
# ==========================================================


def test_top_recommendation_is_rendered(
    root: ctk.CTk,
) -> None:
    """
    Top recommendation should be rendered.
    """

    presentation = make_presentation(
        (
            make_row(
                symbol="TOP-CONTRACT",
                action="BUY",
                level="A",
            ),
        )
    )

    panel = RecommendationPanel(
        root,
        presentation=presentation,
    )

    assert (
        panel.top_label.cget(
            "text"
        )
        == "TOP-CONTRACT   BUY   Level A"
    )

    assert (
        panel.risk_label.cget(
            "text"
        )
        == "Risk status: Active recommendation"
    )

    panel.destroy()


def test_empty_top_is_rendered(
    root: ctk.CTk,
) -> None:
    """
    Empty report should show no top recommendation.
    """

    presentation = make_presentation()

    panel = RecommendationPanel(
        root,
        presentation=presentation,
    )

    assert (
        panel.top_label.cget(
            "text"
        )
        == "--"
    )

    assert (
        panel.risk_label.cget(
            "text"
        )
        == "Risk status: No active recommendation"
    )

    panel.destroy()


def test_high_risk_status_is_rendered(
    root: ctk.CTk,
) -> None:
    """
    High-risk status should be visible.
    """

    presentation = make_presentation(
        (
            make_row(
                action="REJECT",
                level="D",
                risk_score=9.0,
            ),
        ),
        has_high_risk=True,
    )

    panel = RecommendationPanel(
        root,
        presentation=presentation,
    )

    assert (
        panel.risk_label.cget(
            "text"
        )
        == "Risk status: HIGH RISK"
    )

    panel.destroy()


# ==========================================================
# Row Rendering
# ==========================================================


def test_rows_are_rendered(
    root: ctk.CTk,
) -> None:
    """
    Recommendation rows should be rendered.
    """

    presentation = make_presentation(
        (
            make_row(
                symbol="ONE"
            ),
            make_row(
                symbol="TWO",
                action="SELL",
                level="B",
            ),
        )
    )

    panel = RecommendationPanel(
        root,
        presentation=presentation,
    )

    assert len(
        panel._table_widgets
    ) > 0

    panel.destroy()


def test_empty_rows_show_empty_message(
    root: ctk.CTk,
) -> None:
    """
    Empty reports should display an empty-state message.
    """

    presentation = make_presentation()

    panel = RecommendationPanel(
        root,
        presentation=presentation,
    )

    texts = [
        str(
            widget.cget(
                "text"
            )
        )
        for widget in panel._table_widgets
        if hasattr(
            widget,
            "cget",
        )
    ]

    assert "No recommendations" in texts

    panel.destroy()


# ==========================================================
# Formatting Helpers
# ==========================================================


def test_action_color_mapping() -> None:
    """
    Action color mapping should be deterministic.
    """

    assert (
        RecommendationPanel._action_color(
            "BUY"
        )
        != ""
    )

    assert (
        RecommendationPanel._action_color(
            "SELL"
        )
        != ""
    )

    assert (
        RecommendationPanel._action_color(
            "WATCH"
        )
        != ""
    )

    assert (
        RecommendationPanel._action_color(
            "REJECT"
        )
        != ""
    )


def test_level_color_mapping() -> None:
    """
    Level color mapping should be deterministic.
    """

    for level in (
        "A",
        "B",
        "C",
        "D",
    ):
        assert (
            RecommendationPanel._level_color(
                level
            )
            != ""
        )


def test_risk_color_mapping() -> None:
    """
    Risk color mapping should be deterministic.
    """

    assert (
        RecommendationPanel._risk_color(
            2.0
        )
        != ""
    )

    assert (
        RecommendationPanel._risk_color(
            5.0
        )
        != ""
    )

    assert (
        RecommendationPanel._risk_color(
            9.0
        )
        != ""
    )


# ==========================================================
# Read-only Data Contract
# ==========================================================


def test_panel_does_not_modify_presentation(
    root: ctk.CTk,
) -> None:
    """
    Rendering should not replace or mutate presentation data.
    """

    row = make_row(
        symbol="IMMUTABLE"
    )

    presentation = make_presentation(
        (
            row,
        )
    )

    original_rows = presentation.rows
    original_counts = dict(
        presentation.action_counts
    )
    original_levels = dict(
        presentation.level_counts
    )

    panel = RecommendationPanel(
        root,
        presentation=presentation,
    )

    assert presentation.rows == original_rows
    assert presentation.action_counts == original_counts
    assert presentation.level_counts == original_levels

    panel.destroy()


# ==========================================================
# Dynamic Replacement
# ==========================================================


def test_presentation_can_be_replaced(
    root: ctk.CTk,
) -> None:
    """
    A panel should support replacing its presentation.
    """

    first = make_presentation(
        (
            make_row(
                symbol="FIRST"
            ),
        )
    )

    second = make_presentation(
        (
            make_row(
                symbol="SECOND",
                action="SELL",
                level="B",
            ),
        )
    )

    panel = RecommendationPanel(
        root,
        presentation=first,
    )

    assert panel.presentation is first

    panel.set_presentation(
        second
    )

    assert panel.presentation is second

    assert (
        panel.top_label.cget(
            "text"
        )
        == "SECOND   SELL   Level B"
    )

    panel.destroy()


# ==========================================================
# Clear and Reuse
# ==========================================================


def test_panel_can_be_cleared_and_reused(
    root: ctk.CTk,
) -> None:
    """
    Panel should support clear -> set workflow.
    """

    presentation = make_presentation(
        (
            make_row(
                symbol="REUSED"
            ),
        )
    )

    panel = RecommendationPanel(
        root,
        presentation=presentation,
    )

    panel.clear()

    assert panel.presentation is None

    panel.set_presentation(
        presentation
    )

    assert panel.presentation is presentation

    assert (
        panel.top_label.cget(
            "text"
        )
        == "REUSED   BUY   Level A"
    )

    panel.destroy()