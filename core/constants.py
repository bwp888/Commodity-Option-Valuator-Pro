"""
Commodity Option Valuator Pro

Global constants.
"""

import math


# =========================
# Mathematical Constants
# =========================

PI = math.pi

E = math.e

SQRT_2 = math.sqrt(2.0)

SQRT_2PI = math.sqrt(2.0 * math.pi)


# =========================
# Option Types
# =========================

CALL = "CALL"

PUT = "PUT"


# =========================
# Days
# =========================

TRADING_DAYS = 252

CALENDAR_DAYS = 365


# =========================
# Numerical
# =========================

EPSILON = 1e-10

MAX_ITERATION = 100

IV_TOLERANCE = 1e-8


# =========================
# Risk Score
# =========================

LOW_RISK = 30

MEDIUM_RISK = 60

HIGH_RISK = 80


# =========================
# Supported Commodity Types
# =========================

SUPPORTED_PRODUCTS = [

    "CU",
    "AL",
    "ZN",
    "NI",
    "AU",
    "AG",
    "RB",
    "HC",
    "RU",
    "BU",
    "FU",
    "M",
    "Y",
    "P",
    "C",
    "A",
    "B",
    "CF",
    "SR",
    "TA",
    "MA",
    "OI",
    "RM",
]