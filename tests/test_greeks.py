"""
Commodity Option Valuator Pro
=============================

Greeks Engine Tests

Author : Simon
Version : 0.1.0
"""

from __future__ import annotations

import math

from models.greeks import Greeks
from models.black_scholes import BlackScholes
from models.option import Option, OptionType


# ==========================================================
# Fixtures
# ==========================================================


def create_call_greeks() -> Greeks:
    """
    Create standard Call Greeks.
    """

    option = Option(
        option_type=OptionType.CALL,
        spot=100.0,
        strike=100.0,
        maturity=1.0,
        rate=0.05,
        volatility=0.20,
    )

    return Greeks(
        BlackScholes(option)
    )


def create_put_greeks() -> Greeks:
    """
    Create standard Put Greeks.
    """

    option = Option(
        option_type=OptionType.PUT,
        spot=100.0,
        strike=100.0,
        maturity=1.0,
        rate=0.05,
        volatility=0.20,
    )

    return Greeks(
        BlackScholes(option)
    )


# ==========================================================
# Delta Tests
# ==========================================================


def test_call_delta():

    greeks = create_call_greeks()

    assert math.isclose(
        greeks.delta,
        0.6368306511756191,
        rel_tol=1e-10,
    )


def test_put_delta():

    greeks = create_put_greeks()

    assert math.isclose(
        greeks.delta,
        -0.3631693488243809,
        rel_tol=1e-10,
    )


def test_delta_difference():

    call = create_call_greeks()
    put = create_put_greeks()

    assert math.isclose(
        call.delta - put.delta,
        1.0,
        rel_tol=1e-12,
    )


# ==========================================================
# Gamma Tests
# ==========================================================


def test_gamma():

    greeks = create_call_greeks()

    assert math.isclose(
        greeks.gamma,
        0.018762017345846895,
        rel_tol=1e-10,
    )


def test_call_put_same_gamma():

    call = create_call_greeks()
    put = create_put_greeks()

    assert math.isclose(
        call.gamma,
        put.gamma,
        rel_tol=1e-12,
    )


# ==========================================================
# Vega Tests
# ==========================================================


def test_vega():

    greeks = create_call_greeks()

    assert math.isclose(
        greeks.vega,
        37.52403469169379,
        rel_tol=1e-10,
    )


def test_call_put_same_vega():

    call = create_call_greeks()
    put = create_put_greeks()

    assert math.isclose(
        call.vega,
        put.vega,
        rel_tol=1e-12,
    )


# ==========================================================
# Theta Tests
# ==========================================================


def test_theta_daily():

    greeks = create_call_greeks()

    assert math.isclose(
        greeks.theta,
        -0.01757267820925917,
        rel_tol=1e-10,
    )


def test_theta_is_daily():

    greeks = create_call_greeks()

    annual = greeks.theta * 365

    assert annual < 0


# ==========================================================
# Rho Tests
# ==========================================================


def test_call_rho():

    greeks = create_call_greeks()

    assert math.isclose(
        greeks.rho,
        53.232481545376345,
        rel_tol=1e-10,
    )


def test_put_rho_negative():

    greeks = create_put_greeks()

    assert greeks.rho < 0


# ==========================================================
# Elasticity
# ==========================================================


def test_elasticity():

    greeks = create_call_greeks()

    expected = (
        greeks.delta
        * greeks.spot
        / greeks.bs.price
    )

    assert math.isclose(
        greeks.elasticity,
        expected,
        rel_tol=1e-12,
    )


# ==========================================================
# Summary
# ==========================================================


def test_summary_keys():

    greeks = create_call_greeks()

    summary = greeks.summary()

    keys = {
        "delta",
        "gamma",
        "theta",
        "vega",
        "rho",
        "elasticity",
        "price",
    }

    assert keys.issubset(
        summary.keys()
    )


def test_summary_price():

    greeks = create_call_greeks()

    summary = greeks.summary()

    assert math.isclose(
        summary["price"],
        greeks.bs.price,
        rel_tol=1e-12,
    )


# ==========================================================
# Representation
# ==========================================================


def test_string():

    greeks = create_call_greeks()

    text = str(greeks)

    assert "Greeks" in text


def test_repr():

    greeks = create_call_greeks()

    text = repr(greeks)

    assert "Greeks" in text