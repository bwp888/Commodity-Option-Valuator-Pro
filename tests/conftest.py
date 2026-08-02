"""
Commodity Option Valuator Pro
=============================

Pytest Fixtures

Author : Simon
Version : 0.1.0
"""

from __future__ import annotations

import pytest

from models.option import Option
from models.option import OptionType
from models.black_scholes import BlackScholes


@pytest.fixture
def call_option() -> Option:
    """
    Standard European Call option.
    """
    return Option(
        option_type=OptionType.CALL,
        spot=100.0,
        strike=100.0,
        maturity=1.0,
        rate=0.05,
        volatility=0.20,
    )


@pytest.fixture
def put_option() -> Option:
    """
    Standard European Put option.
    """
    return Option(
        option_type=OptionType.PUT,
        spot=100.0,
        strike=100.0,
        maturity=1.0,
        rate=0.05,
        volatility=0.20,
    )


@pytest.fixture
def bs_call(call_option: Option) -> BlackScholes:
    """
    Black-Scholes Call engine.
    """
    return BlackScholes(call_option)


@pytest.fixture
def bs_put(put_option: Option) -> BlackScholes:
    """
    Black-Scholes Put engine.
    """
    return BlackScholes(put_option)