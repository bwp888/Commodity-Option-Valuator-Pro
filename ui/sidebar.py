"""
Commodity Option Valuator Pro
=============================

Application Sidebar.

Commit 0008
------------

Author : Simon
Version : 0.2.0
"""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from ui.styles import (
    COLOR_BACKGROUND,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SURFACE,
    COLOR_TEXT,
    COLOR_TEXT_SECONDARY,
    FONT_BODY_SIZE,
    FONT_FAMILY,
    FONT_SMALL_SIZE,
    SIDEBAR_WIDTH,
)


# ==========================================================
# Navigation
# ==========================================================

NAVIGATION_ITEMS: list[tuple[str, str]] = [
    ("dashboard", "首页"),
    ("valuation", "期权估值"),
    ("scanner", "期权扫描"),
    ("risk", "风险分析"),
    ("market", "行情数据"),
    ("charts", "图表分析"),
    ("reports", "报告中心"),
]


# ==========================================================
# Sidebar
# ==========================================================

class Sidebar(ctk.CTkFrame):
    """
    Main navigation sidebar.
    """

    def __init__(
        self,
        master,
        on_navigate: Callable[[str], None] | None = None,
        **kwargs,
    ) -> None:

        super().__init__(
            master,
            width=SIDEBAR_WIDTH,
            fg_color=COLOR_BACKGROUND,
            corner_radius=0,
            **kwargs,
        )

        self.on_navigate = on_navigate

        self.grid_propagate(
            False
        )

        self.grid_columnconfigure(
            0,
            weight=1,
        )

        self.create_brand()

        self.create_navigation()

        self.create_footer()

    # ======================================================
    # Brand
    # ======================================================

    def create_brand(self) -> None:
        """Create application brand area."""

        self.brand_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )

        self.brand_frame.grid(
            row=0,
            column=0,
            padx=16,
            pady=20,
            sticky="ew",
        )

        self.brand_title = ctk.CTkLabel(
            self.brand_frame,
            text="Commodity",
            text_color=COLOR_TEXT,
            font=(
                FONT_FAMILY,
                18,
                "bold",
            ),
            anchor="w",
        )

        self.brand_title.pack(
            anchor="w"
        )

        self.brand_subtitle = ctk.CTkLabel(
            self.brand_frame,
            text="Option Valuator Pro",
            text_color=COLOR_TEXT_SECONDARY,
            font=(
                FONT_FAMILY,
                FONT_SMALL_SIZE,
            ),
            anchor="w",
        )

        self.brand_subtitle.pack(
            anchor="w",
            pady=(2, 0),
        )

    # ======================================================
    # Navigation
    # ======================================================

    def create_navigation(self) -> None:
        """Create navigation buttons."""

        self.navigation_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )

        self.navigation_frame.grid(
            row=1,
            column=0,
            padx=10,
            pady=10,
            sticky="nsew",
        )

        self.grid_rowconfigure(
            1,
            weight=1,
        )

        self.buttons: dict[
            str,
            ctk.CTkButton,
        ] = {}

        for page_id, label in NAVIGATION_ITEMS:

            button = ctk.CTkButton(
                self.navigation_frame,
                text=label,
                anchor="w",
                height=40,
                fg_color="transparent",
                hover_color=COLOR_PRIMARY_HOVER,
                text_color=COLOR_TEXT_SECONDARY,
                font=(
                    FONT_FAMILY,
                    FONT_BODY_SIZE,
                ),
                corner_radius=6,
                command=lambda pid=page_id: (
                    self.navigate(pid)
                ),
            )

            button.pack(
                fill="x",
                pady=3,
            )

            self.buttons[page_id] = button

    # ======================================================
    # Footer
    # ======================================================

    def create_footer(self) -> None:
        """Create sidebar footer."""

        self.footer = ctk.CTkLabel(
            self,
            text="v0.2.0 · Commit 0008",
            text_color=COLOR_TEXT_SECONDARY,
            font=(
                FONT_FAMILY,
                FONT_SMALL_SIZE,
            ),
        )

        self.footer.grid(
            row=2,
            column=0,
            padx=10,
            pady=12,
            sticky="s",
        )

    # ======================================================
    # Navigation Action
    # ======================================================

    def navigate(
        self,
        page_id: str,
    ) -> None:
        """Navigate to a page."""

        if page_id not in dict(
            NAVIGATION_ITEMS
        ):
            return

        self.set_active(
            page_id
        )

        if self.on_navigate is not None:
            self.on_navigate(
                page_id
            )

    # ======================================================
    # Active State
    # ======================================================

    def set_active(
        self,
        page_id: str,
    ) -> None:
        """Set active navigation item."""

        for current_id, button in (
            self.buttons.items()
        ):

            if current_id == page_id:

                button.configure(
                    fg_color=COLOR_PRIMARY,
                    text_color=COLOR_TEXT,
                )

            else:

                button.configure(
                    fg_color="transparent",
                    text_color=COLOR_TEXT_SECONDARY,
                )


# ==========================================================
# Public Exports
# ==========================================================

__all__ = [
    "NAVIGATION_ITEMS",
    "Sidebar",
]