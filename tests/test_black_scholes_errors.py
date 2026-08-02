"""
Commodity Option Valuator Pro
=============================

Black-Scholes Exception Tests

Author : Simon
Version : 0.1.0
"""

from __future__ import annotations

import math

import pytest

from models.black_scholes import BlackScholes
from models.option import Option
from models.option import OptionType


# ==========================================================
# Invalid Spot
# ==========================================================


def test_zero_spot():

    with pytest.raises(ValueError):

        BlackScholes(
            Option(
                option_type=OptionType.CALL,
                spot=0.0,
                strike=100.0,
                maturity=1.0,
                rate=0.05,
                volatility=0.20,
            )
        )


def test_negative_spot():

    with pytest.raises(ValueError):

        BlackScholes(
            Option(
                option_type=OptionType.CALL,
                spot=-10.0,
                strike=100.0,
                maturity=1.0,
                rate=0.05,
                volatility=0.20,
            )
        )


# ==========================================================
# Invalid Strike
# ==========================================================


def test_zero_strike():

    with pytest.raises(ValueError):

        BlackScholes(
            Option(
                option_type=OptionType.CALL,
                spot=100.0,
                strike=0.0,
                maturity=1.0,
                rate=0.05,
                volatility=0.20,
            )
        )


def test_negative_strike():

    with pytest.raises(ValueError):

        BlackScholes(
            Option(
                option_type=OptionType.CALL,
                spot=100.0,
                strike=-100.0,
                maturity=1.0,
                rate=0.05,
                volatility=0.20,
            )
        )


# ==========================================================
# Invalid Maturity
# ==========================================================


def test_zero_maturity():

    with pytest.raises(ValueError):

        BlackScholes(
            Option(
                option_type=OptionType.CALL,
                spot=100.0,
                strike=100.0,
                maturity=0.0,
                rate=0.05,
                volatility=0.20,
            )
        )


def test_negative_maturity():

    with pytest.raises(ValueError):

        BlackScholes(
            Option(
                option_type=OptionType.CALL,
                spot=100.0,
                strike=100.0,
                maturity=-1.0,
                rate=0.05,
                volatility=0.20,
            )
        )


# ==========================================================
# Invalid Volatility
# ==========================================================


def test_zero_volatility():

    with pytest.raises(ValueError):

        BlackScholes(
            Option(
                option_type=OptionType.CALL,
                spot=100.0,
                strike=100.0,
                maturity=1.0,
                rate=0.05,
                volatility=0.0,
            )
        )


def test_negative_volatility():

    with pytest.raises(ValueError):

        BlackScholes(
            Option(
                option_type=OptionType.CALL,
                spot=100.0,
                strike=100.0,
                maturity=1.0,
                rate=0.05,
                volatility=-0.20,
            )
        )


# ==========================================================
# NaN
# ==========================================================


@pytest.mark.parametrize(
    "spot,strike,maturity,rate,volatility",
    [
        (math.nan, 100.0, 1.0, 0.05, 0.20),
        (100.0, math.nan, 1.0, 0.05, 0.20),
        (100.0, 100.0, math.nan, 0.05, 0.20),
        (100.0, 100.0, 1.0, math.nan, 0.20),
        (100.0, 100.0, 1.0, 0.05, math.nan),
    ],
)
def test_nan_parameters(
    spot,
    strike,
    maturity,
    rate,
    volatility,
):

    with pytest.raises(ValueError):

        BlackScholes(
            Option(
                option_type=OptionType.CALL,
                spot=spot,
                strike=strike,
                maturity=maturity,
                rate=rate,
                volatility=volatility,
            )
        )


# ==========================================================
# Infinity
# ==========================================================


@pytest.mark.parametrize(
    "spot,strike,maturity,rate,volatility",
    [
        (math.inf, 100.0, 1.0, 0.05, 0.20),
        (100.0, math.inf, 1.0, 0.05, 0.20),
        (100.0, 100.0, 1.0, math.inf, 0.20),
        (100.0, 100.0, 1.0, 0.05, math.inf),
    ],
)
def test_inf_parameters(
    spot,
    strike,
    maturity,
    rate,
    volatility,
):

    with pytest.raises(ValueError):

        BlackScholes(
            Option(
                option_type=OptionType.CALL,
                spot=spot,
                strike=strike,
                maturity=maturity,
                rate=rate,
                volatility=volatility,
            )
        )