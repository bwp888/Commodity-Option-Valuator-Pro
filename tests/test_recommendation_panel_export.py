"""
Commodity Option Valuator Pro
=============================

Tests for Recommendation Panel Excel Export Integration.

Commit 0024
-----------

Tests the UI boundary between RecommendationPanel
and the existing Excel export service.

The tests do not test Excel workbook contents.
That contract is already covered by test_excel_export.py.

Author : Simon
Version : 0.6.4
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import customtkinter as ctk
import pytest

from core.recommendation_report_presentation import (
    RecommendationReportPresentation,
    RecommendationReportPresentationRow,
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
    Create one CustomTkinter root for the module.

    Keeping one Tcl/Tk interpreter alive avoids the
    callback lifecycle issues caused by repeatedly
    creating and destroying CustomTkinter roots.
    """

    root = ctk.CTk()

    root.withdraw()

    try:
        yield root
    finally:
        root.destroy()


@pytest.fixture
def panel(root):
    """Create an empty RecommendationPanel."""

    panel = RecommendationPanel(
        root
    )

    panel.pack(
        fill="both",
        expand=True,
    )

    root.update_idletasks()

    return panel


# ==========================================================
# Public Export API
# ==========================================================


def test_panel_exposes_export_button(
    panel: RecommendationPanel,
) -> None:
    """RecommendationPanel should expose an Excel export button."""

    assert hasattr(
        panel,
        "export_button",
    )


def test_export_button_is_disabled_without_presentation(
    panel: RecommendationPanel,
) -> None:
    """Export should not be available when no report exists."""

    assert panel.presentation is None

    assert panel.export_button.cget(
        "state"
    ) == "disabled"


def test_export_button_is_enabled_with_presentation(
    panel: RecommendationPanel,
) -> None:
    """Export should become available after a report is loaded."""

    presentation = make_presentation(
        (
            make_row(),
        )
    )

    panel.set_presentation(
        presentation
    )

    assert panel.export_button.cget(
        "state"
    ) == "normal"


# ==========================================================
# Save Dialog Boundary
# ==========================================================


def test_export_excel_does_nothing_without_presentation(
    panel: RecommendationPanel,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Export action should safely return when no report exists."""

    called = False

    def fake_export(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(
        "ui.recommendation_panel.export_recommendation_report",
        fake_export,
    )

    result = panel.export_excel()

    assert result is None

    assert called is False


def test_export_excel_cancels_without_writing(
    panel: RecommendationPanel,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cancelling the save dialog should not call the exporter."""

    presentation = make_presentation(
        (
            make_row(),
        )
    )

    panel.set_presentation(
        presentation
    )

    called = False

    def fake_export(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(
        "ui.recommendation_panel.export_recommendation_report",
        fake_export,
    )

    monkeypatch.setattr(
        "ui.recommendation_panel.filedialog.asksaveasfilename",
        lambda **kwargs: "",
    )

    result = panel.export_excel()

    assert result is None

    assert called is False


def test_export_excel_uses_save_dialog(
    panel: RecommendationPanel,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Export action should request a .xlsx output path."""

    presentation = make_presentation(
        (
            make_row(),
        )
    )

    panel.set_presentation(
        presentation
    )

    dialog_kwargs = {}

    def fake_dialog(**kwargs):
        dialog_kwargs.update(
            kwargs
        )

        return "C:/temp/recommendation.xlsx"

    monkeypatch.setattr(
        "ui.recommendation_panel.filedialog.asksaveasfilename",
        fake_dialog,
    )

    monkeypatch.setattr(
        "ui.recommendation_panel.export_recommendation_report",
        lambda *args, **kwargs: Path(
            "C:/temp/recommendation.xlsx"
        ),
    )

    panel.export_excel()

    assert dialog_kwargs["defaultextension"] == ".xlsx"

    assert (
        ("Excel 文件", "*.xlsx")
        in dialog_kwargs["filetypes"]
    )


# ==========================================================
# Export Service Boundary
# ==========================================================


def test_export_excel_passes_current_presentation_to_exporter(
    panel: RecommendationPanel,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Panel should pass its current presentation unchanged."""

    presentation = make_presentation(
        (
            make_row(
                "EXPORT-TEST",
            ),
        )
    )

    panel.set_presentation(
        presentation
    )

    output_path = Path(
        "C:/temp/export-test.xlsx"
    )

    monkeypatch.setattr(
        "ui.recommendation_panel.filedialog.asksaveasfilename",
        lambda **kwargs: str(
            output_path
        ),
    )

    calls = []

    def fake_export(
        current_presentation,
        current_output_path,
    ):
        calls.append(
            (
                current_presentation,
                current_output_path,
            )
        )

        return output_path

    monkeypatch.setattr(
        "ui.recommendation_panel.export_recommendation_report",
        fake_export,
    )

    result = panel.export_excel()

    assert len(calls) == 1

    assert calls[0][0] is presentation

    assert calls[0][1] == str(
        output_path
    )

    assert result == output_path


def test_export_excel_returns_exporter_result(
    panel: RecommendationPanel,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Panel export action should return the exporter result."""

    presentation = make_presentation(
        (
            make_row(),
        )
    )

    panel.set_presentation(
        presentation
    )

    output_path = Path(
        "C:/temp/result.xlsx"
    )

    monkeypatch.setattr(
        "ui.recommendation_panel.filedialog.asksaveasfilename",
        lambda **kwargs: str(
            output_path
        ),
    )

    monkeypatch.setattr(
        "ui.recommendation_panel.export_recommendation_report",
        lambda presentation, output_path: Path(
            output_path
        ).resolve(),
    )

    result = panel.export_excel()

    assert result == output_path.resolve()


# ==========================================================
# Presentation Lifecycle
# ==========================================================


def test_clear_disables_export_button(
    panel: RecommendationPanel,
) -> None:
    """Clearing the report should disable Excel export again."""

    presentation = make_presentation(
        (
            make_row(),
        )
    )

    panel.set_presentation(
        presentation
    )

    assert panel.export_button.cget(
        "state"
    ) == "normal"

    panel.clear()

    assert panel.presentation is None

    assert panel.export_button.cget(
        "state"
    ) == "disabled"


# ==========================================================
# Public Method Contract
# ==========================================================


def test_export_excel_is_public_panel_api() -> None:
    """RecommendationPanel should expose export_excel()."""

    assert hasattr(
        RecommendationPanel,
        "export_excel",
    )