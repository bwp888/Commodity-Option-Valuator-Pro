"""
Commodity Option Valuator Pro
=============================

Valuation UI Engine Integration Tests.

Commit 0010
------------

Author : Simon
Version : 0.2.2
"""

from __future__ import annotations

import math
import pytest

from core.valuation_engine import (
    ValuationResult,
)

from models.option_scanner import (
    OptionDirection,
)

from ui.valuation import (
    ValuationPage,
)


# ==========================================================
# Parameter Parsing
# ==========================================================


def test_parse_parameters():

    parameters = {
        "symbol": "SR609C5600",
        "spot": "5600",
        "strike": "5600",
        "market_price": "120",
        "days": "30",
        "volatility": "0.20",
        "rate": "0.025",
        "direction": "CALL",
    }

    result = ValuationPage.parse_parameters(
        parameters
    )

    assert (
        result["symbol"]
        ==
        "SR609C5600"
    )

    assert (
        result["direction"]
        ==
        OptionDirection.CALL
    )

    assert (
        result["spot"]
        ==
        5600.0
    )

    assert (
        result["strike"]
        ==
        5600.0
    )

    assert (
        result["market_price"]
        ==
        120.0
    )

    assert (
        result["days"]
        ==
        30
    )

    assert (
        result["volatility"]
        ==
        0.20
    )

    assert (
        result["rate"]
        ==
        0.025
    )


# ==========================================================
# Default Rate
# ==========================================================


def test_parse_parameters_default_rate():

    parameters = {
        "symbol": "SR609C5600",
        "spot": "5600",
        "strike": "5600",
        "market_price": "120",
        "days": "30",
        "volatility": "0.20",
        "rate": "",
        "direction": "CALL",
    }

    result = ValuationPage.parse_parameters(
        parameters
    )

    assert (
        result["rate"]
        ==
        0.025
    )


# ==========================================================
# PUT Direction
# ==========================================================


def test_parse_put_direction():

    parameters = {
        "symbol": "SR609P5600",
        "spot": "5600",
        "strike": "5600",
        "market_price": "120",
        "days": "30",
        "volatility": "0.20",
        "rate": "0.025",
        "direction": "PUT",
    }

    result = ValuationPage.parse_parameters(
        parameters
    )

    assert (
        result["direction"]
        ==
        OptionDirection.PUT
    )


# ==========================================================
# Invalid Parameters
# ==========================================================


def test_parse_parameters_rejects_invalid_spot():

    parameters = {
        "symbol": "SR609C5600",
        "spot": "0",
        "strike": "5600",
        "market_price": "120",
        "days": "30",
        "volatility": "0.20",
        "rate": "0.025",
        "direction": "CALL",
    }

    try:

        ValuationPage.parse_parameters(
            parameters
        )

    except ValueError as exc:

        assert (
            str(exc)
            ==
            "标的价格必须大于 0。"
        )

    else:

        raise AssertionError(
            "Expected ValueError"
        )


def test_parse_parameters_rejects_invalid_days():

    parameters = {
        "symbol": "SR609C5600",
        "spot": "5600",
        "strike": "5600",
        "market_price": "120",
        "days": "0",
        "volatility": "0.20",
        "rate": "0.025",
        "direction": "CALL",
    }

    try:

        ValuationPage.parse_parameters(
            parameters
        )

    except ValueError as exc:

        assert (
            str(exc)
            ==
            "剩余天数必须大于 0。"
        )

    else:

        raise AssertionError(
            "Expected ValueError"
        )


# ==========================================================
# Contract Construction
# ==========================================================


def test_build_contract():

    parameters = {
        "symbol": "SR609C5600",
        "direction": OptionDirection.CALL,
        "spot": 5600.0,
        "strike": 5600.0,
        "market_price": 120.0,
        "days": 30,
        "volatility": 0.20,
        "rate": 0.025,
    }

    contract = ValuationPage.build_contract(
        parameters
    )

    assert (
        contract.symbol
        ==
        "SR609C5600"
    )

    assert (
        contract.direction
        ==
        OptionDirection.CALL
    )

    assert (
        contract.strike
        ==
        5600.0
    )

    assert (
        contract.price
        ==
        120.0
    )

    assert (
        contract.volume
        ==
        0
    )


# ==========================================================
# Engine Integration
# ==========================================================


def test_evaluate_parameters():

    parameters = {
        "symbol": "SR609C5600",
        "spot": "5600",
        "strike": "5600",
        "market_price": "120",
        "days": "30",
        "volatility": "0.20",
        "rate": "0.025",
        "direction": "CALL",
    }

    page = ValuationPage.__new__(
        ValuationPage
    )

    result = page.evaluate_parameters(
        parameters
    )

    assert isinstance(
        result,
        ValuationResult,
    )

    assert (
        result.symbol
        ==
        "SR609C5600"
    )

    assert (
        result.direction
        ==
        OptionDirection.CALL
    )

    assert math.isfinite(
        result.theoretical_price
    )

    assert math.isfinite(
        result.delta
    )

    assert math.isfinite(
        result.gamma
    )

    assert math.isfinite(
        result.theta
    )

    assert math.isfinite(
        result.vega
    )

    assert (
        result.difference
        is not None
    )

    assert math.isfinite(
        result.risk_score
    )


# ==========================================================
# Result Formatting
# ==========================================================


def test_result_keys():

    expected = {
        "theoretical_price",
        "delta",
        "gamma",
        "theta",
        "vega",
        "difference",
        "risk_score",
    }

    assert (
        set(
            ValuationPage.RESULT_KEYS
        )
        ==
        expected
    )

def test_build_single_option_input_applies_reference_volatility_change():
    parameters = {
        "symbol": "SR609C5600",
        "spot": 5600.0,
        "strike": 5600.0,
        "market_price": 120.0,
        "days": 30,
        "volatility": 19.54,
        "reference_volatility_change": 0.1067,
        "target_futures_price": 5700.0,
        "rate": 0.025,
        "direction": OptionDirection.CALL,
    }

    page = ValuationPage.__new__(
        ValuationPage
    )

    result = page.build_single_option_input(
        parameters
    )

    assert (
        result.reference_volatility.current
        == pytest.approx(1.0)
    )

    assert (
        result.reference_volatility.target
        == pytest.approx(1.1067)
    )

    assert (
        result.current_option_iv
        == pytest.approx(0.1954)
    )


