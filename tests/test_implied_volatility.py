"""
Commodity Option Valuator Pro
=============================

Implied Volatility Solver Tests

Author : Simon
Version : 0.1.0
"""

from __future__ import annotations

import math

import pytest

from models.option import Option
from models.option import OptionType

from models.black_scholes import BlackScholes

from models.implied_volatility import (
    ImpliedVolatility,
)


# ==========================================================
# Helper
# ==========================================================


def create_option(
    option_type: OptionType,
    volatility: float,
) -> Option:
    """
    Create test option.
    """

    return Option(
        option_type=option_type,
        spot=100.0,
        strike=100.0,
        maturity=1.0,
        rate=0.05,
        volatility=volatility,
    )


def create_market_price(
    option: Option,
) -> float:
    """
    Generate market price from BS model.
    """

    return BlackScholes(
        option
    ).price


# ==========================================================
# Basic IV Tests
# ==========================================================


def test_call_iv():

    true_vol = 0.20

    option = create_option(
        OptionType.CALL,
        true_vol,
    )

    price = create_market_price(
        option
    )


    solver = ImpliedVolatility(
        option,
        price,
    )


    iv = solver.solve()


    assert math.isclose(
        iv,
        true_vol,
        rel_tol=1e-8,
    )



def test_put_iv():

    true_vol = 0.20

    option = create_option(
        OptionType.PUT,
        true_vol,
    )

    price = create_market_price(
        option
    )


    solver = ImpliedVolatility(
        option,
        price,
    )


    iv = solver.solve()


    assert math.isclose(
        iv,
        true_vol,
        rel_tol=1e-8,
    )


# ==========================================================
# Different Volatility
# ==========================================================


@pytest.mark.parametrize(
    "volatility",
    [
        0.05,
        0.10,
        0.30,
        0.50,
        1.00,
    ],
)
def test_multiple_volatility(volatility):

    option = create_option(
        OptionType.CALL,
        volatility,
    )

    price = create_market_price(
        option,
    )


    solver = ImpliedVolatility(
        option,
        price,
    )


    result = solver.solve()


    assert math.isclose(
        result,
        volatility,
        rel_tol=1e-8,
    )


# ==========================================================
# Moneyness Tests
# ==========================================================


def test_itm_call_iv():

    option = Option(
        option_type=OptionType.CALL,
        spot=120.0,
        strike=100.0,
        maturity=1.0,
        rate=0.05,
        volatility=0.25,
    )

    price = create_market_price(
        option
    )


    solver = ImpliedVolatility(
        option,
        price,
    )


    assert math.isclose(
        solver.solve(),
        0.25,
        rel_tol=1e-8,
    )



def test_otm_call_iv():

    option = Option(
        option_type=OptionType.CALL,
        spot=80.0,
        strike=100.0,
        maturity=1.0,
        rate=0.05,
        volatility=0.35,
    )

    price = create_market_price(
        option
    )


    solver = ImpliedVolatility(
        option,
        price,
    )


    assert math.isclose(
        solver.solve(),
        0.35,
        rel_tol=1e-8,
    )


# ==========================================================
# Validation Tests
# ==========================================================


def test_negative_market_price():

    option = create_option(
        OptionType.CALL,
        0.20,
    )


    solver = ImpliedVolatility(
        option,
        -1.0,
    )


    with pytest.raises(
        ValueError
    ):

        solver.solve()



def test_market_price_below_intrinsic():

    option = Option(
        option_type=OptionType.CALL,
        spot=120.0,
        strike=100.0,
        maturity=1.0,
        rate=0.05,
        volatility=0.20,
    )


    solver = ImpliedVolatility(
        option,
        10.0,
    )


    with pytest.raises(
        ValueError
    ):

        solver.solve()


# ==========================================================
# Summary
# ==========================================================


def test_summary():

    option = create_option(
        OptionType.CALL,
        0.20,
    )


    price = create_market_price(
        option
    )


    solver = ImpliedVolatility(
        option,
        price,
    )


    summary = solver.summary()


    assert (
        "implied_volatility"
        in summary
    )


    assert math.isclose(
        summary["implied_volatility"],
        0.20,
        rel_tol=1e-8,
    )


# ==========================================================
# Cache
# ==========================================================


def test_iv_cache():

    option = create_option(
        OptionType.CALL,
        0.20,
    )

    price = create_market_price(
        option,
    )


    solver = ImpliedVolatility(
        option,
        price,
    )


    first = solver.solve_cached()

    second = solver.solve_cached()


    assert first == second



# ==========================================================
# Representation
# ==========================================================


def test_str():

    option = create_option(
        OptionType.CALL,
        0.20,
    )

    price = create_market_price(
        option,
    )


    solver = ImpliedVolatility(
        option,
        price,
    )


    assert (
        "ImpliedVolatility"
        in str(solver)
    )



def test_repr():

    option = create_option(
        OptionType.CALL,
        0.20,
    )

    price = create_market_price(
        option,
    )


    solver = ImpliedVolatility(
        option,
        price,
    )


    assert (
        "ImpliedVolatility"
        in repr(solver)
    )