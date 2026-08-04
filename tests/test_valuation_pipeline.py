"""
Commodity Option Valuator Pro
=============================

Valuation Pipeline Tests

Author : Simon
Version : 1.0.0
"""


from __future__ import annotations


import pytest



from models.option_scanner import (
    OptionContract,
    OptionDirection,
)


from core.valuation_engine import (
    ValuationEngine,
    ValuationResult,
)



# ==========================================================
# Fixtures
# ==========================================================


@pytest.fixture
def engine():

    return ValuationEngine()



@pytest.fixture
def call_option():

    return OptionContract(

        symbol="CU2409-C-70000",

        direction=OptionDirection.CALL,

        strike=70000,

        price=850,

        volume=10000,

        open_interest=50000,

        bid=840,

        ask=860,

    )



@pytest.fixture
def put_option():

    return OptionContract(

        symbol="CU2409-P-70000",

        direction=OptionDirection.PUT,

        strike=70000,

        price=620,

        volume=8000,

        open_interest=30000,

        bid=610,

        ask=630,

    )



# ==========================================================
# Initialization
# ==========================================================


def test_engine_create():

    engine = ValuationEngine()

    assert engine is not None



def test_default_rate():

    engine = ValuationEngine()

    assert (
        engine.risk_free_rate
        ==
        0.025
    )



def test_days_year():

    engine = ValuationEngine()

    assert (
        engine.days_per_year
        ==
        365
    )



# ==========================================================
# Validation
# ==========================================================


def test_valid_contract(
    engine,
    call_option,
):

    assert (
        engine.validate_contract(
            call_option
        )
        is True
    )



def test_none_contract(
    engine,
):

    assert (
        engine.validate_contract(
            None
        )
        is False
    )



# ==========================================================
# Parameter
# ==========================================================


def test_days_to_year(
    engine,
):

    result = engine.days_to_year(
        365
    )

    assert result == 1



def test_build_parameters(
    engine,
    call_option,
):

    params = engine.build_parameters(

        call_option,

        70000,

        0.25,

        60,

    )


    assert (
        params["spot"]
        ==
        70000
    )


    assert (
        params["strike"]
        ==
        70000
    )


    assert (
        params["time"]
        ==
        60 / 365
    )



# ==========================================================
# Evaluation
# ==========================================================


def test_single_evaluation(
    engine,
    call_option,
):

    result = engine.evaluate(

        call_option,

        underlying_price=70000,

        volatility=0.25,

        days=60,

    )


    assert isinstance(
        result,
        ValuationResult,
    )



def test_result_symbol(
    engine,
    call_option,
):

    result = engine.evaluate(

        call_option,

        70000,

        0.25,

        60,

    )


    assert (
        result.symbol
        ==
        call_option.symbol
    )



def test_result_price(
    engine,
    call_option,
):

    result = engine.evaluate(

        call_option,

        70000,

        0.25,

        60,

    )


    assert (
        result.theoretical_price
        >=
        0
    )



# ==========================================================
# Result Methods
# ==========================================================


def test_difference(
    engine,
    call_option,
):

    result = engine.evaluate(

        call_option,

        70000,

        0.25,

        60,

    )


    value = result.premium_difference()


    assert isinstance(
        value,
        float,
    )



def test_ratio(
    engine,
    call_option,
):

    result = engine.evaluate(

        call_option,

        70000,

        0.25,

        60,

    )


    ratio = result.valuation_ratio()


    assert ratio >= 0



# ==========================================================
# Batch
# ==========================================================


def test_batch_evaluation(
    engine,
    call_option,
    put_option,
):

    results = engine.evaluate_batch(

        [

            call_option,

            put_option,

        ],

        70000,

        0.25,

        60,

    )


    assert len(results) == 2



# ==========================================================
# Sorting
# ==========================================================


def test_sort_risk(
    engine,
):

    items = [

        ValuationResult(

            "A",

            OptionDirection.CALL,

            10,

            12,

            0.5,

            0.1,

            -0.01,

            0.2,

            0.3,

            50,

        ),

        ValuationResult(

            "B",

            OptionDirection.PUT,

            20,

            18,

            -0.5,

            0.2,

            -0.02,

            0.5,

            0.25,

            80,

        ),

    ]


    result = engine.sort_by_risk(
        items
    )


    assert (
        result[0].symbol
        ==
        "B"
    )



def test_sort_difference(
    engine,
):

    items = [

        ValuationResult(

            "A",

            OptionDirection.CALL,

            10,

            8,

            0,

            0,

            0,

            0,

            None,

            10,

        ),

        ValuationResult(

            "B",

            OptionDirection.CALL,

            20,

            10,

            0,

            0,

            0,

            0,

            None,

            10,

        ),

    ]


    result = engine.sort_by_difference(
        items
    )


    assert (
        result[0].symbol
        ==
        "B"
    )



# ==========================================================
# Export
# ==========================================================


def test_result_to_dict(
    engine,
    call_option,
):

    result = engine.evaluate(

        call_option,

        70000,

        0.25,

        60,

    )


    data = engine.result_to_dict(
        result
    )


    assert (
        "symbol"
        in data
    )


    assert (
        "risk_score"
        in data
    )



# ==========================================================
# Representation
# ==========================================================


def test_engine_str(
    engine,
):

    assert (
        "ValuationEngine"
        in str(engine)
    )



def test_engine_repr(
    engine,
):

    assert (
        "ValuationEngine"
        in repr(engine)
    )