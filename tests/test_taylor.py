"""
Commodity Option Valuator Pro
=============================

Taylor Valuation Engine Tests

Author : Simon
Version : 0.1.0
"""

from __future__ import annotations

import math

import pytest

from models.option import (
    Option,
    OptionType,
)

from models.black_scholes import (
    BlackScholes,
)

from models.greeks import (
    Greeks,
)

from models.taylor import (
    TaylorValuator,
)


# ==========================================================
# Helper
# ==========================================================


def create_taylor() -> TaylorValuator:
    """
    Create standard Taylor model.
    """

    option = Option(
        option_type=OptionType.CALL,
        spot=100.0,
        strike=100.0,
        maturity=1.0,
        rate=0.05,
        volatility=0.20,
    )


    bs = BlackScholes(
        option
    )


    greeks = Greeks(
        bs
    )


    return TaylorValuator(
        greeks
    )


# ==========================================================
# Basic Properties
# ==========================================================


def test_base_price():

    taylor = create_taylor()

    assert math.isclose(
        taylor.base_price,
        10.450583572185565,
        rel_tol=1e-10,
    )



def test_spot():

    taylor = create_taylor()

    assert taylor.spot == 100.0



def test_delta():

    taylor = create_taylor()

    assert math.isclose(
        taylor.delta,
        0.6368306511,
        rel_tol=1e-8,
    )



def test_gamma():

    taylor = create_taylor()

    assert math.isclose(
        taylor.gamma,
        0.0187620173,
        rel_tol=1e-8,
    )


# ==========================================================
# Spot Change
# ==========================================================


def test_spot_change():

    taylor = create_taylor()

    result = taylor.spot_change(
        105.0
    )

    assert result == 5.0



def test_negative_spot_change():

    taylor = create_taylor()

    result = taylor.spot_change(
        95.0
    )

    assert result == -5.0


# ==========================================================
# Delta Effect
# ==========================================================


def test_delta_effect():

    taylor = create_taylor()

    result = taylor.delta_effect(
        105.0
    )


    expected = (
        taylor.delta
        *
        5.0
    )


    assert math.isclose(
        result,
        expected,
        rel_tol=1e-12,
    )


# ==========================================================
# Gamma Effect
# ==========================================================


def test_gamma_effect():

    taylor = create_taylor()


    result = taylor.gamma_effect(
        105.0
    )


    expected = (
        0.5
        *
        taylor.gamma
        *
        25.0
    )


    assert math.isclose(
        result,
        expected,
        rel_tol=1e-12,
    )


# ==========================================================
# First Order
# ==========================================================


def test_first_order():

    taylor = create_taylor()


    result = taylor.first_order(
        105.0
    )


    expected = (
        taylor.base_price
        +
        taylor.delta * 5.0
    )


    assert math.isclose(
        result,
        expected,
        rel_tol=1e-12,
    )


# ==========================================================
# Second Order
# ==========================================================


def test_second_order():

    taylor = create_taylor()


    result = taylor.second_order(
        105.0
    )


    expected = (
        taylor.base_price
        +
        taylor.delta * 5.0
        +
        0.5
        *
        taylor.gamma
        *
        25.0
    )


    assert math.isclose(
        result,
        expected,
        rel_tol=1e-12,
    )


# ==========================================================
# Estimate Output
# ==========================================================


def test_estimate_keys():

    taylor = create_taylor()


    result = taylor.estimate(
        105.0
    )


    keys = {
        "base_price",
        "old_spot",
        "new_spot",
        "spot_change",
        "delta_effect",
        "gamma_effect",
        "first_order_price",
        "second_order_price",
    }


    assert keys.issubset(
        result.keys()
    )



def test_estimate_price_relation():

    taylor = create_taylor()


    result = taylor.estimate(
        105.0
    )


    assert math.isclose(
        result["second_order_price"],
        (
            result["base_price"]
            +
            result["delta_effect"]
            +
            result["gamma_effect"]
        ),
        rel_tol=1e-12,
    )


# ==========================================================
# Validation
# ==========================================================


def test_invalid_spot():

    taylor = create_taylor()


    with pytest.raises(
        ValueError
    ):

        taylor.summary(
            -10
        )


# ==========================================================
# Export
# ==========================================================


def test_to_dict():

    taylor = create_taylor()


    result = taylor.to_dict(
        105
    )


    assert isinstance(
        result,
        dict,
    )



# ==========================================================
# Representation
# ==========================================================


def test_str():

    taylor = create_taylor()


    assert (
        "TaylorValuator"
        in str(taylor)
    )



def test_repr():

    taylor = create_taylor()


    assert (
        "TaylorValuator"
        in repr(taylor)
    )