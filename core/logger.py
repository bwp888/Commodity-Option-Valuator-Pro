"""
Commodity Option Valuator Pro
-----------------------------

Global logging module.

Features
--------
- Console logging
- File logging
- Automatic log directory creation
- UTF-8 encoding
- Singleton logger instance

Author : Simon
Version: v0.1.0
"""

from __future__ import annotations

import logging
from logging import Logger
from pathlib import Path

from config.settings import LOG_DIR, LOG_FILE, LOG_LEVEL


class LoggerManager:
    """
    Global logger manager.

    Creates one shared logger instance for the entire application.
    """

    _logger: Logger | None = None

    @classmethod
    def get_logger(cls) -> Logger:
        """
        Return the global logger.

        Returns
        -------
        Logger
            Configured logger instance.
        """
        if cls._logger is not None:
            return cls._logger

        LOG_DIR.mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger("CommodityOptionValuator")

        if logger.handlers:
            cls._logger = logger
            return logger

        logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
        logger.propagate = False

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
        console_handler.setFormatter(formatter)

        # File Handler
        file_handler = logging.FileHandler(
            filename=Path(LOG_FILE),
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        cls._logger = logger

        logger.info("=" * 60)
        logger.info("Commodity Option Valuator Pro Started")
        logger.info("=" * 60)

        return logger


logger = LoggerManager.get_logger()


def get_logger() -> Logger:
    """
    Shortcut function.

    Returns
    -------
    Logger
        Shared logger instance.
    """
    return LoggerManager.get_logger()