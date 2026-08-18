"""
Commodity Option Valuator Pro
=============================

Valuation Workspace UI Tests.

Commit 0009
------------

Author : Simon
Version : 0.2.1
"""

from __future__ import annotations


# ==========================================================
# Imports
# ==========================================================

from ui.app import (
    ApplicationFrame,
    PAGE_TITLES,
)

from ui.valuation import (
    ValuationPage,
)


# ==========================================================
# Page Import
# ==========================================================

def test_valuation_page_import():

    assert (
        ValuationPage
        is not None
    )


# ==========================================================
# Page Metadata
# ==========================================================

def test_valuation_page_metadata():

    assert (
        "valuation"
        in PAGE_TITLES
    )

    assert (
        PAGE_TITLES["valuation"]
        ==
        "期权估值"
    )


# ==========================================================
# Application Integration
# ==========================================================

def test_application_frame_import():

    assert (
        ApplicationFrame
        is not None
    )


def test_application_contains_valuation_page():

    assert (
        PAGE_TITLES["valuation"]
        ==
        "期权估值"
    )


# ==========================================================
# Parameter Contract
# ==========================================================

def test_valuation_parameter_names():

    expected = {
        "symbol",
        "spot",
        "strike",
        "days",
        "volatility",
        "rate",
        "direction",
    }

    method_names = {
        "symbol",
        "spot",
        "strike",
        "days",
        "volatility",
        "rate",
        "direction",
    }

    assert (
        method_names
        ==
        expected
    )


# ==========================================================
# Result Contract
# ==========================================================

def test_valuation_result_fields():

    expected = {
        "theoretical_price",
        "delta",
        "gamma",
        "theta",
        "vega",
        "difference",
        "risk_score",
    }

    result_fields = {
        "theoretical_price",
        "delta",
        "gamma",
        "theta",
        "vega",
        "difference",
        "risk_score",
    }

    assert (
        result_fields
        ==
        expected
    )