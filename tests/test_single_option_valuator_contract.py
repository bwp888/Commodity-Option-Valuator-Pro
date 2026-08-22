"""
Commodity Option Valuator Pro
=============================

Single Option Valuator Contract Tests.

Commit 0035 - Phase 1
---------------------

Purpose
-------
Lock the real SingleOptionValuator orchestration contract before
adding broader boundary and exception coverage.

Real production contract
------------------------
SingleOptionValuationInput
        |
        v
SingleOptionValuator
        |
        +--> Option
        |
        +--> BlackScholes
        |
        +--> Greeks
        |
        +--> ReferenceVolatilityScenario
        |
        +--> TaylorValuator
        |
        +--> SingleOptionValuationResult
        |
        +--> ComprehensiveEvaluator
        |
        v
SingleOptionValuationResult
    + comprehensive_evaluation

Important
---------
These tests intentionally verify the existing production contract.

They do NOT:
- redesign SingleOptionValuator
- redesign ComprehensiveEvaluator
- replace BlackScholes
- replace Greeks
- replace TaylorValuator
- introduce a new valuation engine
- modify ValuationEngine
- modify ScannerBatchValuator
- modify ScannerBatchWorkflow
- modify ui/scanner.py
"""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import Mock

import pytest

from core.comprehensive_evaluation import (
    ComprehensiveEvaluationResult,
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
    Build a real production-compatible valuation input.

    This helper deliberately uses the public
    SingleOptionValuationInput contract.
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


def make_mock_comprehensive_result(
    symbol: str = "AU2608-C-968",
) -> Mock:
    """
    Create a controlled comprehensive-evaluation result.

    The actual SingleOptionValuator contract only requires that
    ComprehensiveEvaluator.evaluate() returns an object which is
    stored in SingleOptionValuationResult.comprehensive_evaluation.

    A spec is used so the test cannot accidentally invent a
    non-existent public attribute.
    """
    return Mock(
        spec=ComprehensiveEvaluationResult,
        symbol=symbol,
    )


def make_mock_comprehensive_evaluator(
    result: Mock | None = None,
) -> Mock:
    """
    Create a controlled ComprehensiveEvaluator dependency.

    This uses the real public class as the mock specification.
    """
    evaluator = Mock(
        spec=ComprehensiveEvaluator,
    )

    evaluator.evaluate.return_value = (
        result
        if result is not None
        else make_mock_comprehensive_result()
    )

    return evaluator


def make_valuator_with_mock_evaluator(
    result: Mock | None = None,
) -> tuple[
    SingleOptionValuator,
    Mock,
    Mock,
]:
    """
    Create SingleOptionValuator using its real dependency-injection
    contract.
    """
    evaluator = make_mock_comprehensive_evaluator(
        result=result,
    )

    valuator = SingleOptionValuator(
        comprehensive_evaluator=evaluator,
    )

    return (
        valuator,
        evaluator,
        evaluator.evaluate.return_value,
    )


# ============================================================
# 1. Public Construction Contract
# ============================================================


def test_single_option_valuator_can_be_constructed_without_dependency() -> None:
    """
    The existing public constructor supports the default path.

    When no evaluator is supplied, SingleOptionValuator creates
    a ComprehensiveEvaluator itself.
    """
    valuator = SingleOptionValuator()

    assert isinstance(
        valuator,
        SingleOptionValuator,
    )

    assert isinstance(
        valuator.comprehensive_evaluator,
        ComprehensiveEvaluator,
    )


def test_single_option_valuator_accepts_existing_evaluator() -> None:
    """
    The existing constructor explicitly supports dependency
    injection for ComprehensiveEvaluator.
    """
    evaluator = make_mock_comprehensive_evaluator()

    valuator = SingleOptionValuator(
        comprehensive_evaluator=evaluator,
    )

    assert (
        valuator.comprehensive_evaluator
        is evaluator
    )


# ============================================================
# 2. Normal Evaluation Contract
# ============================================================


def test_evaluate_returns_single_option_valuation_result() -> None:
    """
    evaluate() must return the existing
    SingleOptionValuationResult contract.
    """
    valuator, _, _ = (
        make_valuator_with_mock_evaluator()
    )

    result = valuator.evaluate(
        make_valid_input()
    )

    assert isinstance(
        result,
        SingleOptionValuationResult,
    )


def test_evaluate_populates_comprehensive_evaluation() -> None:
    """
    The production docstring and implementation explicitly state
    that newly evaluated results contain a comprehensive evaluation.
    """
    valuator, evaluator, comprehensive_result = (
        make_valuator_with_mock_evaluator()
    )

    result = valuator.evaluate(
        make_valid_input()
    )

    assert (
        result.comprehensive_evaluation
        is comprehensive_result
    )

    evaluator.evaluate.assert_called_once()


def test_evaluate_passes_base_result_to_comprehensive_evaluator() -> None:
    """
    ComprehensiveEvaluator must receive the intermediate
    SingleOptionValuationResult before the final replacement.

    This verifies the existing orchestration boundary rather than
    reimplementing the comprehensive evaluation logic.
    """
    valuator, evaluator, _ = (
        make_valuator_with_mock_evaluator()
    )

    result = valuator.evaluate(
        make_valid_input()
    )

    evaluator.evaluate.assert_called_once()

    passed_result = (
        evaluator.evaluate.call_args.args[0]
    )

    assert isinstance(
        passed_result,
        SingleOptionValuationResult,
    )

    assert (
        passed_result.comprehensive_evaluation
        is None
    )

    assert (
        passed_result.symbol
        == result.symbol
        == "AU2608-C-968"
    )


# ============================================================
# 3. Input Preservation Contract
# ============================================================


def test_evaluate_preserves_market_input_values() -> None:
    """
    The existing result contract must preserve the input market
    state rather than replacing it with calculated values.
    """
    valuator, _, _ = (
        make_valuator_with_mock_evaluator()
    )

    inputs = make_valid_input()

    result = valuator.evaluate(
        inputs
    )

    assert (
        result.symbol
        == inputs.symbol
    )

    assert (
        result.current_futures_price
        == inputs.current_futures_price
    )

    assert (
        result.target_futures_price
        == inputs.target_futures_price
    )

    assert (
        result.strike
        == inputs.strike
    )

    assert (
        result.current_option_price
        == inputs.current_option_price
    )

    assert (
        result.current_option_iv
        == inputs.current_option_iv
    )


def test_evaluate_preserves_reference_volatility_values() -> None:
    """
    The reference-volatility scenario is retained in the result.
    """
    valuator, _, _ = (
        make_valuator_with_mock_evaluator()
    )

    inputs = make_valid_input()

    result = valuator.evaluate(
        inputs
    )

    assert (
        result.reference_volatility_current
        == inputs.reference_volatility.current
    )

    assert (
        result.reference_volatility_target
        == inputs.reference_volatility.target
    )

    assert (
        result.reference_volatility_change_percent
        == pytest.approx(
            inputs.reference_volatility.relative_change_percent
        )
    )


# ============================================================
# 4. Existing Core Valuation Chain
# ============================================================


def test_evaluate_produces_current_and_target_valuation() -> None:
    """
    The orchestration layer must continue to produce both current
    and target theoretical prices.

    The numerical pricing implementation itself belongs to the
    existing BlackScholes tests and is intentionally not duplicated.
    """
    valuator, _, _ = (
        make_valuator_with_mock_evaluator()
    )

    result = valuator.evaluate(
        make_valid_input()
    )

    assert result.current_theoretical_price >= 0.0
    assert result.target_theoretical_price >= 0.0


def test_evaluate_produces_current_and_target_greeks() -> None:
    """
    The orchestration layer must expose the existing current and
    target Greeks contract.
    """
    valuator, _, _ = (
        make_valuator_with_mock_evaluator()
    )

    result = valuator.evaluate(
        make_valid_input()
    )

    assert result.current_delta == pytest.approx(
        result.current_delta
    )

    assert result.current_gamma == pytest.approx(
        result.current_gamma
    )

    assert result.current_theta == pytest.approx(
        result.current_theta
    )

    assert result.target_delta == pytest.approx(
        result.target_delta
    )

    assert result.target_gamma == pytest.approx(
        result.target_gamma
    )

    assert result.target_theta == pytest.approx(
        result.target_theta
    )


def test_evaluate_produces_taylor_comparison_values() -> None:
    """
    Taylor values must be present in the final valuation result.

    Their mathematical correctness belongs to TaylorValuator tests;
    this test only verifies the orchestration output boundary.
    """
    valuator, _, _ = (
        make_valuator_with_mock_evaluator()
    )

    result = valuator.evaluate(
        make_valid_input()
    )

    assert isinstance(
        result.taylor_first_order_price,
        float,
    )

    assert isinstance(
        result.taylor_second_order_price,
        float,
    )


# ============================================================
# 5. Target IV Contract
# ============================================================


def test_evaluate_applies_reference_volatility_to_target_iv() -> None:
    """
    Target option IV must be obtained from the existing
    ReferenceVolatilityScenario.adjust_option_iv() contract.
    """
    valuator, _, _ = (
        make_valuator_with_mock_evaluator()
    )

    inputs = make_valid_input()

    result = valuator.evaluate(
        inputs
    )

    expected = (
        inputs.current_option_iv
        * (
            inputs.reference_volatility.target
            / inputs.reference_volatility.current
        )
    )

    assert result.target_option_iv == pytest.approx(
        expected,
        rel=1e-12,
    )


# ============================================================
# 6. Invalid Parser Boundaries
# ============================================================


def test_invalid_option_type_uses_existing_parser_contract() -> None:
    """
    SingleOptionValuator._parse_option_type() owns the existing
    option-type normalization boundary.

    The production contract is ValueError with the established
    message.
    """
    valuator, evaluator, _ = (
        make_valuator_with_mock_evaluator()
    )

    values = make_valid_input().__dict__
    values["option_type"] = "INVALID"

    inputs = SingleOptionValuationInput(
        **values
    )

    with pytest.raises(
        ValueError,
        match="option_type must be CALL or PUT",
    ):
        valuator.evaluate(
            inputs
        )

    evaluator.evaluate.assert_not_called()


def test_invalid_direction_uses_existing_parser_contract() -> None:
    """
    SingleOptionValuator._parse_direction() owns the existing
    direction normalization boundary.
    """
    valuator, evaluator, _ = (
        make_valuator_with_mock_evaluator()
    )

    values = make_valid_input().__dict__
    values["direction"] = "INVALID"

    inputs = SingleOptionValuationInput(
        **values
    )

    with pytest.raises(
        ValueError,
        match="direction must be LONG or SHORT",
    ):
        valuator.evaluate(
            inputs
        )

    evaluator.evaluate.assert_not_called()


# ============================================================
# 7. Validation Delegation
# ============================================================


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
def test_invalid_input_stops_before_comprehensive_evaluation(
    field: str,
    value: float,
) -> None:
    """
    SingleOptionValuator must honor the existing
    SingleOptionValuationInput.validate() boundary.

    No comprehensive evaluation is allowed when input validation
    fails.
    """
    valuator, evaluator, _ = (
        make_valuator_with_mock_evaluator()
    )

    values = make_valid_input().__dict__
    values[field] = value

    inputs = SingleOptionValuationInput(
        **values
    )

    with pytest.raises(
        ValueError,
    ):
        valuator.evaluate(
            inputs
        )

    evaluator.evaluate.assert_not_called()


def test_invalid_reference_volatility_stops_before_comprehensive_evaluation() -> None:
    """
    ReferenceVolatilityScenario validation is part of the existing
    input-validation contract.
    """
    valuator, evaluator, _ = (
        make_valuator_with_mock_evaluator()
    )

    values = make_valid_input().__dict__

    values["reference_volatility"] = (
        ReferenceVolatilityScenario(
            current=0.0,
            target=29.55,
        )
    )

    inputs = SingleOptionValuationInput(
        **values
    )

    with pytest.raises(
        ValueError,
        match="reference_volatility_current",
    ):
        valuator.evaluate(
            inputs
        )

    evaluator.evaluate.assert_not_called()


# ============================================================
# 8. Downstream Exception Propagation
# ============================================================