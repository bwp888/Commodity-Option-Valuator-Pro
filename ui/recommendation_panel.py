"""
Commodity Option Valuator Pro
=============================

Recommendation Panel.

Commit 0023
-----------

Provides the CustomTkinter presentation panel for
RecommendationReportPresentation.

Architecture
------------
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
    ↓
Recommendation Panel
    ↓
CustomTkinter UI

The panel is intentionally read-only.

It does not:
    - calculate recommendation scores,
    - change recommendation decisions,
    - change ranking order,
    - modify report data,
    - modify summary values.

Author : Simon
Version : 0.6.3
Python : 3.12
"""

from __future__ import annotations

import customtkinter as ctk

from core.recommendation_report_presentation import (
    RecommendationReportPresentation,
    RecommendationReportPresentationRow,
)

from ui.styles import (
    CARD_PADDING,
    CARD_RADIUS,
    COLOR_BORDER,
    COLOR_DANGER,
    COLOR_INFO,
    COLOR_SUCCESS,
    COLOR_SURFACE,
    COLOR_SURFACE_LIGHT,
    COLOR_TEXT,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    CONTENT_PADDING,
    FONT_BODY_SIZE,
    FONT_METRIC_SIZE,
    FONT_SMALL_SIZE,
    FONT_SUBTITLE_SIZE,
    FONT_TITLE_SIZE,
)


# ==========================================================
# Recommendation Panel
# ==========================================================


class RecommendationPanel(ctk.CTkFrame):
    """
    CustomTkinter panel for displaying recommendation reports.

    The panel consumes RecommendationReportPresentation only.

    Business logic remains completely outside the UI layer.
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        presentation: RecommendationReportPresentation | None = None,
        **kwargs,
    ) -> None:
        """
        Initialize the recommendation panel.
        """

        super().__init__(
            master,
            fg_color="transparent",
            **kwargs,
        )

        self._presentation: (
            RecommendationReportPresentation | None
        ) = None

        self._build_ui()

        if presentation is not None:
            self.set_presentation(
                presentation
            )
        else:
            self.clear()

    # ======================================================
    # UI Construction
    # ======================================================

    def _build_ui(self) -> None:
        """
        Build the static UI structure.
        """

        self.grid_columnconfigure(
            0,
            weight=1,
        )
        self.grid_rowconfigure(
            3,
            weight=1,
        )

        self._build_header()
        self._build_metrics()
        self._build_summary()
        self._build_table()

    def _build_header(self) -> None:
        """
        Build report header.
        """

        self.header_frame = ctk.CTkFrame(
            self,
            fg_color=COLOR_SURFACE,
            corner_radius=CARD_RADIUS,
            border_width=1,
            border_color=COLOR_BORDER,
        )

        self.header_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=CONTENT_PADDING,
            pady=(
                CONTENT_PADDING,
                8,
            ),
        )

        self.header_frame.grid_columnconfigure(
            0,
            weight=1,
        )

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Recommendation Report",
            font=(
                "Microsoft YaHei",
                FONT_TITLE_SIZE,
                "bold",
            ),
            text_color=COLOR_TEXT,
            anchor="w",
        )

        self.title_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=CARD_PADDING,
            pady=(
                CARD_PADDING,
                4,
            ),
        )

        self.generated_at_label = ctk.CTkLabel(
            self.header_frame,
            text="Generated: --",
            font=(
                "Microsoft YaHei",
                FONT_SMALL_SIZE,
            ),
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        )

        self.generated_at_label.grid(
            row=1,
            column=0,
            sticky="w",
            padx=CARD_PADDING,
            pady=(
                0,
                CARD_PADDING,
            ),
        )

    def _build_metrics(self) -> None:
        """
        Build main metric cards.
        """

        self.metrics_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )

        self.metrics_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=CONTENT_PADDING,
            pady=8,
        )

        for column in range(5):
            self.metrics_frame.grid_columnconfigure(
                column,
                weight=1,
            )

        self.ranked_metric = self._create_metric_card(
            self.metrics_frame,
            0,
            "Ranked",
        )

        self.total_metric = self._create_metric_card(
            self.metrics_frame,
            1,
            "Recommendations",
        )

        self.active_metric = self._create_metric_card(
            self.metrics_frame,
            2,
            "Active",
        )

        self.highest_score_metric = self._create_metric_card(
            self.metrics_frame,
            3,
            "Highest Score",
        )

        self.lowest_risk_metric = self._create_metric_card(
            self.metrics_frame,
            4,
            "Lowest Risk",
        )

    def _create_metric_card(
        self,
        parent: ctk.CTkFrame,
        column: int,
        title: str,
    ) -> dict[str, ctk.CTkLabel]:
        """
        Create one metric card.
        """

        card = ctk.CTkFrame(
            parent,
            fg_color=COLOR_SURFACE,
            corner_radius=CARD_RADIUS,
            border_width=1,
            border_color=COLOR_BORDER,
        )

        card.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=4,
        )

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=(
                "Microsoft YaHei",
                FONT_SMALL_SIZE,
            ),
            text_color=COLOR_TEXT_SECONDARY,
        )

        title_label.pack(
            padx=CARD_PADDING,
            pady=(
                CARD_PADDING,
                2,
            ),
        )

        value_label = ctk.CTkLabel(
            card,
            text="--",
            font=(
                "Microsoft YaHei",
                FONT_METRIC_SIZE,
                "bold",
            ),
            text_color=COLOR_TEXT,
        )

        value_label.pack(
            padx=CARD_PADDING,
            pady=(
                0,
                CARD_PADDING,
            ),
        )

        return {
            "card": card,
            "title": title_label,
            "value": value_label,
        }

    def _build_summary(self) -> None:
        """
        Build action, level, and top recommendation summary.
        """

        self.summary_frame = ctk.CTkFrame(
            self,
            fg_color=COLOR_SURFACE,
            corner_radius=CARD_RADIUS,
            border_width=1,
            border_color=COLOR_BORDER,
        )

        self.summary_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=CONTENT_PADDING,
            pady=8,
        )

        self.summary_frame.grid_columnconfigure(
            0,
            weight=1,
        )
        self.summary_frame.grid_columnconfigure(
            1,
            weight=1,
        )
        self.summary_frame.grid_columnconfigure(
            2,
            weight=2,
        )

        # --------------------------------------------------
        # Action summary
        # --------------------------------------------------

        action_frame = ctk.CTkFrame(
            self.summary_frame,
            fg_color="transparent",
        )

        action_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=CARD_PADDING,
            pady=CARD_PADDING,
        )

        ctk.CTkLabel(
            action_frame,
            text="Actions",
            font=(
                "Microsoft YaHei",
                FONT_SUBTITLE_SIZE,
                "bold",
            ),
            text_color=COLOR_TEXT,
            anchor="w",
        ).pack(
            anchor="w",
        )

        self.action_label = ctk.CTkLabel(
            action_frame,
            text="BUY 0   SELL 0   WATCH 0   REJECT 0",
            font=(
                "Microsoft YaHei",
                FONT_BODY_SIZE,
            ),
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        )

        self.action_label.pack(
            anchor="w",
            pady=(
                6,
                0,
            ),
        )

        # --------------------------------------------------
        # Level summary
        # --------------------------------------------------

        level_frame = ctk.CTkFrame(
            self.summary_frame,
            fg_color="transparent",
        )

        level_frame.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=CARD_PADDING,
            pady=CARD_PADDING,
        )

        ctk.CTkLabel(
            level_frame,
            text="Levels",
            font=(
                "Microsoft YaHei",
                FONT_SUBTITLE_SIZE,
                "bold",
            ),
            text_color=COLOR_TEXT,
            anchor="w",
        ).pack(
            anchor="w",
        )

        self.level_label = ctk.CTkLabel(
            level_frame,
            text="A 0   B 0   C 0   D 0",
            font=(
                "Microsoft YaHei",
                FONT_BODY_SIZE,
            ),
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        )

        self.level_label.pack(
            anchor="w",
            pady=(
                6,
                0,
            ),
        )

        # --------------------------------------------------
        # Top recommendation
        # --------------------------------------------------

        top_frame = ctk.CTkFrame(
            self.summary_frame,
            fg_color=COLOR_SURFACE_LIGHT,
            corner_radius=CARD_RADIUS,
        )

        top_frame.grid(
            row=0,
            column=2,
            sticky="ew",
            padx=CARD_PADDING,
            pady=CARD_PADDING,
        )

        ctk.CTkLabel(
            top_frame,
            text="Top Recommendation",
            font=(
                "Microsoft YaHei",
                FONT_SMALL_SIZE,
            ),
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        ).pack(
            anchor="w",
            padx=CARD_PADDING,
            pady=(
                10,
                2,
            ),
        )

        self.top_label = ctk.CTkLabel(
            top_frame,
            text="--",
            font=(
                "Microsoft YaHei",
                FONT_SUBTITLE_SIZE,
                "bold",
            ),
            text_color=COLOR_INFO,
            anchor="w",
        )

        self.top_label.pack(
            anchor="w",
            padx=CARD_PADDING,
            pady=(
                0,
                10,
            ),
        )

        self.risk_label = ctk.CTkLabel(
            top_frame,
            text="Risk status: --",
            font=(
                "Microsoft YaHei",
                FONT_SMALL_SIZE,
            ),
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        )

        self.risk_label.pack(
            anchor="w",
            padx=CARD_PADDING,
            pady=(
                0,
                10,
            ),
        )

    def _build_table(self) -> None:
        """
        Build recommendation table area.
        """

        self.table_frame = ctk.CTkFrame(
            self,
            fg_color=COLOR_SURFACE,
            corner_radius=CARD_RADIUS,
            border_width=1,
            border_color=COLOR_BORDER,
        )

        self.table_frame.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=CONTENT_PADDING,
            pady=(
                8,
                CONTENT_PADDING,
            ),
        )

        self.table_frame.grid_columnconfigure(
            0,
            weight=1,
        )
        self.table_frame.grid_rowconfigure(
            1,
            weight=1,
        )

        self.table_title = ctk.CTkLabel(
            self.table_frame,
            text="Recommendations",
            font=(
                "Microsoft YaHei",
                FONT_SUBTITLE_SIZE,
                "bold",
            ),
            text_color=COLOR_TEXT,
            anchor="w",
        )

        self.table_title.grid(
            row=0,
            column=0,
            sticky="w",
            padx=CARD_PADDING,
            pady=(
                CARD_PADDING,
                8,
            ),
        )

        self.table_scroll = ctk.CTkScrollableFrame(
            self.table_frame,
            fg_color="transparent",
        )

        self.table_scroll.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=8,
            pady=8,
        )

        self.table_scroll.grid_columnconfigure(
            0,
            weight=3,
        )
        self.table_scroll.grid_columnconfigure(
            1,
            weight=1,
        )
        self.table_scroll.grid_columnconfigure(
            2,
            weight=1,
        )
        self.table_scroll.grid_columnconfigure(
            3,
            weight=1,
        )
        self.table_scroll.grid_columnconfigure(
            4,
            weight=1,
        )
        self.table_scroll.grid_columnconfigure(
            5,
            weight=3,
        )

        self._table_widgets: list[ctk.CTkBaseClass] = []

    # ======================================================
    # Public Data API
    # ======================================================

    @property
    def presentation(
        self,
    ) -> RecommendationReportPresentation | None:
        """
        Return the currently displayed presentation.
        """

        return self._presentation

    def set_presentation(
        self,
        presentation: RecommendationReportPresentation,
    ) -> None:
        """
        Replace the displayed presentation.
        """

        if not isinstance(
            presentation,
            RecommendationReportPresentation,
        ):
            raise TypeError(
                "presentation must be a "
                "RecommendationReportPresentation"
            )

        self._presentation = presentation

        self._render(
            presentation
        )

    def clear(self) -> None:
        """
        Clear all displayed recommendation data.
        """

        self._presentation = None

        self.title_label.configure(
            text="Recommendation Report"
        )

        self.generated_at_label.configure(
            text="Generated: --"
        )

        self._set_metric(
            self.ranked_metric,
            "--",
        )
        self._set_metric(
            self.total_metric,
            "--",
        )
        self._set_metric(
            self.active_metric,
            "--",
        )
        self._set_metric(
            self.highest_score_metric,
            "--",
        )
        self._set_metric(
            self.lowest_risk_metric,
            "--",
        )

        self.action_label.configure(
            text="BUY 0   SELL 0   WATCH 0   REJECT 0"
        )

        self.level_label.configure(
            text="A 0   B 0   C 0   D 0"
        )

        self.top_label.configure(
            text="--"
        )

        self.risk_label.configure(
            text="Risk status: --",
            text_color=COLOR_TEXT_SECONDARY,
        )

        self._clear_table()

    # ======================================================
    # Rendering
    # ======================================================

    def _render(
        self,
        presentation: RecommendationReportPresentation,
    ) -> None:
        """
        Render presentation data into the UI.
        """

        self.title_label.configure(
            text=presentation.title
        )

        self.generated_at_label.configure(
            text=(
                "Generated: "
                + presentation.generated_at_text
            )
        )

        self._set_metric(
            self.ranked_metric,
            presentation.ranked_count_text,
        )

        self._set_metric(
            self.total_metric,
            presentation.total_count_text,
        )

        self._set_metric(
            self.active_metric,
            presentation.active_count_text,
        )

        self._set_metric(
            self.highest_score_metric,
            presentation.highest_score_text,
        )

        self._set_metric(
            self.lowest_risk_metric,
            presentation.lowest_risk_score_text,
        )

        self._render_action_summary(
            presentation
        )

        self._render_level_summary(
            presentation
        )

        self._render_top_summary(
            presentation
        )

        self._render_rows(
            presentation.rows
        )

    @staticmethod
    def _set_metric(
        metric: dict[str, ctk.CTkLabel],
        value: str,
    ) -> None:
        """
        Set a metric card value.
        """

        metric["value"].configure(
            text=value
        )

    def _render_action_summary(
        self,
        presentation: RecommendationReportPresentation,
    ) -> None:
        """
        Render action counts.
        """

        counts = presentation.action_counts

        self.action_label.configure(
            text=(
                f"BUY {counts.get('BUY', 0)}   "
                f"SELL {counts.get('SELL', 0)}   "
                f"WATCH {counts.get('WATCH', 0)}   "
                f"REJECT {counts.get('REJECT', 0)}"
            )
        )

    def _render_level_summary(
        self,
        presentation: RecommendationReportPresentation,
    ) -> None:
        """
        Render level counts.
        """

        counts = presentation.level_counts

        self.level_label.configure(
            text=(
                f"A {counts.get('A', 0)}   "
                f"B {counts.get('B', 0)}   "
                f"C {counts.get('C', 0)}   "
                f"D {counts.get('D', 0)}"
            )
        )

    def _render_top_summary(
        self,
        presentation: RecommendationReportPresentation,
    ) -> None:
        """
        Render top recommendation and risk status.
        """

        if presentation.top_symbol is None:
            self.top_label.configure(
                text="--"
            )
        else:
            action = (
                presentation.top_action
                or "--"
            )

            level = (
                presentation.top_level
                or "--"
            )

            self.top_label.configure(
                text=(
                    f"{presentation.top_symbol}   "
                    f"{action}   "
                    f"Level {level}"
                )
            )

        if presentation.has_high_risk:
            self.risk_label.configure(
                text="Risk status: HIGH RISK",
                text_color=COLOR_DANGER,
            )

        elif presentation.has_active_recommendation:
            self.risk_label.configure(
                text="Risk status: Active recommendation",
                text_color=COLOR_SUCCESS,
            )

        else:
            self.risk_label.configure(
                text="Risk status: No active recommendation",
                text_color=COLOR_WARNING,
            )

    def _clear_table(self) -> None:
        """
        Remove all table rows.
        """

        for widget in self._table_widgets:
            widget.destroy()

        self._table_widgets.clear()

    def _render_rows(
        self,
        rows: tuple[
            RecommendationReportPresentationRow,
            ...,
        ],
    ) -> None:
        """
        Render recommendation rows.
        """

        self._clear_table()

        headers = (
            "Symbol",
            "Action",
            "Level",
            "Score",
            "Risk",
            "Reason",
        )

        for column, header in enumerate(
            headers
        ):
            label = ctk.CTkLabel(
                self.table_scroll,
                text=header,
                font=(
                    "Microsoft YaHei",
                    FONT_SMALL_SIZE,
                    "bold",
                ),
                text_color=COLOR_TEXT_SECONDARY,
                anchor="w",
            )

            label.grid(
                row=0,
                column=column,
                sticky="ew",
                padx=6,
                pady=(
                    4,
                    8,
                ),
            )

            self._table_widgets.append(
                label
            )

        if not rows:
            empty_label = ctk.CTkLabel(
                self.table_scroll,
                text="No recommendations",
                font=(
                    "Microsoft YaHei",
                    FONT_BODY_SIZE,
                ),
                text_color=COLOR_TEXT_SECONDARY,
                anchor="w",
            )

            empty_label.grid(
                row=1,
                column=0,
                columnspan=6,
                sticky="w",
                padx=6,
                pady=16,
            )

            self._table_widgets.append(
                empty_label
            )

            return

        for index, row in enumerate(
            rows,
            start=1,
        ):
            self._render_row(
                index,
                row,
            )

    def _render_row(
        self,
        row_index: int,
        row: RecommendationReportPresentationRow,
    ) -> None:
        """
        Render one recommendation row.
        """

        values = (
            row.symbol,
            row.action_title,
            row.level_title,
            row.score_text,
            row.risk_score_text,
            row.reason,
        )

        for column, value in enumerate(
            values
        ):
            text_color = COLOR_TEXT

            if column == 1:
                text_color = self._action_color(
                    row.action
                )

            elif column == 2:
                text_color = self._level_color(
                    row.level
                )

            elif column == 4:
                text_color = self._risk_color(
                    row.risk_score
                )

            label = ctk.CTkLabel(
                self.table_scroll,
                text=str(value),
                font=(
                    "Microsoft YaHei",
                    FONT_BODY_SIZE,
                ),
                text_color=text_color,
                anchor="w",
            )

            label.grid(
                row=row_index,
                column=column,
                sticky="ew",
                padx=6,
                pady=4,
            )

            self._table_widgets.append(
                label
            )

    # ======================================================
    # Display Colors
    # ======================================================

    @staticmethod
    def _action_color(
        action: str,
    ) -> str:
        """
        Return display color for an action.
        """

        normalized = str(
            action
        ).strip().upper()

        if normalized == "BUY":
            return COLOR_SUCCESS

        if normalized == "SELL":
            return COLOR_DANGER

        if normalized == "WATCH":
            return COLOR_WARNING

        return COLOR_TEXT_SECONDARY

    @staticmethod
    def _level_color(
        level: str,
    ) -> str:
        """
        Return display color for recommendation level.
        """

        normalized = str(
            level
        ).strip().upper()

        if normalized == "A":
            return COLOR_SUCCESS

        if normalized == "B":
            return COLOR_INFO

        if normalized == "C":
            return COLOR_WARNING

        if normalized == "D":
            return COLOR_DANGER

        return COLOR_TEXT_SECONDARY

    @staticmethod
    def _risk_color(
        risk_score: float,
    ) -> str:
        """
        Return display color according to risk score.

        The UI only classifies an already calculated risk score.
        It does not modify or recalculate that score.
        """

        value = float(
            risk_score
        )

        if value >= 7.0:
            return COLOR_DANGER

        if value >= 4.0:
            return COLOR_WARNING

        return COLOR_SUCCESS


# ==========================================================
# Public Convenience Function
# ==========================================================


def create_recommendation_panel(
    master: ctk.CTkBaseClass,
    presentation: RecommendationReportPresentation | None = None,
    **kwargs,
) -> RecommendationPanel:
    """
    Create a RecommendationPanel.
    """

    return RecommendationPanel(
        master,
        presentation=presentation,
        **kwargs,
    )


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "RecommendationPanel",
    "create_recommendation_panel",
]