"""
Commodity Option Valuator Pro
=============================

Reusable UI Components.

Commit 0008
------------

Author : Simon
Version : 0.2.0
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from ui.styles import (
    COLOR_BORDER,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SUCCESS,
    COLOR_SURFACE,
    COLOR_SURFACE_LIGHT,
    COLOR_TEXT,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    CARD_PADDING,
    CARD_RADIUS,
    CONTENT_PADDING,
    FONT_BODY_SIZE,
    FONT_FAMILY,
    FONT_METRIC_SIZE,
    FONT_SMALL_SIZE,
    FONT_SUBTITLE_SIZE,
)


# ==========================================================
# Metric Card
# ==========================================================

class MetricCard(ctk.CTkFrame):
    """
    Display a single numerical metric.

    Parameters
    ----------
    master:
        Parent widget.

    title:
        Metric title.

    value:
        Main metric value.

    subtitle:
        Optional secondary text.
    """

    def __init__(
        self,
        master,
        title: str = "",
        value: str = "--",
        subtitle: str = "",
        **kwargs,
    ) -> None:

        super().__init__(
            master,
            fg_color=COLOR_SURFACE,
            border_width=1,
            border_color=COLOR_BORDER,
            corner_radius=CARD_RADIUS,
            **kwargs,
        )

        self.grid_columnconfigure(
            0,
            weight=1,
        )

        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            text_color=COLOR_TEXT_SECONDARY,
            font=(
                FONT_FAMILY,
                FONT_SMALL_SIZE,
            ),
            anchor="w",
        )

        self.title_label.grid(
            row=0,
            column=0,
            padx=CARD_PADDING,
            pady=(
                CARD_PADDING,
                4,
            ),
            sticky="w",
        )

        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            text_color=COLOR_TEXT,
            font=(
                FONT_FAMILY,
                FONT_METRIC_SIZE,
                "bold",
            ),
            anchor="w",
        )

        self.value_label.grid(
            row=1,
            column=0,
            padx=CARD_PADDING,
            pady=4,
            sticky="w",
        )

        self.subtitle_label = ctk.CTkLabel(
            self,
            text=subtitle,
            text_color=COLOR_TEXT_SECONDARY,
            font=(
                FONT_FAMILY,
                FONT_SMALL_SIZE,
            ),
            anchor="w",
        )

        self.subtitle_label.grid(
            row=2,
            column=0,
            padx=CARD_PADDING,
            pady=(
                4,
                CARD_PADDING,
            ),
            sticky="w",
        )

    def set_value(
        self,
        value: str,
    ) -> None:
        """Update the displayed metric value."""

        self.value_label.configure(
            text=value
        )

    def set_title(
        self,
        title: str,
    ) -> None:
        """Update the metric title."""

        self.title_label.configure(
            text=title
        )


# ==========================================================
# Section Card
# ==========================================================

class SectionCard(ctk.CTkFrame):
    """
    Reusable section container.

    Provides a title and a content frame.
    """

    def __init__(
        self,
        master,
        title: str = "",
        **kwargs,
    ) -> None:

        super().__init__(
            master,
            fg_color=COLOR_SURFACE,
            border_width=1,
            border_color=COLOR_BORDER,
            corner_radius=CARD_RADIUS,
            **kwargs,
        )

        self.grid_columnconfigure(
            0,
            weight=1,
        )

        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            text_color=COLOR_TEXT,
            font=(
                FONT_FAMILY,
                FONT_SUBTITLE_SIZE,
                "bold",
            ),
            anchor="w",
        )

        self.title_label.grid(
            row=0,
            column=0,
            padx=CARD_PADDING,
            pady=(
                CARD_PADDING,
                8,
            ),
            sticky="w",
        )

        self.content = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )

        self.content.grid(
            row=1,
            column=0,
            padx=CARD_PADDING,
            pady=(
                0,
                CARD_PADDING,
            ),
            sticky="nsew",
        )

        self.grid_rowconfigure(
            1,
            weight=1,
        )

    def set_title(
        self,
        title: str,
    ) -> None:
        """Update the section title."""

        self.title_label.configure(
            text=title
        )


# ==========================================================
# Status Indicator
# ==========================================================

class StatusIndicator(ctk.CTkFrame):
    """
    Display application/system status.
    """

    STATUS_COLORS = {
        "ready": COLOR_SUCCESS,
        "success": COLOR_SUCCESS,
        "warning": COLOR_WARNING,
        "error": COLOR_DANGER,
        "danger": COLOR_DANGER,
        "info": COLOR_PRIMARY,
    }

    def __init__(
        self,
        master,
        text: str = "Ready",
        status: str = "ready",
        **kwargs,
    ) -> None:

        super().__init__(
            master,
            fg_color="transparent",
            corner_radius=0,
            **kwargs,
        )

        self.grid_columnconfigure(
            1,
            weight=1,
        )

        self.indicator = ctk.CTkLabel(
            self,
            text="●",
            width=18,
            text_color=COLOR_SUCCESS,
            font=(
                FONT_FAMILY,
                12,
            ),
        )

        self.indicator.grid(
            row=0,
            column=0,
            padx=(
                0,
                4,
            ),
        )

        self.label = ctk.CTkLabel(
            self,
            text=text,
            text_color=COLOR_TEXT_SECONDARY,
            font=(
                FONT_FAMILY,
                FONT_SMALL_SIZE,
            ),
        )

        self.label.grid(
            row=0,
            column=1,
        )

        self.set_status(
            status,
            text,
        )

    def set_status(
        self,
        status: str,
        text: str | None = None,
    ) -> None:
        """
        Update indicator state.
        """

        color = self.STATUS_COLORS.get(
            status.lower(),
            COLOR_PRIMARY,
        )

        self.indicator.configure(
            text_color=color
        )

        if text is not None:
            self.label.configure(
                text=text
            )


# ==========================================================
# Primary Button
# ==========================================================

class PrimaryButton(ctk.CTkButton):
    """
    Standard primary application button.
    """

    def __init__(
        self,
        master,
        text: str = "确定",
        command: Callable[[], None] | None = None,
        **kwargs,
    ) -> None:

        super().__init__(
            master,
            text=text,
            command=command,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color=COLOR_TEXT,
            corner_radius=6,
            font=(
                FONT_FAMILY,
                FONT_BODY_SIZE,
            ),
            **kwargs,
        )


# ==========================================================
# Placeholder Page
# ==========================================================

class PlaceholderPage(ctk.CTkFrame):
    """
    Temporary page container.

    Used by Commit 0008 for modules whose functional
    implementation will be added in later commits.
    """

    def __init__(
        self,
        master,
        title: str = "功能页面",
        description: str = "功能正在建设中",
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
            0,
            weight=1,
        )

        self.container = ctk.CTkFrame(
            self,
            fg_color=COLOR_SURFACE,
            border_width=1,
            border_color=COLOR_BORDER,
            corner_radius=CARD_RADIUS,
        )

        self.container.grid(
            row=0,
            column=0,
            padx=CONTENT_PADDING,
            pady=CONTENT_PADDING,
            sticky="nsew",
        )

        self.container.grid_columnconfigure(
            0,
            weight=1,
        )

        self.container.grid_rowconfigure(
            1,
            weight=1,
        )

        self.title_label = ctk.CTkLabel(
            self.container,
            text=title,
            text_color=COLOR_TEXT,
            font=(
                FONT_FAMILY,
                22,
                "bold",
            ),
        )

        self.title_label.grid(
            row=0,
            column=0,
            padx=CONTENT_PADDING,
            pady=CONTENT_PADDING,
        )

        self.description_label = ctk.CTkLabel(
            self.container,
            text=description,
            text_color=COLOR_TEXT_SECONDARY,
            font=(
                FONT_FAMILY,
                FONT_BODY_SIZE,
            ),
        )

        self.description_label.grid(
            row=1,
            column=0,
            padx=CONTENT_PADDING,
            pady=CONTENT_PADDING,
        )


# ==========================================================
# Public Exports
# ==========================================================

__all__ = [
    "MetricCard",
    "SectionCard",
    "StatusIndicator",
    "PrimaryButton",
    "PlaceholderPage",
]