"""
Commodity Option Valuator Pro
=============================

Application UI Container.

Commit 0011
------------

Connect option scanner workspace.

Author : Simon
Version : 0.3.0
"""

from __future__ import annotations

import customtkinter as ctk

from ui.components import (
    PlaceholderPage,
    StatusIndicator,
)

from ui.dashboard import (
    DashboardPage,
)

from ui.scanner import (
    ScannerPage,
)

from ui.sidebar import (
    Sidebar,
)

from ui.styles import (
    COLOR_BACKGROUND,
    COLOR_TEXT,
    CONTENT_PADDING,
    FONT_FAMILY,
    HEADER_HEIGHT,
)


# ==========================================================
# Page Metadata
# ==========================================================


PAGE_TITLES: dict[str, str] = {
    "dashboard": "首页",
    "valuation": "期权估值",
    "scanner": "期权扫描",
    "risk": "风险分析",
    "market": "行情数据",
    "charts": "图表分析",
    "reports": "报告中心",
}


# ==========================================================
# Application Frame
# ==========================================================


class ApplicationFrame(ctk.CTkFrame):
    """
    Main application UI container.

    Responsibilities
    ----------------
    - Sidebar
    - Page navigation
    - Header
    - Page lifecycle
    - Application status
    """

    def __init__(
        self,
        master,
        **kwargs,
    ) -> None:

        super().__init__(
            master,
            fg_color=COLOR_BACKGROUND,
            corner_radius=0,
            **kwargs,
        )

        self.current_page = "dashboard"

        self.page_widgets: dict[
            str,
            ctk.CTkFrame,
        ] = {}

        self.grid_columnconfigure(
            1,
            weight=1,
        )

        self.grid_rowconfigure(
            1,
            weight=1,
        )

        self.create_sidebar()

        self.create_header()

        self.create_content()

        self.show_page(
            "dashboard"
        )

    # ======================================================
    # Sidebar
    # ======================================================

    def create_sidebar(self) -> None:
        """Create application sidebar."""

        self.sidebar = Sidebar(
            self,
            on_navigate=self.show_page,
        )

        self.sidebar.grid(
            row=0,
            column=0,
            rowspan=2,
            sticky="nsew",
        )

        self.sidebar.set_active(
            "dashboard"
        )

    # ======================================================
    # Header
    # ======================================================

    def create_header(self) -> None:
        """Create application header."""

        self.header = ctk.CTkFrame(
            self,
            height=HEADER_HEIGHT,
            corner_radius=0,
            fg_color=COLOR_BACKGROUND,
        )

        self.header.grid(
            row=0,
            column=1,
            sticky="ew",
        )

        self.header.grid_columnconfigure(
            0,
            weight=1,
        )

        self.header.grid_propagate(
            False
        )

        self.page_title = ctk.CTkLabel(
            self.header,
            text=PAGE_TITLES[
                "dashboard"
            ],
            text_color=COLOR_TEXT,
            font=(
                FONT_FAMILY,
                18,
                "bold",
            ),
            anchor="w",
        )

        self.page_title.grid(
            row=0,
            column=0,
            padx=CONTENT_PADDING,
            sticky="w",
        )

        self.status_indicator = StatusIndicator(
            self.header,
            text="系统就绪",
            status="ready",
        )

        self.status_indicator.grid(
            row=0,
            column=1,
            padx=CONTENT_PADDING,
        )

    # ======================================================
    # Content
    # ======================================================

    def create_content(self) -> None:
        """Create main content container."""

        self.content = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )

        self.content.grid(
            row=1,
            column=1,
            sticky="nsew",
        )

        self.content.grid_columnconfigure(
            0,
            weight=1,
        )

        self.content.grid_rowconfigure(
            0,
            weight=1,
        )

    # ======================================================
    # Page Creation
    # ======================================================

    def create_page(
        self,
        page_id: str,
    ) -> ctk.CTkFrame:
        """
        Create a page from its identifier.
        """

        if page_id == "dashboard":

            return DashboardPage(
                self.content
            )

        if page_id == "scanner":

            return ScannerPage(
                self.content
            )

        descriptions: dict[
            str,
            str,
        ] = {
            "valuation": (
                "Black-Scholes 估值、Greeks "
                "和二阶 Taylor 估值功能已接入。"
            ),
            "risk": (
                "风险评分和风险等级分析功能将在后续版本接入。"
            ),
            "market": (
                "文华财经、通达信等市场数据将在后续版本接入。"
            ),
            "charts": (
                "收益曲线、Greeks 曲线和风险图表将在后续版本接入。"
            ),
            "reports": (
                "估值报告和风险分析报告将在后续版本接入。"
            ),
        }

        return PlaceholderPage(
            self.content,
            title=PAGE_TITLES.get(
                page_id,
                "功能页面",
            ),
            description=descriptions.get(
                page_id,
                "功能正在建设中。",
            ),
        )

    # ======================================================
    # Show Page
    # ======================================================

    def show_page(
        self,
        page_id: str,
    ) -> None:
        """
        Display the requested page.
        """

        if page_id not in PAGE_TITLES:
            return

        if page_id not in self.page_widgets:

            self.page_widgets[
                page_id
            ] = self.create_page(
                page_id
            )

        for widget in (
            self.page_widgets.values()
        ):

            widget.grid_forget()

        page = self.page_widgets[
            page_id
        ]

        page.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self.current_page = page_id

        self.page_title.configure(
            text=PAGE_TITLES[
                page_id
            ]
        )

        self.sidebar.set_active(
            page_id
        )

        self.status_indicator.set_status(
            "ready",
            "系统就绪",
        )

    # ======================================================
    # Status
    # ======================================================

    def set_status(
        self,
        status: str,
        text: str,
    ) -> None:
        """Update application status."""

        self.status_indicator.set_status(
            status,
            text,
        )


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "PAGE_TITLES",
    "ApplicationFrame",
]