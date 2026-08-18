"""
Commodity Option Valuator Pro
=============================

UI Theme and Style Definitions.

Commit 0008
------------

Author : Simon
Version : 0.2.0
"""

from __future__ import annotations

import customtkinter as ctk


# ==========================================================
# Colors
# ==========================================================

COLOR_BACKGROUND = "#111827"

COLOR_SURFACE = "#1F2937"

COLOR_SURFACE_LIGHT = "#273449"

COLOR_BORDER = "#374151"

COLOR_TEXT = "#F9FAFB"

COLOR_TEXT_SECONDARY = "#9CA3AF"

COLOR_PRIMARY = "#2563EB"

COLOR_PRIMARY_HOVER = "#1D4ED8"

COLOR_SUCCESS = "#22C55E"

COLOR_WARNING = "#F59E0B"

COLOR_DANGER = "#EF4444"

COLOR_INFO = "#38BDF8"


# ==========================================================
# Layout
# ==========================================================

SIDEBAR_WIDTH = 220

HEADER_HEIGHT = 64

CONTENT_PADDING = 24

CARD_PADDING = 16

CARD_RADIUS = 10


# ==========================================================
# Fonts
# ==========================================================

FONT_FAMILY = "Microsoft YaHei"

FONT_TITLE_SIZE = 24

FONT_SUBTITLE_SIZE = 16

FONT_BODY_SIZE = 13

FONT_SMALL_SIZE = 11

FONT_METRIC_SIZE = 24


# ==========================================================
# Theme
# ==========================================================

def initialize_theme() -> None:
    """
    Initialize the CustomTkinter application theme.

    This function is intentionally idempotent and may be
    called more than once.
    """

    ctk.set_appearance_mode("dark")

    ctk.set_default_color_theme("blue")


# ==========================================================
# Public Exports
# ==========================================================

__all__ = [
    "COLOR_BACKGROUND",
    "COLOR_SURFACE",
    "COLOR_SURFACE_LIGHT",
    "COLOR_BORDER",
    "COLOR_TEXT",
    "COLOR_TEXT_SECONDARY",
    "COLOR_PRIMARY",
    "COLOR_PRIMARY_HOVER",
    "COLOR_SUCCESS",
    "COLOR_WARNING",
    "COLOR_DANGER",
    "COLOR_INFO",
    "SIDEBAR_WIDTH",
    "HEADER_HEIGHT",
    "CONTENT_PADDING",
    "CARD_PADDING",
    "CARD_RADIUS",
    "FONT_FAMILY",
    "FONT_TITLE_SIZE",
    "FONT_SUBTITLE_SIZE",
    "FONT_BODY_SIZE",
    "FONT_SMALL_SIZE",
    "FONT_METRIC_SIZE",
    "initialize_theme",
]