"""
Commodity Option Valuator Pro
=============================

Application UI Container.

Commit 0008
------------

Author : Simon
Version : 0.2.0
"""

from __future__ import annotations

import customtkinter as ctk

from ui.sidebar import (
    Sidebar,
)

from ui.dashboard import (
    DashboardPage,
)

from ui.components import (
    PlaceholderPage,
    StatusIndicator,
)

from ui.styles import (
    COLOR_BACKGROUND,
    COLOR_TEXT,
    COLOR_TEXT_SECONDARY,
    HEADER_HEIGHT,
    FONT_FAMILY,
    FONT_BODY_SIZE,
    CONTENT_PADDING,
)


# ==========================================================
# Page Metadata
# ==========================================================


PAGE_TITLES: dict[str, str] = {
    "dashboard": "首页",
    "valuation": "单合约估值",
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

        self.current_page = (
            "dashboard"
        )

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
        """
        Create application sidebar.
        """

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

    # ======================================================
    # Header
    # ======================================================

    def create_header(self) -> None:
        """
        Create top application header.
        """

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
            text="首页",
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

        self.status_indicator = (
            StatusIndicator(
                self.header,
                text="系统就绪",
                status="ready",
            )
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
        """
        Create main page content container.
        """

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

        placeholder_text = {
            "valuation": (
                "单合约估值页面"
            ),
            "scanner": (
                "期权扫描页面"
            ),
            "risk": (
                "风险分析页面"
            ),
            "market": (
                "行情数据页面"
            ),
            "charts": (
                "图表分析页面"
            ),
            "reports": (
                "报告中心页面"
            ),
        }

        return PlaceholderPage(
            self.content,
            title=PAGE_TITLES.get(
                page_id,
                "页面",
            ),
            description=placeholder_text.get(
                page_id,
                "功能页面",
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
        Display requested page.
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
        """
        Update application status.
        """

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