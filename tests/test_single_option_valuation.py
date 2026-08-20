"""
Tests for Commit 0026.

Single Option Valuation and Scenario Analysis.
"""

from __future__ import annotations

import math

import pytest

from core.single_option_valuation import (
    ReferenceVolatilityScenario,
    SingleOptionValuationInput,
    SingleOptionValuationResult,
    SingleOptionValuator,
)
from models.option import (
    OptionDirection,
    OptionType,
)


# ==========================================================
# Reference Volatility
# ==========================================================


def test_reference_volatility_change() -> None:
    scenario = ReferenceVolatilityScenario(
        current=26.70,
        target=29.55,
    )

    assert scenario.relative_change_percent == pytest.approx(
        10.6741573,
        rel=1e-6,
    )


def test_reference_volatility_adjusts_option_iv() -> None:
    """
    The single-option IV should change proportionally
    to the reference volatility change.

    This test intentionally uses simple generic values.
    26.70 -> 29.55 is only a real-world example and
    is not a fixed application parameter.
    """

    scenario = ReferenceVolatilityScenario(
        current=20.0,
        target=22.0,
    )

    target_iv = scenario.adjust_option_iv(
        0.20
    )

    assert target_iv == pytest.approx(
        0.22,
        rel=1e-6,
    )


def test_reference_volatility_rejects_zero_current() -> None:
    scenario = ReferenceVolatilityScenario(
        current=0.0,
        target=29.55,
    )

    with pytest.raises(ValueError):
        scenario.validate()


def test_reference_volatility_rejects_zero_target() -> None:
    scenario = ReferenceVolatilityScenario(
        current=26.70,
        target=0.0,
    )

    with pytest.raises(ValueError):
        scenario.validate()


def test_reference_volatility_rejects_invalid_option_iv() -> None:
    scenario = ReferenceVolatilityScenario(
        current=26.70,
        target=29.55,
    )

    with pytest.raises(
        ValueError,
        match="current_option_iv",
    ):
        scenario.adjust_option_iv(
            0.0
        )


# ==========================================================
# Input Validation
# ==========================================================


def make_valid_input() -> SingleOptionValuationInput:
    return SingleOptionValuationInput(
        symbol="AU2608-C-968",
        option_type=OptionType.CALL,
        current_futures_price=900.0,
        strike=968.0,
        current_option_price=15.0,
        current_option_iv=0.1954,
        remaining_days=30,
        target_futures_price=1000.0,
        reference_volatility=(
            ReferenceVolatilityScenario(
                current=26.70,
                target=29.55,
            )
        ),
    )


def test_valid_input_passes_validation() -> None:
    inputs = make_valid_input()

    inputs.validate()


@pytest.mark.parametrize(
    "field,value",
    [
        (
            "current_futures_price",
            0.0,
        ),
        (
            "strike",
            0.0,
        ),
        (
            "current_option_iv",
            0.0,
        ),
        (
            "remaining_days",
            0,
        ),
        (
            "target_futures_price",
            0.0,
        ),
    ],
)
def test_invalid_positive_inputs_are_rejected(
    field: str,
    value: float,
) -> None:
    values = make_valid_input().__dict__
    values[field] = value

    inputs = SingleOptionValuationInput(
        **values
    )

    with pytest.raises(ValueError):
        inputs.validate()


def test_negative_current_option_price_is_rejected() -> None:
    values = make_valid_input().__dict__
    values["current_option_price"] = -1.0

    inputs = SingleOptionValuationInput(
        **values
    )

    with pytest.raises(ValueError):
        inputs.validate()


def test_negative_risk_free_rate_is_rejected() -> None:
    values = make_valid_input().__dict__
    values["risk_free_rate"] = -0.01

    inputs = SingleOptionValuationInput(
        **values
    )

    with pytest.raises(ValueError):
        inputs.validate()


# ==========================================================
# Evaluation
# ==========================================================


def test_evaluate_returns_result() -> None:
    valuator = SingleOptionValuator()

    result = valuator.evaluate(
        make_valid_input()
    )

    assert isinstance(
        result,
        SingleOptionValuationResult,
    )


def test_evaluate_preserves_market_inputs() -> None:
    valuator = SingleOptionValuator()

    result = valuator.evaluate(
        make_valid_input()
    )

    assert result.symbol == "AU2608-C-968"
    assert result.current_futures_price == 900.0
    assert result.target_futures_price == 1000.0
    assert result.strike == 968.0
    assert result.current_option_price == 15.0
    assert result.current_option_iv == 0.1954


def test_evaluate_calculates_target_iv() -> None:
    valuator = SingleOptionValuator()

    result = valuator.evaluate(
        make_valid_input()
    )

    expected = (
        0.1954
        * (
            29.55 / 26.70
        )
    )

    assert result.target_option_iv == pytest.approx(
        expected,
        rel=1e-10,
    )


def test_evaluate_calculates_current_price() -> None:
    valuator = SingleOptionValuator()

    result = valuator.evaluate(
        make_valid_input()
    )

    assert math.isfinite(
        result.current_theoretical_price
    )

    assert result.current_theoretical_price >= 0.0


def test_evaluate_calculates_target_price() -> None:
    valuator = SingleOptionValuator()

    result = valuator.evaluate(
        make_valid_input()
    )

    assert math.isfinite(
        result.target_theoretical_price
    )

    assert result.target_theoretical_price >= 0.0


# ==========================================================
# Greeks
# ==========================================================


def test_evaluate_calculates_current_greeks() -> None:
    valuator = SingleOptionValuator()

    result = valuator.evaluate(
        make_valid_input()
    )

    assert math.isfinite(
        result.current_delta
    )

    assert math.isfinite(
        result.current_gamma
    )

    assert math.isfinite(
        result.current_theta
    )


def test_evaluate_calculates_target_greeks() -> None:
    valuator = SingleOptionValuator()

    result = valuator.evaluate(
        make_valid_input()
    )

    assert math.isfinite(
        result.target_delta
    )

    assert math.isfinite(
        result.target_gamma
    )

    assert math.isfinite(
        result.target_theta
    )


# ==========================================================
# Taylor
# ==========================================================


def test_evaluate_calculates_taylor_prices() -> None:
    valuator = SingleOptionValuator()

    result = valuator.evaluate(
        make_valid_input()
    )

    assert math.isfinite(
        result.taylor_first_order_price
    )

    assert math.isfinite(
        result.taylor_second_order_price
    )


# ==========================================================
# Result Calculations
# ==========================================================


def test_result_price_change() -> None:
    valuator = SingleOptionValuator()

    result = valuator.evaluate(
        make_valid_input()
    )

    assert result.theoretical_price_change == pytest.approx(
        result.target_theoretical_price
        - result.current_theoretical_price
    )


def test_result_to_dict() -> None:
    valuator = SingleOptionValuator()

    result = valuator.evaluate(
        make_valid_input()
    )

    data = result.to_dict()

    assert data["symbol"] == "AU2608-C-968"

    assert (
        data["target_option_iv"]
        == result.target_option_iv
    )

    assert (
        data["target_theoretical_price"]
        == result.target_theoretical_price
    )


# ==========================================================
# PUT
# ==========================================================


def test_put_option_is_supported() -> None:
    values = make_valid_input().__dict__

    values["symbol"] = "AU2608-P-968"
    values["option_type"] = OptionType.PUT

    inputs = SingleOptionValuationInput(
        **values
    )

    result = SingleOptionValuator().evaluate(
        inputs
    )

    assert result.symbol == "AU2608-P-968"

    assert (
        result.current_theoretical_price
        >= 0.0
    )

    assert (
        result.target_theoretical_price
        >= 0.0
    )


# ==========================================================
# String Compatibility
# ==========================================================


def test_string_option_type_is_supported() -> None:
    values = make_valid_input().__dict__

    values["option_type"] = "CALL"

    inputs = SingleOptionValuationInput(
        **values
    )

    result = SingleOptionValuator().evaluate(
        inputs
    )

    assert result.symbol == "AU2608-C-968"


def test_string_direction_is_supported() -> None:
    values = make_valid_input().__dict__

    values["direction"] = "LONG"

    inputs = SingleOptionValuationInput(
        **values
    )

    result = SingleOptionValuator().evaluate(
        inputs
    )

    assert result.symbol == "AU2608-C-968"


# ==========================================================
# Public API
# ==========================================================


def test_public_exports() -> None:
    from core.single_option_valuation import (
        ReferenceVolatilityScenario,
        SingleOptionValuationInput,
        SingleOptionValuationResult,
        SingleOptionValuator,
    )

    assert ReferenceVolatilityScenario is not None
    assert SingleOptionValuationInput is not None
    assert SingleOptionValuationResult is not None
    assert SingleOptionValuator is not None