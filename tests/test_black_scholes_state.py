"""
Commodity Option Valuator Pro
=============================

Black-Scholes State Tests

Author : Simon
Version : 0.1.0
"""

from __future__ import annotations

import math

from models.black_scholes import BlackScholes
from models.option import Option, OptionType


# ==========================================================
# Option State Tests
# ==========================================================


def test_call_at_the_money(bs_call):
    """
    Standard ATM Call.
    """

    assert bs_call.is_at_the_money
    assert not bs_call.is_in_the_money
    assert not bs_call.is_out_of_the_money


def test_put_at_the_money(bs_put):
    """
    Standard ATM Put.
    """

    assert bs_put.is_at_the_money
    assert not bs_put.is_in_the_money
    assert not bs_put.is_out_of_the_money


def test_call_in_the_money():
    """
    ITM Call.
    """

    option = Option(
        option_type=OptionType.CALL,
        spot=120.0,
        strike=100.0,
        maturity=1.0,
        rate=0.05,
        volatility=0.20,
    )

    bs = BlackScholes(option)

    assert bs.is_in_the_money
    assert not bs.is_at_the_money
    assert not bs.is_out_of_the_money


def test_call_out_of_the_money():
    """
    OTM Call.
    """

    option = Option(
        option_type=OptionType.CALL,
        spot=80.0,
        strike=100.0,
        maturity=1.0,
        rate=0.05,
        volatility=0.20,
    )

    bs = BlackScholes(option)

    assert bs.is_out_of_the_money
    assert not bs.is_in_the_money
    assert not bs.is_at_the_money


def test_put_in_the_money():
    """
    ITM Put.
    """

    option = Option(
        option_type=OptionType.PUT,
        spot=80.0,
        strike=100.0,
        maturity=1.0,
        rate=0.05,
        volatility=0.20,
    )

    bs = BlackScholes(option)

    assert bs.is_in_the_money
    assert not bs.is_out_of_the_money
    assert not bs.is_at_the_money


def test_put_out_of_the_money():
    """
    OTM Put.
    """

    option = Option(
        option_type=OptionType.PUT,
        spot=120.0,
        strike=100.0,
        maturity=1.0,
        rate=0.05,
        volatility=0.20,
    )

    bs = BlackScholes(option)

    assert bs.is_out_of_the_money
    assert not bs.is_in_the_money
    assert not bs.is_at_the_money


# ==========================================================
# Summary Tests
# ==========================================================


def test_summary_keys(bs_call):
    """
    Summary contains required keys.
    """

    summary = bs_call.summary()

    expected = {
        "option_type",
        "spot",
        "strike",
        "maturity",
        "rate",
        "volatility",
        "d1",
        "d2",
        "forward_price",
        "discount_factor",
        "call_price",
        "put_price",
        "price",
        "intrinsic_value",
        "time_value",
        "is_itm",
        "is_atm",
        "is_otm",
        "put_call_parity",
    }

    assert expected.issubset(summary.keys())


def test_summary_price(bs_call):
    """
    Summary price equals engine price.
    """

    summary = bs_call.summary()

    assert math.isclose(
        summary["price"],
        bs_call.price,
        rel_tol=1e-12,
    )


def test_summary_option_type(bs_call):
    """
    Summary option type.
    """

    summary = bs_call.summary()

    assert summary["option_type"] == "CALL"