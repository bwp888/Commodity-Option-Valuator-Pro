"""
Commodity Option Valuator Pro
-----------------------------

Application Entry Point

Author : Simon
Version : 0.1.0
Python  : 3.12
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


# ==========================================================
# Logger
# ==========================================================

logger = get_logger()


class CommodityOptionValuatorApp(ctk.CTk):
    """
    Main Application Window.
    """

    def __init__(self) -> None:
        super().__init__()

        logger.info("Initializing application...")

        self.initialize_window()

        logger.info("Application initialized successfully.")

    # ------------------------------------------------------

    def initialize_window(self) -> None:
        """
        Initialize main window.
        """

        self.title(f"{APP_NAME}  v{APP_VERSION}")

        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

        self.minsize(1200, 800)

        # Window centered
        self.center_window()

    # ------------------------------------------------------

    def center_window(self) -> None:
        """
        Center the application window.
        """

        self.update_idletasks()

        width = self.winfo_width()
        height = self.winfo_height()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = int((screen_width - width) / 2)
        y = int((screen_height - height) / 2)

        self.geometry(f"{width}x{height}+{x}+{y}")

    # ------------------------------------------------------

    def run(self) -> None:
        """
        Start application.
        """

        logger.info("Application started.")

        self.mainloop()


# ==========================================================
# Main
# ==========================================================

def main() -> None:
    """
    Application entry.
    """

    logger.info("=" * 60)
    logger.info(APP_NAME)
    logger.info(f"Version : {APP_VERSION}")
    logger.info("=" * 60)

    ctk.set_appearance_mode(THEME)

    ctk.set_default_color_theme(COLOR_THEME)

    app = CommodityOptionValuatorApp()

    app.run()


if __name__ == "__main__":
    main()