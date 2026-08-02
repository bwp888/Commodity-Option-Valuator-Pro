"""
Commodity Option Valuator Pro

Black-Scholes Price Tests
"""

from __future__ import annotations

import math


def test_call_price(bs_call):
    """
    Standard Call price.
    """
    assert math.isclose(
        bs_call.call_price,
        10.450583572185565,
        rel_tol=1e-8,
    )


def test_put_price(bs_put):
    """
    Standard Put price.
    """
    assert math.isclose(
        bs_put.put_price,
        5.573526022256971,
        rel_tol=1e-8,
    )


def test_price_property_call(bs_call):
    """
    price property (Call).
    """
    assert bs_call.price == bs_call.call_price


def test_price_property_put(bs_put):
    """
    price property (Put).
    """
    assert bs_put.price == bs_put.put_price


def test_discount_factor(bs_call):
    """
    Discount factor.
    """
    assert math.isclose(
        bs_call.discount_factor,
        math.exp(-0.05),
        rel_tol=1e-12,
    )


def test_forward_price(bs_call):
    """
    Forward price.
    """
    assert math.isclose(
        bs_call.forward_price,
        100.0 * math.exp(0.05),
        rel_tol=1e-12,
    )
    # ==========================================================
# Mathematical Validation
# ==========================================================


def test_d1(bs_call):
    """
    Validate d1.
    """

    assert math.isclose(
        bs_call.d1,
        0.35000000000000003,
        rel_tol=1e-12,
    )


def test_d2(bs_call):
    """
    Validate d2.
    """

    assert math.isclose(
        bs_call.d2,
        0.15000000000000002,
        rel_tol=1e-12,
    )


def test_put_call_parity(bs_call):
    """
    Put-Call parity  should be close to zero.
    """

    assert math.isclose(
        bs_call.put_call_parity,
        0.0,
        abs_tol=1e-12,
    )


def test_intrinsic_value_call(bs_call):
    """
    ATM Call intrinsic value.
    """

    assert bs_call.intrinsic_value == 0.0


def test_intrinsic_value_put(bs_put):
    """
    ATM Put intrinsic value.
    """

    assert bs_put.intrinsic_value == 0.0


def test_time_value_call(bs_call):
    """
    ATM Call time value.
    """

    assert math.isclose(
        bs_call.time_value,
        bs_call.price,
        rel_tol=1e-12,
    )


def test_time_value_put(bs_put):
    """
    ATM Put time value.
    """

    assert math.isclose(
        bs_put.time_value,
        bs_put.price,
        rel_tol=1e-12,
    )


def test_moneyness(bs_call):
    """
    ATM moneyness.
    """

    assert math.isclose(
        bs_call.moneyness,
        1.0,
        rel_tol=1e-12,
    )