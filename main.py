"""
Commodity Option Valuator Pro
=============================

Application Entry Point

Commit 0008
------------
Build modular CustomTkinter application GUI framework.

Author : Simon
Version : 0.2.0
Python : 3.12
"""

from __future__ import annotations

import customtkinter as ctk

from config.settings import (
    APP_NAME,
    APP_VERSION,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    THEME,
    COLOR_THEME,
)

from core.logger import get_logger

from ui.app import ApplicationFrame
from ui.styles import initialize_theme


# ==========================================================
# Logger
# ==========================================================

logger = get_logger()


# ==========================================================
# Main Application
# ==========================================================


class CommodityOptionValuatorApp(ctk.CTk):
    """
    Main application window.
    """

    def __init__(self) -> None:
        super().__init__()

        logger.info(
            "Initializing application..."
        )

        self.initialize_window()

        self.application_frame = (
            ApplicationFrame(
                self
            )
        )

        self.application_frame.pack(
            fill="both",
            expand=True,
        )

        logger.info(
            "Application initialized successfully."
        )

    # ------------------------------------------------------
    # Window Initialization
    # ------------------------------------------------------

    def initialize_window(self) -> None:
        """
        Initialize main application window.
        """

        self.title(
            f"{APP_NAME}  v{APP_VERSION}"
        )

        self.geometry(
            f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
        )

        self.minsize(
            1200,
            800,
        )

        self.center_window()

    # ------------------------------------------------------
    # Center Window
    # ------------------------------------------------------

    def center_window(self) -> None:
        """
        Center the application window.
        """

        self.update_idletasks()

        width = self.winfo_width()
        height = self.winfo_height()

        if width <= 1:
            width = WINDOW_WIDTH

        if height <= 1:
            height = WINDOW_HEIGHT

        screen_width = (
            self.winfo_screenwidth()
        )

        screen_height = (
            self.winfo_screenheight()
        )

        x = int(
            (screen_width - width)
            / 2
        )

        y = int(
            (screen_height - height)
            / 2
        )

        self.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    # ------------------------------------------------------
    # Run
    # ------------------------------------------------------

    def run(self) -> None:
        """
        Start application event loop.
        """

        logger.info(
            "Application started."
        )

        self.mainloop()


# ==========================================================
# Main
# ==========================================================


def main() -> None:
    """
    Application entry point.
    """

    logger.info("=" * 60)
    logger.info(APP_NAME)
    logger.info(
        f"Version : {APP_VERSION}"
    )
    logger.info("=" * 60)

    initialize_theme()

    app = CommodityOptionValuatorApp()

    app.run()


# ==========================================================
# Script Entry
# ==========================================================

if __name__ == "__main__":
    main()