"""
Commodity Option Valuator Pro
=============================

Dashboard Page.

Commit 0008
------------

Author : Simon
Version : 0.2.0
"""

from __future__ import annotations

import customtkinter as ctk

from ui.components import (
    MetricCard,
    SectionCard,
)
from ui.styles import (
    COLOR_TEXT,
    COLOR_TEXT_SECONDARY,
    CONTENT_PADDING,
    FONT_BODY_SIZE,
    FONT_FAMILY,
    FONT_TITLE_SIZE,
)


# ==========================================================
# Dashboard Page
# ==========================================================

class DashboardPage(ctk.CTkFrame):
    """
    Main dashboard page.

    Commit 0008 provides the UI structure only.
    Actual market and valuation data will be connected
    in subsequent commits.
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
            2,
            weight=1,
        )

        self.create_header()

        self.create_metrics()

        self.create_overview()

    # ======================================================
    # Header
    # ======================================================

    def create_header(self) -> None:
        """Create dashboard heading."""

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
            text="期权估值分析",
            text_color=COLOR_TEXT,
            font=(
                FONT_FAMILY,
                FONT_TITLE_SIZE,
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
            text="商品期权市场监控与估值概览",
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
    # Metrics
    # ======================================================

    def create_metrics(self) -> None:
        """Create summary metric cards."""

        self.metrics_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )

        self.metrics_frame.grid(
            row=1,
            column=0,
            padx=CONTENT_PADDING,
            pady=(0, CONTENT_PADDING),
            sticky="ew",
        )

        for column in range(4):

            self.metrics_frame.grid_columnconfigure(
                column,
                weight=1,
            )

        self.market_metric = MetricCard(
            self.metrics_frame,
            title="监控合约",
            value="--",
            subtitle="当前市场数据",
        )

        self.market_metric.grid(
            row=0,
            column=0,
            padx=6,
            sticky="ew",
        )

        self.valuation_metric = MetricCard(
            self.metrics_frame,
            title="估值机会",
            value="--",
            subtitle="待扫描",
        )

        self.valuation_metric.grid(
            row=0,
            column=1,
            padx=6,
            sticky="ew",
        )

        self.risk_metric = MetricCard(
            self.metrics_frame,
            title="风险等级",
            value="--",
            subtitle="待计算",
        )

        self.risk_metric.grid(
            row=0,
            column=2,
            padx=6,
            sticky="ew",
        )

        self.iv_metric = MetricCard(
            self.metrics_frame,
            title="平均隐含波动率",
            value="--",
            subtitle="IV",
        )

        self.iv_metric.grid(
            row=0,
            column=3,
            padx=6,
            sticky="ew",
        )

    # ======================================================
    # Overview
    # ======================================================

    def create_overview(self) -> None:
        """Create dashboard overview section."""

        self.overview = SectionCard(
            self,
            title="市场概览",
        )

        self.overview.grid(
            row=2,
            column=0,
            padx=CONTENT_PADDING,
            pady=(0, CONTENT_PADDING),
            sticky="nsew",
        )

        self.overview.grid_columnconfigure(
            0,
            weight=1,
        )

        self.overview.grid_rowconfigure(
            1,
            weight=1,
        )

        self.description = ctk.CTkLabel(
            self.overview.content,
            text=(
                "Commit 0008 完成基础 UI 框架。"
                "\n"
                "市场行情、Black-Scholes 估值、"
                "Greeks、风险分析和期权扫描功能"
                "将在后续 Commit 中接入。"
            ),
            text_color=COLOR_TEXT_SECONDARY,
            font=(
                FONT_FAMILY,
                FONT_BODY_SIZE,
            ),
            justify="left",
            anchor="nw",
        )

        self.description.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=8,
            anchor="nw",
        )


# ==========================================================
# Public Exports
# ==========================================================

__all__ = [
    "DashboardPage",
]