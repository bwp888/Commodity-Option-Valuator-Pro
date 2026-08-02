"""
Commodity Option Valuator Pro
=============================

Risk Analyzer Tests

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

from models.implied_volatility import (
    ImpliedVolatility,
)

from models.taylor import (
    TaylorValuator,
)

from models.risk import (
    RiskAnalyzer,
    RiskLevel,
)



# ==========================================================
# Helper
# ==========================================================


def create_risk() -> RiskAnalyzer:
    """
    Create complete risk analyzer.
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


    market_price = bs.price


    iv = ImpliedVolatility(
        option,
        market_price,
    )


    taylor = TaylorValuator(
        greeks
    )


    return RiskAnalyzer(
        greeks,
        iv,
        taylor,
    )



# ==========================================================
# Basic Properties
# ==========================================================


def test_option():

    risk = create_risk()

    assert (
        risk.option
        is not None
    )



def test_spot():

    risk = create_risk()

    assert risk.spot == 100.0



def test_price():

    risk = create_risk()

    assert math.isclose(
        risk.price,
        10.450583572,
        rel_tol=1e-8,
    )



# ==========================================================
# Component Score Tests
# ==========================================================


def test_iv_score():

    risk = create_risk()

    score = risk.iv_score()


    assert 0 <= score <= 25



def test_gamma_score():

    risk = create_risk()

    score = risk.gamma_score()


    assert 0 <= score <= 25



def test_theta_score():

    risk = create_risk()

    score = risk.theta_score()


    assert 0 <= score <= 20



def test_valuation_score():

    risk = create_risk()

    score = risk.valuation_score(
        105.0
    )


    assert 0 <= score <= 30



# ==========================================================
# Total Score
# ==========================================================


def test_total_score():

    risk = create_risk()


    score = risk.total_score()


    assert 0 <= score <= 100



# ==========================================================
# Risk Level
# ==========================================================


@pytest.mark.parametrize(
    "score,level",
    [
        (20, RiskLevel.LOW),
        (50, RiskLevel.MEDIUM),
        (80, RiskLevel.HIGH),
        (95, RiskLevel.EXTREME),
    ],
)
def test_risk_level(
    score,
    level,
):

    risk = create_risk()


    assert (
        risk.risk_level(score)
        ==
        level
    )



# ==========================================================
# Analyze
# ==========================================================


def test_analyze_structure():

    risk = create_risk()


    result = risk.analyze()


    assert (
        "score"
        in result
    )


    assert (
        "level"
        in result
    )


    assert (
        "components"
        in result
    )


    assert (
        "market"
        in result
    )



def test_analyze_score():

    risk = create_risk()


    result = risk.analyze()


    assert (
        0
        <=
        result["score"]
        <=
        100
    )



def test_component_structure():

    risk = create_risk()


    result = risk.analyze()


    components = result[
        "components"
    ]


    assert (
        "iv_score"
        in components
    )


    assert (
        "gamma_score"
        in components
    )


    assert (
        "theta_score"
        in components
    )


    assert (
        "valuation_score"
        in components
    )



# ==========================================================
# Summary / Export
# ==========================================================


def test_summary():

    risk = create_risk()


    result = risk.summary()


    assert isinstance(
        result,
        dict,
    )



def test_to_dict():

    risk = create_risk()


    result = risk.to_dict()


    assert isinstance(
        result,
        dict,
    )



# ==========================================================
# Representation
# ==========================================================


def test_str():

    risk = create_risk()


    assert (
        "RiskAnalyzer"
        in str(risk)
    )



def test_repr():

    risk = create_risk()


    assert (
        "RiskAnalyzer"
        in repr(risk)
    )