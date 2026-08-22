"""
Commodity Option Valuator Pro
=============================

Single Option Valuator Boundary Tests.

Commit 0035 - Phase 2
---------------------

Purpose
-------
Validate the real runtime boundaries and exception boundaries of
SingleOptionValuator.

These tests complement:

    tests/test_single_option_valuator_contract.py

The Phase 1 contract tests lock the orchestration contract.

This Phase 2 module focuses on boundary behavior that is not merely
a duplicate of the existing mathematical model tests.

Important
---------
These tests intentionally use the existing production contracts.

They do NOT:
- modify SingleOptionValuator
- modify ComprehensiveEvaluator
- redesign ValuationEngine
- modify ScannerBatchValuator
- modify ScannerBatchWorkflow
- modify ui/scanner.py
- reimplement Black-Scholes
- reimplement Greeks
- reimplement Taylor valuation
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from core.comprehensive_evaluation import (
    ComprehensiveEvaluator,
)
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


# ============================================================
# Test Helpers
# ============================================================


def make_valid_input() -> SingleOptionValuationInput:
    """
    Build the existing production-compatible input contract.
    """
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
        risk_free_rate=0.025,
        direction=OptionDirection.LONG,
    )


def make_evaluator_mock() -> Mock:
    """
    Create a mock using the real ComprehensiveEvaluator contract.
    """
    evaluator = Mock(
        spec=ComprehensiveEvaluator,
    )

    evaluator.evaluate.return_value = Mock()

    return evaluator


def make_valuator() -> tuple[
    SingleOptionValuator,
    Mock,
]:
    """
    Create SingleOptionValuator with a controlled existing
    ComprehensiveEvaluator dependency.
    """
    evaluator = make_evaluator_mock()

    valuator = SingleOptionValuator(
        comprehensive_evaluator=evaluator,
    )

    return valuator, evaluator


def build_input(
    **overrides: object,
) -> SingleOptionValuationInput:
    """
    Build a production input while changing only explicitly
    requested fields.
    """
    values = make_valid_input().__dict__
    values.update(overrides)

    return SingleOptionValuationInput(
        **values,
    )


# ============================================================
# 1. Minimum Valid Remaining Days
# ============================================================


def test_one_remaining_day_is_a_valid_evaluation_boundary() -> None:
    """
    remaining_days > 0 is the existing validation contract.

    Therefore one calendar day is the smallest valid value.
    """
    valuator, evaluator = make_valuator()

    result = valuator.evaluate(
        build_input(
            remaining_days=1,
        )
    )

    assert isinstance(
        result,
        SingleOptionValuationResult,
    )

    assert evaluator.evaluate.call_count == 1


# ============================================================
# 2. Zero Current Market Option Price
# ============================================================


def test_zero_current_option_price_is_valid_boundary() -> None:
    """
    current_option_price may be zero.

    The production validation explicitly rejects only negative
    values, not zero.
    """
    valuator, evaluator = make_valuator()

    result = valuator.evaluate(
        build_input(
            current_option_price=0.0,
        )
    )

    assert isinstance(
        result,
        SingleOptionValuationResult,
    )

    assert result.current_option_price == 0.0

    assert evaluator.evaluate.call_count == 1


# ============================================================
# 3. Zero Risk-Free Rate
# ============================================================


def test_zero_risk_free_rate_is_valid_boundary() -> None:
    """
    risk_free_rate may be zero.

    The existing validation contract rejects negative values only.
    """
    valuator, evaluator = make_valuator()

    result = valuator.evaluate(
        build_input(
            risk_free_rate=0.0,
        )
    )

    assert isinstance(
        result,
        SingleOptionValuationResult,
    )

    assert evaluator.evaluate.call_count == 1


# ============================================================
# 4. Unchanged Reference Volatility
# ============================================================


def test_unchanged_reference_volatility_preserves_option_iv() -> None:
    """
    If reference volatility does not change, the target option IV
    must remain equal to the current option IV.

    This verifies the existing scenario contract without duplicating
    the generic ReferenceVolatilityScenario unit tests.
    """
    valuator, _ = make_valuator()

    result = valuator.evaluate(
        build_input(
            reference_volatility=(
                ReferenceVolatilityScenario(
                    current=20.0,
                    target=20.0,
                )
            ),
        )
    )

    assert result.target_option_iv == pytest.approx(
        result.current_option_iv,
        rel=1e-12,
    )


# ============================================================
# 5. Unchanged Futures Price
# ============================================================


def test_same_current_and_target_futures_price_is_valid() -> None:
    """
    The existing input validation requires both futures prices to be
    positive but does not require them to differ.

    Therefore equal current and target futures prices are a valid
    scenario boundary.
    """
    valuator, evaluator = make_valuator()

    result = valuator.evaluate(
        build_input(
            target_futures_price=900.0,
        )
    )

    assert isinstance(
        result,
        SingleOptionValuationResult,
    )

    assert (
        result.current_futures_price
        == result.target_futures_price
        == 900.0
    )

    assert evaluator.evaluate.call_count == 1


# ============================================================
# 6. Lowercase Option Type
# ============================================================


def test_lowercase_option_type_is_normalized_by_existing_parser() -> None:
    """
    _parse_option_type() explicitly uppercases string values before
    constructing OptionType.
    """
    valuator, evaluator = make_valuator()

    result = valuator.evaluate(
        build_input(
            option_type="call",
        )
    )

    assert result.symbol == "AU2608-C-968"

    assert evaluator.evaluate.call_count == 1


# ============================================================
# 7. Lowercase Direction
# ============================================================


def test_lowercase_direction_is_normalized_by_existing_parser() -> None:
    """
    _parse_direction() explicitly uppercases string values before
    constructing OptionDirection.
    """
    valuator, evaluator = make_valuator()

    result = valuator.evaluate(
        build_input(
            direction="long",
        )
    )

    assert result.symbol == "AU2608-C-968"

    assert evaluator.evaluate.call_count == 1


# ============================================================
# 8. SHORT Direction Boundary
# ============================================================


def test_short_direction_is_supported_by_existing_option_contract() -> None:
    """
    SHORT is part of the existing OptionDirection contract.

    This test verifies that SingleOptionValuator accepts the value
    and reaches the normal downstream evaluation path.
    """
    valuator, evaluator = make_valuator()

    result = valuator.evaluate(
        build_input(
            direction=OptionDirection.SHORT,
        )
    )

    assert isinstance(
        result,
        SingleOptionValuationResult,
    )

    assert evaluator.evaluate.call_count == 1


# ============================================================
# 9. PUT + SHORT Combination
# ============================================================


def test_put_short_combination_reaches_normal_evaluation_path() -> None:
    """
    Option type and direction are independent production inputs.

    The combined PUT + SHORT boundary must therefore be accepted
    without SingleOptionValuator introducing an artificial
    compatibility restriction.
    """
    valuator, evaluator = make_valuator()

    result = valuator.evaluate(
        build_input(
            symbol="AU2608-P-968",
            option_type=OptionType.PUT,
            direction=OptionDirection.SHORT,
        )
    )

    assert isinstance(
        result,
        SingleOptionValuationResult,
    )

    assert result.symbol == "AU2608-P-968"

    assert evaluator.evaluate.call_count == 1


# ============================================================
# 10. Downstream Exception Boundary
# ============================================================


def test_comprehensive_evaluator_value_error_is_not_swallowed() -> None:
    """
    SingleOptionValuator does not catch exceptions raised by
    ComprehensiveEvaluator.evaluate().

    Therefore a downstream ValueError must propagate unchanged.
    """
    evaluator = Mock(
        spec=ComprehensiveEvaluator,
    )

    expected_error = ValueError(
        "downstream comprehensive evaluation error"
    )

    evaluator.evaluate.side_effect = expected_error

    valuator = SingleOptionValuator(
        comprehensive_evaluator=evaluator,
    )

    with pytest.raises(
        ValueError,
        match="downstream comprehensive evaluation error",
    ):
        valuator.evaluate(
            make_valid_input()
        )

    evaluator.evaluate.assert_called_once()


# ============================================================
# 11. Validation Failure Must Stop Downstream Evaluation
# ============================================================


def test_invalid_remaining_days_does_not_reach_comprehensive_evaluator() -> None:
    """
    Input validation happens before the valuation chain.

    Therefore an invalid remaining_days value must prevent
    ComprehensiveEvaluator from being called.
    """
    valuator, evaluator = make_valuator()

    with pytest.raises(
        ValueError,
        match="remaining_days must be greater than zero",
    ):
        valuator.evaluate(
            build_input(
                remaining_days=0,
            )
        )

    evaluator.evaluate.assert_not_called()


# ============================================================
# 12. Invalid Reference Volatility Must Stop Evaluation
# ============================================================


def test_invalid_reference_volatility_does_not_reach_comprehensive_evaluator() -> None:
    """
    ReferenceVolatilityScenario.validate() is invoked by
    SingleOptionValuationInput.validate().

    Failure must happen before downstream comprehensive evaluation.
    """
    valuator, evaluator = make_valuator()

    invalid_scenario = (
        ReferenceVolatilityScenario(
            current=20.0,
            target=0.0,
        )
    )

    with pytest.raises(
        ValueError,
        match="reference_volatility_target must be greater than zero",
    ):
        valuator.evaluate(
            build_input(
                reference_volatility=invalid_scenario,
            )
        )

    evaluator.evaluate.assert_not_called()


# ============================================================
# 13. Invalid Symbol Must Stop Evaluation
# ============================================================


def test_empty_symbol_does_not_reach_comprehensive_evaluator() -> None:
    """
    Empty symbol is rejected by the existing input validation
    contract before any downstream evaluator is called.
    """
    valuator, evaluator = make_valuator()

    with pytest.raises(
        ValueError,
        match="symbol cannot be empty",
    ):
        valuator.evaluate(
            build_input(
                symbol="",
            )
        )

    evaluator.evaluate.assert_not_called()


# ============================================================
# 14. Negative Market Price Must Stop Evaluation
# ============================================================


def test_negative_current_option_price_does_not_reach_comprehensive_evaluator() -> None:
    """
    Negative current option price is outside the existing input
    contract and must fail before downstream evaluation.
    """
    valuator, evaluator = make_valuator()

    with pytest.raises(
        ValueError,
        match="current_option_price cannot be negative",
    ):
        valuator.evaluate(
            build_input(
                current_option_price=-0.01,
            )
        )

    evaluator.evaluate.assert_not_called()


# ============================================================
# 15. Negative Risk-Free Rate Must Stop Evaluation
# ============================================================


def test_negative_risk_free_rate_does_not_reach_comprehensive_evaluator() -> None:
    """
    Negative risk-free rate is outside the current production input
    contract and must fail before downstream evaluation.
    """
    valuator, evaluator = make_valuator()

    with pytest.raises(
        ValueError,
        match="risk_free_rate cannot be negative",
    ):
        valuator.evaluate(
            build_input(
                risk_free_rate=-0.0001,
            )
        )

    evaluator.evaluate.assert_not_called()


# ============================================================
# 16. Invalid Target Futures Price Must Stop Evaluation
# ============================================================


def test_zero_target_futures_price_does_not_reach_comprehensive_evaluator() -> None:
    """
    target_futures_price must be strictly greater than zero.
    """
    valuator, evaluator = make_valuator()

    with pytest.raises(
        ValueError,
        match="target_futures_price must be greater than zero",
    ):
        valuator.evaluate(
            build_input(
                target_futures_price=0.0,
            )
        )

    evaluator.evaluate.assert_not_called()


# ============================================================
# 17. Invalid Current Futures Price Must Stop Evaluation
# ============================================================


def test_zero_current_futures_price_does_not_reach_comprehensive_evaluator() -> None:
    """
    current_futures_price must be strictly greater than zero.
    """
    valuator, evaluator = make_valuator()

    with pytest.raises(
        ValueError,
        match="current_futures_price must be greater than zero",
    ):
        valuator.evaluate(
            build_input(
                current_futures_price=0.0,
            )
        )

    evaluator.evaluate.assert_not_called()


# ============================================================
# 18. Invalid Strike Must Stop Evaluation
# ============================================================


def test_zero_strike_does_not_reach_comprehensive_evaluator() -> None:
    """
    Strike must be strictly greater than zero.
    """
    valuator, evaluator = make_valuator()

    with pytest.raises(
        ValueError,
        match="strike must be greater than zero",
    ):
        valuator.evaluate(
            build_input(
                strike=0.0,
            )
        )

    evaluator.evaluate.assert_not_called()


# ============================================================
# 19. Invalid Current IV Must Stop Evaluation
# ============================================================


def test_zero_current_iv_does_not_reach_comprehensive_evaluator() -> None:
    """
    Current option IV must be strictly greater than zero.
    """
    valuator, evaluator = make_valuator()

    with pytest.raises(
        ValueError,
        match="current_option_iv must be greater than zero",
    ):
        valuator.evaluate(
            build_input(
                current_option_iv=0.0,
            )
        )

    evaluator.evaluate.assert_not_called()


# ============================================================
# 20. Invalid Option Type Must Stop Evaluation
# ============================================================


def test_invalid_option_type_does_not_reach_comprehensive_evaluator() -> None:
    """
    Invalid option type is rejected by the existing parser before
    ComprehensiveEvaluator is reached.
    """
    valuator, evaluator = make_valuator()

    with pytest.raises(
        ValueError,
        match="option_type must be CALL or PUT",
    ):
        valuator.evaluate(
            build_input(
                option_type="NOT_AN_OPTION",
            )
        )

    evaluator.evaluate.assert_not_called()


# ============================================================
# 21. Invalid Direction Must Stop Evaluation
# ============================================================


def test_invalid_direction_does_not_reach_comprehensive_evaluator() -> None:
    """
    Invalid direction is rejected by the existing parser before
    ComprehensiveEvaluator is reached.
    """
    valuator, evaluator = make_valuator()

    with pytest.raises(
        ValueError,
        match="direction must be LONG or SHORT",
    ):
        valuator.evaluate(
            build_input(
                direction="NOT_A_DIRECTION",
            )
        )

    evaluator.evaluate.assert_not_called()