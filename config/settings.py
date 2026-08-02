"""
Commodity Option Valuator Pro
-----------------------------

Global configuration file.

Author : Simon
Version: v0.1.0
"""

from pathlib import Path


# =========================
# Project Paths
# =========================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = PROJECT_ROOT / "data"
REPORT_DIR = PROJECT_ROOT / "reports"
LOG_DIR = PROJECT_ROOT / "logs"

CONFIG_DIR = PROJECT_ROOT / "config"
CHART_DIR = PROJECT_ROOT / "charts"


# =========================
# Application
# =========================

APP_NAME = "Commodity Option Valuator Pro"

APP_VERSION = "0.1.0"

AUTHOR = "Simon"

WINDOW_WIDTH = 1500

WINDOW_HEIGHT = 900


# =========================
# Theme
# =========================

THEME = "dark"

COLOR_THEME = "blue"


# =========================
# Log
# =========================

LOG_LEVEL = "INFO"

LOG_FILE = LOG_DIR / "application.log"


# =========================
# Chart
# =========================

DEFAULT_FIGSIZE = (10, 6)

DEFAULT_DPI = 120


# =========================
# Create Directories
# =========================

ASSETS_DIR.mkdir(exist_ok=True)

DATA_DIR.mkdir(exist_ok=True)

REPORT_DIR.mkdir(exist_ok=True)

LOG_DIR.mkdir(exist_ok=True)

CHART_DIR.mkdir(exist_ok=True)