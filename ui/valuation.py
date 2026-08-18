"""
Commodity Option Valuator Pro
=============================

Option Valuation Workspace.

Commit 0009
------------

Author : Simon
Version : 0.2.1
"""

from __future__ import annotations

import customtkinter as ctk

from ui.components import (
    PrimaryButton,
    SectionCard,
)
from ui.styles import (
    COLOR_TEXT,
    COLOR_TEXT_SECONDARY,
    CONTENT_PADDING,
    FONT_BODY_SIZE,
    FONT_FAMILY,
    FONT_SMALL_SIZE,
    FONT_SUBTITLE_SIZE,
)


# ==========================================================
# Valuation Page
# ==========================================================


class ValuationPage(ctk.CTkFrame):
    """
    Option valuation workspace.

    Commit 0009 provides the valuation workspace UI
    foundation.

    The page is intentionally separated from the
    valuation engine. Core valuation execution will
    be connected in a subsequent commit.
    """

    def __init__(
        self,
        master,
        **kwargs,
    ) -> None:

        super().__init__(
            master,
            fg_color="transparent",
            corner_radius=0,
            **kwargs,
        )

        self.grid_columnconfigure(
            0,
            weight=1,
        )

        self.grid_rowconfigure(
            1,
            weight=1,
        )

        self.create_header()

        self.create_workspace()

    # ======================================================
    # Header
    # ======================================================

    def create_header(self) -> None:
        """Create valuation workspace heading."""

        self.header = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )

        self.header.grid(
            row=0,
            column=0,
            padx=CONTENT_PADDING,
            pady=CONTENT_PADDING,
            sticky="ew",
        )

        self.header.grid_columnconfigure(
            0,
            weight=1,
        )

        self.title = ctk.CTkLabel(
            self.header,
            text="期权估值工作台",
            text_color=COLOR_TEXT,
            font=(
                FONT_FAMILY,
                24,
                "bold",
            ),
            anchor="w",
        )

        self.title.grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.subtitle = ctk.CTkLabel(
            self.header,
            text=(
                "输入期权合约参数，"
                "计算理论价值与风险参数"
            ),
            text_color=COLOR_TEXT_SECONDARY,
            font=(
                FONT_FAMILY,
                FONT_BODY_SIZE,
            ),
            anchor="w",
        )

        self.subtitle.grid(
            row=1,
            column=0,
            pady=(4, 0),
            sticky="w",
        )

    # ======================================================
    # Workspace
    # ======================================================

    def create_workspace(self) -> None:
        """Create valuation workspace."""

        self.workspace = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )

        self.workspace.grid(
            row=1,
            column=0,
            padx=CONTENT_PADDING,
            pady=(0, CONTENT_PADDING),
            sticky="nsew",
        )

        self.workspace.grid_columnconfigure(
            0,
            weight=1,
            uniform="valuation",
        )

        self.workspace.grid_columnconfigure(
            1,
            weight=1,
            uniform="valuation",
        )

        self.workspace.grid_rowconfigure(
            0,
            weight=1,
        )

        self.create_parameter_section()

        self.create_result_section()

    # ======================================================
    # Parameter Section
    # ======================================================

    def create_parameter_section(self) -> None:
        """Create option parameter input section."""

        self.parameter_section = SectionCard(
            self.workspace,
            title="合约参数",
        )

        self.parameter_section.grid(
            row=0,
            column=0,
            padx=(0, 8),
            sticky="nsew",
        )

        self.parameter_section.content.grid_columnconfigure(
            1,
            weight=1,
        )

        self.create_parameter_label(
            row=0,
            text="合约代码",
        )

        self.symbol_entry = self.create_entry(
            row=0,
            placeholder="例如 SR609C5600",
        )

        self.create_parameter_label(
            row=1,
            text="标的价格",
        )

        self.spot_entry = self.create_entry(
            row=1,
            placeholder="例如 5600",
        )

        self.create_parameter_label(
            row=2,
            text="行权价格",
        )

        self.strike_entry = self.create_entry(
            row=2,
            placeholder="例如 5600",
        )

        self.create_parameter_label(
            row=3,
            text="剩余天数",
        )

        self.days_entry = self.create_entry(
            row=3,
            placeholder="例如 30",
        )

        self.create_parameter_label(
            row=4,
            text="波动率",
        )

        self.volatility_entry = self.create_entry(
            row=4,
            placeholder="例如 0.20",
        )

        self.create_parameter_label(
            row=5,
            text="无风险利率",
        )

        self.rate_entry = self.create_entry(
            row=5,
            placeholder="默认 0.025",
        )

        self.create_parameter_label(
            row=6,
            text="期权方向",
        )

        self.direction_selector = ctk.CTkSegmentedButton(
            self.parameter_section.content,
            values=[
                "CALL",
                "PUT",
            ],
        )

        self.direction_selector.set(
            "CALL"
        )

        self.direction_selector.grid(
            row=6,
            column=1,
            padx=(8, 0),
            pady=6,
            sticky="ew",
        )

        self.valuate_button = PrimaryButton(
            self.parameter_section.content,
            text="开始估值",
            command=self.on_valuate,
        )

        self.valuate_button.grid(
            row=7,
            column=0,
            columnspan=2,
            padx=8,
            pady=(18, 8),
            sticky="ew",
        )

        self.parameter_hint = ctk.CTkLabel(
            self.parameter_section.content,
            text=(
                "Commit 0009：完成估值工作台基础界面。"
                "\n"
                "计算引擎将在后续 Commit 接入。"
            ),
            text_color=COLOR_TEXT_SECONDARY,
            font=(
                FONT_FAMILY,
                FONT_SMALL_SIZE,
            ),
            justify="left",
            anchor="w",
        )

        self.parameter_hint.grid(
            row=8,
            column=0,
            columnspan=2,
            padx=8,
            pady=(12, 8),
            sticky="ew",
        )

    # ======================================================
    # Parameter Helpers
    # ======================================================

    def create_parameter_label(
        self,
        row: int,
        text: str,
    ) -> None:
        """Create a parameter label."""

        label = ctk.CTkLabel(
            self.parameter_section.content,
            text=text,
            text_color=COLOR_TEXT_SECONDARY,
            font=(
                FONT_FAMILY,
                FONT_BODY_SIZE,
            ),
            anchor="w",
        )

        label.grid(
            row=row,
            column=0,
            padx=8,
            pady=6,
            sticky="w",
        )

    def create_entry(
        self,
        row: int,
        placeholder: str,
    ) -> ctk.CTkEntry:
        """Create a parameter entry."""

        entry = ctk.CTkEntry(
            self.parameter_section.content,
            placeholder_text=placeholder,
        )

        entry.grid(
            row=row,
            column=1,
            padx=(8, 0),
            pady=6,
            sticky="ew",
        )

        return entry

    # ======================================================
    # Result Section
    # ======================================================

    def create_result_section(self) -> None:
        """Create valuation result section."""

        self.result_section = SectionCard(
            self.workspace,
            title="估值结果",
        )

        self.result_section.grid(
            row=0,
            column=1,
            padx=(8, 0),
            sticky="nsew",
        )

        self.result_section.content.grid_columnconfigure(
            1,
            weight=1,
        )

        self.result_labels: dict[
            str,
            ctk.CTkLabel,
        ] = {}

        result_items = [
            ("theoretical_price", "理论价格"),
            ("delta", "Delta"),
            ("gamma", "Gamma"),
            ("theta", "Theta"),
            ("vega", "Vega"),
            ("difference", "估值差"),
            ("risk_score", "风险评分"),
        ]

        for row, (key, title) in enumerate(
            result_items
        ):

            label = ctk.CTkLabel(
                self.result_section.content,
                text=title,
                text_color=COLOR_TEXT_SECONDARY,
                font=(
                    FONT_FAMILY,
                    FONT_BODY_SIZE,
                ),
                anchor="w",
            )

            label.grid(
                row=row,
                column=0,
                padx=8,
                pady=8,
                sticky="w",
            )

            value_label = ctk.CTkLabel(
                self.result_section.content,
                text="--",
                text_color=COLOR_TEXT,
                font=(
                    FONT_FAMILY,
                    FONT_SUBTITLE_SIZE,
                    "bold",
                ),
                anchor="e",
            )

            value_label.grid(
                row=row,
                column=1,
                padx=8,
                pady=8,
                sticky="e",
            )

            self.result_labels[
                key
            ] = value_label

    # ======================================================
    # Valuation Action
    # ======================================================

    def on_valuate(self) -> None:
        """
        Handle valuation button.

        Commit 0009 intentionally does not execute the
        valuation engine yet. This method establishes
        the UI action boundary for the next commit.
        """

        self.result_labels[
            "theoretical_price"
        ].configure(
            text="待接入"
        )

        self.result_labels[
            "delta"
        ].configure(
            text="待接入"
        )

        self.result_labels[
            "gamma"
        ].configure(
            text="待接入"
        )

        self.result_labels[
            "theta"
        ].configure(
            text="待接入"
        )

        self.result_labels[
            "vega"
        ].configure(
            text="待接入"
        )

        self.result_labels[
            "difference"
        ].configure(
            text="待接入"
        )

        self.result_labels[
            "risk_score"
        ].configure(
            text="待接入"
        )

    # ======================================================
    # Public API
    # ======================================================

    def get_parameters(self) -> dict[str, str]:
        """
        Return current UI parameters.

        The method intentionally returns raw strings.
        Numeric conversion belongs to the valuation layer.
        """

        return {
            "symbol": self.symbol_entry.get(),
            "spot": self.spot_entry.get(),
            "strike": self.strike_entry.get(),
            "days": self.days_entry.get(),
            "volatility": self.volatility_entry.get(),
            "rate": self.rate_entry.get(),
            "direction": self.direction_selector.get(),
        }

    def reset_results(self) -> None:
        """Reset all valuation results."""

        for label in self.result_labels.values():
            label.configure(
                text="--"
            )


# ==========================================================
# Public Exports
# ==========================================================

__all__ = [
    "ValuationPage",
]