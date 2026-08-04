"""
Commodity Option Valuator Pro
-----------------------------

Common utility functions.

Author : Simon
Version: v0.1.0
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


def current_time() -> str:
    """
    Return current datetime string.

    Returns
    -------
    str
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def current_date() -> str:
    """
    Return current date.

    Returns
    -------
    str
    """
    return datetime.now().strftime("%Y-%m-%d")


def file_exists(path: str | Path) -> bool:
    """
    Check whether a file exists.

    Parameters
    ----------
    path
        File path.

    Returns
    -------
    bool
    """
    return Path(path).exists()


def ensure_directory(path: str | Path) -> Path:
    """
    Create directory if not exists.

    Parameters
    ----------
    path
        Directory path.

    Returns
    -------
    Path
    """
    directory = Path(path)

    directory.mkdir(parents=True, exist_ok=True)

    return directory


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Convert object to float safely.

    Parameters
    ----------
    value
        Any value.

    default
        Default value.

    Returns
    -------
    float
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    Convert object to integer safely.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def is_number(value: Any) -> bool:
    """
    Check whether object is numeric.
    """
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def percentage(value: float, digits: int = 2) -> str:
    """
    Convert decimal to percentage string.

    Example
    -------
    0.1234 -> 12.34%
    """
    return f"{value * 100:.{digits}f}%"


def round_decimal(value: float, digits: int = 4) -> float:
    """
    Round float.
    """
    return round(value, digits)


def clamp(value: float, minimum: float, maximum: float) -> float:
    """
    Limit value to a range.
    """
    return max(minimum, min(value, maximum))