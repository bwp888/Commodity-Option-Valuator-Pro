"""
Commodity Option Valuator Pro
=============================

Tests for ApplicationFrame Recommendation Panel Integration.

Commit 0024
-----------

Author : Simon
Version : 0.6.4
"""

from __future__ import annotations

from datetime import datetime

import customtkinter as ctk
import pytest

from core.recommendation_report_presentation import (
    RecommendationReportPresentation,
    RecommendationReportPresentationRow,
)

from ui.app import (
    ApplicationFrame,
    PAGE_TITLES,
)

from ui.recommendation_panel import (
    RecommendationPanel,
)


# ==========================================================
# Test Data
# ==========================================================


def make_row(
    symbol: str = "TEST-C-100",
) -> RecommendationReportPresentationRow:
    """Create deterministic presentation-row data."""

    return RecommendationReportPresentationRow(
        symbol=symbol,
        action="BUY",
        action_title="BUY",
        action_description="buy",
        level="A",
        level_title="A",
        level_description="test level",
        score=5.0,
        risk_score=2.0,
        score_text="5.00",
        risk_score_text="2.00",
        reason="test reason",
        risk_warning=None,
        risk_warning_text="",
    )


def make_presentation(
    rows: tuple[
        RecommendationReportPresentationRow,
        ...,
    ] = (),
) -> RecommendationReportPresentation:
    """Create deterministic recommendation presentation."""

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
        total_count=len(rows),
        total_count_text=str(
            len(rows)
        ),
        active_count=1 if rows else 0,
        active_count_text=(
            "1"
            if rows
            else "0"
        ),
        has_active_recommendation=bool(
            rows
        ),
        has_high_risk=False,
        highest_score=5.0 if rows else None,
        highest_score_text=(
            "5.00"
            if rows
            else "--"
        ),
        lowest_risk_score=2.0 if rows else None,
        lowest_risk_score_text=(
            "2.00"
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
            "BUY": 1 if rows else 0,
            "SELL": 0,
            "WATCH": 0,
            "REJECT": 0,
        },
        level_counts={
            "A": 1 if rows else 0,
            "B": 0,
            "C": 0,
            "D": 0,
        },
    )


# ==========================================================
# Fixtures
# ==========================================================


@pytest.fixture(scope="module")
def root():
    """
    Create one CustomTkinter root for the entire test module.

    CustomTkinter registers internal Tk ``after`` callbacks.
    Recreating and destroying the Tk root for every test can leave
    callbacks associated with a destroyed Tcl interpreter and cause
    intermittent Tcl/Tk initialization failures.

    A module-scoped root keeps one Tcl/Tk interpreter alive for all
    UI integration tests while the ApplicationFrame fixture remains
    function-scoped for test isolation.
    """

    root = ctk.CTk()

    root.withdraw()

    try:
        yield root
    finally:
        root.destroy()


@pytest.fixture
def app(root):
    """
    Create an ApplicationFrame.
    """

    application = ApplicationFrame(
        root
    )

    application.pack(
        fill="both",
        expand=True,
    )

    root.update_idletasks()

    return application


# ==========================================================
# Page Metadata
# ==========================================================


def test_reports_page_exists() -> None:
    """Reports page should remain part of application navigation."""

    assert "reports" in PAGE_TITLES

    assert PAGE_TITLES[
        "reports"
    ] == "推荐报告"


# ==========================================================
# Reports Page Creation
# ==========================================================


def test_reports_page_is_recommendation_panel(
    app: ApplicationFrame,
) -> None:
    """Reports page should be backed by RecommendationPanel."""

    app.show_page(
        "reports"
    )

    assert app.current_page == "reports"

    assert "reports" in app.page_widgets

    assert isinstance(
        app.page_widgets[
            "reports"
        ],
        RecommendationPanel,
    )


def test_get_recommendation_panel(
    app: ApplicationFrame,
) -> None:
    """Application should expose its recommendation panel."""

    panel = (
        app.get_recommendation_panel()
    )

    assert isinstance(
        panel,
        RecommendationPanel,
    )

    assert panel is app.page_widgets[
        "reports"
    ]


def test_recommendation_panel_is_lazy(
    app: ApplicationFrame,
) -> None:
    """Recommendation panel should be created lazily."""

    assert "reports" not in app.page_widgets

    panel = (
        app.get_recommendation_panel()
    )

    assert "reports" in app.page_widgets

    assert panel is app.page_widgets[
        "reports"
    ]


# ==========================================================
# Presentation Injection
# ==========================================================


def test_set_recommendation_presentation(
    app: ApplicationFrame,
) -> None:
    """Application should forward presentation to panel."""

    presentation = make_presentation(
        (
            make_row(),
        )
    )

    app.set_recommendation_presentation(
        presentation
    )

    panel = (
        app.get_recommendation_panel()
    )

    assert panel.presentation is presentation


def test_get_recommendation_presentation(
    app: ApplicationFrame,
) -> None:
    """Application should expose current presentation."""

    presentation = make_presentation(
        (
            make_row(
                "TOP",
            ),
        )
    )

    app.set_recommendation_presentation(
        presentation
    )

    result = (
        app.get_recommendation_presentation()
    )

    assert result is presentation

    assert result is not None

    assert result.top_symbol == "TOP"


def test_recommendation_presentation_is_rendered(
    app: ApplicationFrame,
) -> None:
    """Injected presentation should update panel widgets."""

    presentation = make_presentation(
        (
            make_row(
                "RENDER-TEST",
            ),
        )
    )

    app.set_recommendation_presentation(
        presentation
    )

    panel = (
        app.get_recommendation_panel()
    )

    assert panel.title_label.cget(
        "text"
    ) == "Test Recommendation Report"

    assert panel.generated_at_label.cget(
        "text"
    ) == "Generated: 2026-08-19 10:30:00"

    assert panel.ranked_metric[
        "value"
    ].cget(
        "text"
    ) == "10"

    assert panel.total_metric[
        "value"
    ].cget(
        "text"
    ) == "1"

    assert panel.active_metric[
        "value"
    ].cget(
        "text"
    ) == "1"


# ==========================================================
# Type Validation
# ==========================================================


def test_set_recommendation_presentation_rejects_invalid_input(
    app: ApplicationFrame,
) -> None:
    """Invalid presentation input should be rejected."""

    with pytest.raises(
        TypeError,
        match="presentation must be a "
        "RecommendationReportPresentation",
    ):
        app.set_recommendation_presentation(
            "invalid"  # type: ignore[arg-type]
        )


# ==========================================================
# Empty State
# ==========================================================


def test_recommendation_panel_starts_empty(
    app: ApplicationFrame,
) -> None:
    """Recommendation panel should start in an empty state."""

    panel = (
        app.get_recommendation_panel()
    )

    assert panel.presentation is None

    assert panel.title_label.cget(
        "text"
    ) == "Recommendation Report"

    assert panel.ranked_metric[
        "value"
    ].cget(
        "text"
    ) == "--"

    assert panel.total_metric[
        "value"
    ].cget(
        "text"
    ) == "--"


def test_clear_recommendation_report(
    app: ApplicationFrame,
) -> None:
    """Application should be able to clear the report."""

    presentation = make_presentation(
        (
            make_row(),
        )
    )

    app.set_recommendation_presentation(
        presentation
    )

    assert (
        app.get_recommendation_presentation()
        is not None
    )

    app.clear_recommendation_report()

    assert (
        app.get_recommendation_presentation()
        is None
    )

    panel = (
        app.get_recommendation_panel()
    )

    assert panel.title_label.cget(
        "text"
    ) == "Recommendation Report"

    assert panel.ranked_metric[
        "value"
    ].cget(
        "text"
    ) == "--"


# ==========================================================
# Navigation
# ==========================================================


def test_navigation_to_reports_page(
    app: ApplicationFrame,
) -> None:
    """Reports navigation should display the recommendation panel."""

    app.show_page(
        "dashboard"
    )

    assert app.current_page == "dashboard"

    app.show_page(
        "reports"
    )

    assert app.current_page == "reports"

    assert isinstance(
        app.page_widgets[
            "reports"
        ],
        RecommendationPanel,
    )


def test_navigation_preserves_recommendation_data(
    app: ApplicationFrame,
) -> None:
    """Switching pages should preserve the report presentation."""

    presentation = make_presentation(
        (
            make_row(
                "PERSIST",
            ),
        )
    )

    app.set_recommendation_presentation(
        presentation
    )

    app.show_page(
        "dashboard"
    )

    app.show_page(
        "reports"
    )

    result = (
        app.get_recommendation_presentation()
    )

    assert result is presentation

    assert result is not None

    assert result.top_symbol == "PERSIST"


# ==========================================================
# Existing Scanner Boundary
# ==========================================================


def test_scanner_page_remains_available(
    app: ApplicationFrame,
) -> None:
    """Adding recommendation UI must not break scanner access."""

    scanner = (
        app.get_scanner_page()
    )

    assert scanner is not None

    assert "scanner" in app.page_widgets


# ==========================================================
# Public API
# ==========================================================


def test_application_frame_public_api() -> None:
    """ApplicationFrame should expose expected recommendation methods."""

    assert hasattr(
        ApplicationFrame,
        "get_recommendation_panel",
    )

    assert hasattr(
        ApplicationFrame,
        "set_recommendation_presentation",
    )

    assert hasattr(
        ApplicationFrame,
        "get_recommendation_presentation",
    )

    assert hasattr(
        ApplicationFrame,
        "clear_recommendation_report",
    )