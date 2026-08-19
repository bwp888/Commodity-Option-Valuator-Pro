"""
Commodity Option Valuator Pro
=============================

Recommendation Report Presentation.

Commit 0022
-----------

Provides a stable presentation layer above RecommendationReport.

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
    ↓
Recommendation Report Presentation

The presentation layer is intentionally read-only. It does not
change recommendation decisions, ranking order, summary values,
or report contents.

Author : Simon
Version : 0.6.3
Python : 3.12
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.recommendation_report import (
    RecommendationReport,
    RecommendationReportItem,
)


# ==========================================================
# Report Presentation Row
# ==========================================================


@dataclass(frozen=True)
class RecommendationReportPresentationRow:
    """
    UI/report-friendly representation of one report item.

    The row contains already-normalized display values so
    downstream UI and export layers do not need to know the
    internal RecommendationReportItem structure.
    """

    symbol: str

    action: str

    action_title: str

    level: str

    level_title: str

    score: float

    risk_score: float

    score_text: str

    risk_score_text: str

    reason: str

    risk_warning: str | None

    risk_warning_text: str

    action_description: str

    level_description: str


# ==========================================================
# Report Presentation
# ==========================================================


@dataclass(frozen=True)
class RecommendationReportPresentation:
    """
    Complete presentation model for RecommendationReport.

    This class is deliberately independent of any UI framework.

    CustomTkinter, Excel, PDF, CSV, and other output layers can
    consume this structure without depending directly on the
    underlying report model.
    """

    title: str

    generated_at: datetime

    generated_at_text: str

    ranked_count: int

    ranked_count_text: str

    total_count: int

    total_count_text: str

    active_count: int

    active_count_text: str

    has_active_recommendation: bool

    has_high_risk: bool

    highest_score: float | None

    highest_score_text: str

    lowest_risk_score: float | None

    lowest_risk_score_text: str

    top_symbol: str | None

    top_action: str | None

    top_level: str | None

    rows: tuple[
        RecommendationReportPresentationRow,
        ...,
    ]

    action_counts: dict[str, int]

    level_counts: dict[str, int]


# ==========================================================
# Recommendation Report Presenter
# ==========================================================


class RecommendationReportPresenter:
    """
    Convert RecommendationReport into a stable presentation model.

    This class does not change report data.

    It only:
        - validates the report,
        - formats display values,
        - converts report items into rows,
        - exposes summary information in UI-friendly form.
    """

    # ======================================================
    # Validation
    # ======================================================

    @staticmethod
    def _validate_report(
        report: RecommendationReport,
    ) -> None:
        """
        Validate a RecommendationReport instance.
        """

        if not isinstance(
            report,
            RecommendationReport,
        ):
            raise TypeError(
                "report must be a RecommendationReport"
            )

    @staticmethod
    def _validate_item(
        item: RecommendationReportItem,
    ) -> None:
        """
        Validate a RecommendationReportItem instance.
        """

        if not isinstance(
            item,
            RecommendationReportItem,
        ):
            raise TypeError(
                "item must be a RecommendationReportItem"
            )

    # ======================================================
    # Formatting
    # ======================================================

    @staticmethod
    def format_datetime(
        value: datetime,
    ) -> str:
        """
        Format report timestamp for UI and export layers.
        """

        if not isinstance(
            value,
            datetime,
        ):
            raise TypeError(
                "value must be a datetime"
            )

        return value.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    @staticmethod
    def format_score(
        value: float | None,
    ) -> str:
        """
        Format a score for presentation.

        None is represented by '--'.
        """

        if value is None:
            return "--"

        return f"{float(value):.2f}"

    @staticmethod
    def format_count(
        value: int,
    ) -> str:
        """
        Format an integer count for presentation.
        """

        if not isinstance(
            value,
            int,
        ):
            raise TypeError(
                "value must be an int"
            )

        return str(value)

    @staticmethod
    def format_risk_warning(
        warning: str | None,
    ) -> str:
        """
        Normalize an optional risk warning.

        Missing warnings are represented by an empty string,
        which is convenient for table and spreadsheet output.
        """

        if warning is None:
            return ""

        return str(
            warning
        ).strip()

    # ======================================================
    # Action / Level Titles
    # ======================================================

    @staticmethod
    def action_title(
        action: str,
    ) -> str:
        """
        Return a stable display title for an action.
        """

        normalized = str(
            action
        ).strip().upper()

        mapping = {
            "BUY": "BUY",
            "SELL": "SELL",
            "WATCH": "WATCH",
            "REJECT": "REJECT",
        }

        if normalized not in mapping:
            raise ValueError(
                f"invalid recommendation action: {normalized}"
            )

        return mapping[
            normalized
        ]

    @staticmethod
    def level_title(
        level: str,
    ) -> str:
        """
        Return a stable display title for a recommendation level.
        """

        normalized = str(
            level
        ).strip().upper()

        if normalized not in {
            "A",
            "B",
            "C",
            "D",
        }:
            raise ValueError(
                f"invalid recommendation level: {normalized}"
            )

        return normalized

    # ======================================================
    # Single Row
    # ======================================================

    @classmethod
    def present_item(
        cls,
        item: RecommendationReportItem,
    ) -> RecommendationReportPresentationRow:
        """
        Convert one RecommendationReportItem into a presentation row.
        """

        cls._validate_item(
            item
        )

        action = cls.action_title(
            item.action
        )

        level = cls.level_title(
            item.level
        )

        warning_text = cls.format_risk_warning(
            item.risk_warning
        )

        return RecommendationReportPresentationRow(
            symbol=item.symbol,
            action=action,
            action_title=item.action_title,
            level=level,
            level_title=item.level_title,
            score=float(
                item.score
            ),
            risk_score=float(
                item.risk_score
            ),
            score_text=cls.format_score(
                item.score
            ),
            risk_score_text=cls.format_score(
                item.risk_score
            ),
            reason=item.reason,
            risk_warning=item.risk_warning,
            risk_warning_text=warning_text,
            action_description=item.action_description,
            level_description=item.level_description,
        )

    # ======================================================
    # Complete Report
    # ======================================================

    @classmethod
    def present(
        cls,
        report: RecommendationReport,
    ) -> RecommendationReportPresentation:
        """
        Convert a RecommendationReport into a presentation model.
        """

        cls._validate_report(
            report
        )

        rows = tuple(
            cls.present_item(
                item
            )
            for item in report.items
        )

        summary = report.summary

        top_symbol = (
            report.top.symbol
            if report.top is not None
            else None
        )

        top_action = (
            report.top.action
            if report.top is not None
            else None
        )

        top_level = (
            report.top.level
            if report.top is not None
            else None
        )

        return RecommendationReportPresentation(
            title=report.title,
            generated_at=report.generated_at,
            generated_at_text=cls.format_datetime(
                report.generated_at
            ),
            ranked_count=report.ranked_count,
            ranked_count_text=cls.format_count(
                report.ranked_count
            ),
            total_count=report.total_count,
            total_count_text=cls.format_count(
                report.total_count
            ),
            active_count=summary.active_count,
            active_count_text=cls.format_count(
                summary.active_count
            ),
            has_active_recommendation=(
                report.has_active_recommendation
            ),
            has_high_risk=(
                report.has_high_risk
            ),
            highest_score=summary.highest_score,
            highest_score_text=cls.format_score(
                summary.highest_score
            ),
            lowest_risk_score=summary.lowest_risk_score,
            lowest_risk_score_text=cls.format_score(
                summary.lowest_risk_score
            ),
            top_symbol=top_symbol,
            top_action=top_action,
            top_level=top_level,
            rows=rows,
            action_counts=dict(
                summary.action_counts
            ),
            level_counts=dict(
                summary.level_counts
            ),
        )

    # ======================================================
    # Convenience
    # ======================================================

    @classmethod
    def empty(
        cls,
        report: RecommendationReport | None = None,
    ) -> RecommendationReportPresentation:
        """
        Present an empty report.

        If no report is supplied, RecommendationReport.empty()
        is used.
        """

        target = (
            report
            if report is not None
            else RecommendationReport.empty()
        )

        return cls.present(
            target
        )


# ==========================================================
# Public Convenience Function
# ==========================================================


def present_recommendation_report(
    report: RecommendationReport,
) -> RecommendationReportPresentation:
    """
    Convert RecommendationReport into presentation data.
    """

    return RecommendationReportPresenter.present(
        report
    )


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "RecommendationReportPresentationRow",
    "RecommendationReportPresentation",
    "RecommendationReportPresenter",
    "present_recommendation_report",
]