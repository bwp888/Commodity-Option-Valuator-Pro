"""
Commodity Option Valuator Pro
=============================

Comprehensive Evaluator Contract Tests.

Commit 0036 - Phase 1
---------------------

Purpose
-------
Lock the existing ComprehensiveEvaluator production contract before
adding boundary and exception tests.

These tests are intentionally based on the current production
implementation.

Current contract:

    SingleOptionValuationResult-like object
        ↓
    ComprehensiveEvaluator
        ↓
    ComprehensiveEvaluationResult

Important
---------
ComprehensiveEvaluator intentionally accepts a duck-typed valuation
result.

This module therefore does NOT require the input object to be an
instance of SingleOptionValuationResult.

This module does NOT:
- modify ComprehensiveEvaluator
- redesign ComprehensiveEvaluator
- modify SingleOptionValuator
- modify ScannerBatchValuator
- modify ScannerBatchWorkflow
- modify ui/scanner.py
- reimplement scoring logic
- reimplement risk-analysis logic
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from core.comprehensive_evaluation import (
    ComprehensiveDecision,
    ComprehensiveEvaluationResult,
    ComprehensiveEvaluator,
    EvaluationComponents,
)


# ============================================================
# Test Fixtures / Helpers
# ============================================================


@dataclass
class DuckTypedValuationResult:
    """
    Minimal duck-typed valuation result accepted by the current
    ComprehensiveEvaluator contract.
    """

    symbol: str = "AU2608-C-968"

    current_option_price: float = 15.0
    current_theoretical_price: float = 16.0
    current_option_iv: float = 0.20

    current_gamma: float = 0.01
    current_theta: float = -0.20

    target_theoretical_price: float = 24.0
    taylor_first_order_price: float = 23.0
    taylor_second_order_price: float = 23.5

    current_futures_price: float = 900.0


def make_valuation_result(
    **overrides: Any,
) -> DuckTypedValuationResult:
    """
    Build a valid duck-typed valuation result and apply only the
    explicitly requested overrides.
    """

    values = {
        "symbol": "AU2608-C-968",
        "current_option_price": 15.0,
        "current_theoretical_price": 16.0,
        "current_option_iv": 0.20,
        "current_gamma": 0.01,
        "current_theta": -0.20,
        "target_theoretical_price": 24.0,
        "taylor_first_order_price": 23.0,
        "taylor_second_order_price": 23.5,
        "current_futures_price": 900.0,
    }

    values.update(overrides)

    return DuckTypedValuationResult(
        **values
    )


# ============================================================
# 1. Default Construction
# ============================================================


def test_comprehensive_evaluator_can_be_constructed_without_arguments() -> None:
    """
    The production evaluator supports default construction.
    """

    evaluator = ComprehensiveEvaluator()

    assert isinstance(
        evaluator,
        ComprehensiveEvaluator,
    )


# ============================================================
# 2. Normal Evaluation Returns Existing Result Contract
# ============================================================


def test_evaluate_returns_comprehensive_evaluation_result() -> None:
    """
    evaluate() returns the existing ComprehensiveEvaluationResult
    contract.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result()
    )

    assert isinstance(
        result,
        ComprehensiveEvaluationResult,
    )


# ============================================================
# 3. Result Symbol
# ============================================================


def test_evaluation_result_preserves_symbol() -> None:
    """
    The result symbol is copied from the valuation input.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result(
            symbol="AU2608-P-968",
        )
    )

    assert result.symbol == "AU2608-P-968"


# ============================================================
# 4. Result Core Fields
# ============================================================


def test_evaluation_result_contains_core_contract_fields() -> None:
    """
    ComprehensiveEvaluationResult exposes the production-level
    decision, score, risk score, risk level, components and reasons.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result()
    )

    assert hasattr(
        result,
        "symbol",
    )

    assert hasattr(
        result,
        "decision",
    )

    assert hasattr(
        result,
        "score",
    )

    assert hasattr(
        result,
        "risk_score",
    )

    assert hasattr(
        result,
        "risk_level",
    )

    assert hasattr(
        result,
        "components",
    )

    assert hasattr(
        result,
        "reasons",
    )


# ============================================================
# 5. Decision Is Existing Enum
# ============================================================


def test_decision_uses_existing_comprehensive_decision_enum() -> None:
    """
    Decision values belong to the existing ComprehensiveDecision
    enum rather than a newly invented string contract.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result()
    )

    assert isinstance(
        result.decision,
        ComprehensiveDecision,
    )


# ============================================================
# 6. Components Contract
# ============================================================


def test_components_uses_existing_evaluation_components_contract() -> None:
    """
    The components field is the existing EvaluationComponents
    dataclass.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result()
    )

    assert isinstance(
        result.components,
        EvaluationComponents,
    )


# ============================================================
# 7. Component Fields
# ============================================================


def test_evaluation_components_expose_all_existing_score_components() -> None:
    """
    EvaluationComponents exposes the five component scores and the
    total score used by ComprehensiveEvaluator.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result()
    )

    components = result.components

    assert hasattr(
        components,
        "valuation_score",
    )

    assert hasattr(
        components,
        "iv_score",
    )

    assert hasattr(
        components,
        "theta_score",
    )

    assert hasattr(
        components,
        "gamma_score",
    )

    assert hasattr(
        components,
        "taylor_score",
    )

    assert hasattr(
        components,
        "total_score",
    )


# ============================================================
# 8. Total Score Is Numeric
# ============================================================


def test_total_score_is_numeric() -> None:
    """
    The production score contract is numeric.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result()
    )

    assert isinstance(
        result.components.total_score,
        (int, float),
    )


# ============================================================
# 9. Result Score Matches Component Total Score
# ============================================================


def test_result_score_matches_component_total_score() -> None:
    """
    The top-level result score represents the total score produced
    by EvaluationComponents.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result()
    )

    assert result.score == pytest.approx(
        result.components.total_score,
    )


# ============================================================
# 10. Risk Score Is Numeric
# ============================================================


def test_risk_score_is_numeric() -> None:
    """
    risk_score is exposed as a numeric result field.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result()
    )

    assert isinstance(
        result.risk_score,
        (int, float),
    )


# ============================================================
# 11. Risk Level Is Present
# ============================================================


def test_risk_level_is_present_in_result() -> None:
    """
    ComprehensiveEvaluationResult exposes the risk level generated
    by the existing risk-analysis path.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result()
    )

    assert result.risk_level is not None


# ============================================================
# 12. Reasons Are Structured
# ============================================================


def test_reasons_are_structured_reason_objects() -> None:
    """
    The current production contract exposes reasons as a tuple of
    structured EvaluationReason objects.

    The exact number of reasons is intentionally not asserted here.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result()
    )

    assert isinstance(
        result.reasons,
        tuple,
    )

    for reason in result.reasons:
        assert hasattr(
            reason,
            "category",
        )

        assert hasattr(
            reason,
            "positive",
        )

        assert hasattr(
            reason,
            "message",
        )


# ============================================================
# 13. Reason Messages
# ============================================================


def test_reason_messages_are_available_as_text_values() -> None:
    """
    Every structured reason exposes a text message.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result()
    )

    for reason in result.reasons:
        assert isinstance(
            reason.message,
            str,
        )


# ============================================================
# 14. Result Can Be Converted To Dictionary
# ============================================================


def test_result_to_dict_returns_dictionary() -> None:
    """
    ComprehensiveEvaluationResult.to_dict() is part of the current
    serialization contract.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result()
    )

    payload = result.to_dict()

    assert isinstance(
        payload,
        dict,
    )


# ============================================================
# 15. Result To-Dict Contains Core Keys
# ============================================================


def test_result_to_dict_contains_existing_core_keys() -> None:
    """
    to_dict() exposes the existing top-level result fields.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result()
    )

    payload = result.to_dict()

    expected_keys = {
        "symbol",
        "decision",
        "score",
        "risk_score",
        "risk_level",
        "components",
        "reasons",
    }

    assert expected_keys.issubset(
        payload.keys()
    )


# ============================================================
# 16. Evaluate-To-Dict Returns Dictionary
# ============================================================


def test_evaluate_to_dict_returns_dictionary() -> None:
    """
    ComprehensiveEvaluator.evaluate_to_dict() is the existing
    dictionary-level convenience API.
    """

    evaluator = ComprehensiveEvaluator()

    payload = evaluator.evaluate_to_dict(
        make_valuation_result()
    )

    assert isinstance(
        payload,
        dict,
    )


# ============================================================
# 17. Evaluate-To-Dict Matches Result Serialization
# ============================================================


def test_evaluate_to_dict_matches_evaluate_result_serialization() -> None:
    """
    evaluate_to_dict() should expose the same serialization contract
    as evaluate(...).to_dict().
    """

    evaluator = ComprehensiveEvaluator()

    valuation_result = make_valuation_result()

    result_payload = evaluator.evaluate(
        valuation_result
    ).to_dict()

    direct_payload = evaluator.evaluate_to_dict(
        valuation_result
    )

    assert direct_payload == result_payload


# ============================================================
# 18. Duck-Typed Input Is Accepted
# ============================================================


def test_duck_typed_valuation_result_is_accepted() -> None:
    """
    The current production implementation intentionally accepts a
    duck-typed valuation result.

    This test locks that behavior instead of imposing an
    isinstance(SingleOptionValuationResult) requirement.
    """

    evaluator = ComprehensiveEvaluator()

    valuation_result = make_valuation_result()

    result = evaluator.evaluate(
        valuation_result
    )

    assert isinstance(
        result,
        ComprehensiveEvaluationResult,
    )


# ============================================================
# 19. Input Object Is Not Replaced By Evaluation
# ============================================================


def test_evaluation_does_not_replace_input_object() -> None:
    """
    ComprehensiveEvaluator consumes the valuation result and returns
    a separate ComprehensiveEvaluationResult.

    The original valuation object remains the same object.
    """

    evaluator = ComprehensiveEvaluator()

    valuation_result = make_valuation_result()

    before_id = id(
        valuation_result
    )

    result = evaluator.evaluate(
        valuation_result
    )

    assert id(
        valuation_result
    ) == before_id

    assert result is not valuation_result


# ============================================================
# 20. Symbol Remains Stable Across Serialization
# ============================================================


def test_symbol_remains_stable_across_result_serialization() -> None:
    """
    Symbol survives the evaluate() -> to_dict() boundary.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result(
            symbol="AU2608-P-968",
        )
    )

    payload = result.to_dict()

    assert payload["symbol"] == "AU2608-P-968"


# ============================================================
# 21. Decision Serialization Uses Existing Value
# ============================================================


def test_decision_serialization_uses_existing_enum_value() -> None:
    """
    The serialized decision corresponds to the existing enum value.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result()
    )

    payload = result.to_dict()

    assert payload["decision"] == result.decision.value


# ============================================================
# 22. Components Serialization Is A Dictionary
# ============================================================


def test_components_are_serialized_as_dictionary() -> None:
    """
    The serialized components field remains structured.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result()
    )

    payload = result.to_dict()

    assert isinstance(
        payload["components"],
        dict,
    )


# ============================================================
# 23. Reasons Serialization Is A List
# ============================================================


def test_reasons_are_serialized_as_list() -> None:
    """
    The in-memory reasons contract is a tuple, while the serialized
    dictionary contract exposes reasons as a list.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result()
    )

    payload = result.to_dict()

    assert isinstance(
        result.reasons,
        tuple,
    )

    assert isinstance(
        payload["reasons"],
        list,
    )


# ============================================================
# 24. Required Missing Attribute Is Rejected
# ============================================================


@dataclass
class MissingSymbolValuationResult:
    """
    Deliberately incomplete duck-typed object.

    This verifies that the evaluator consumes its actual required
    attributes instead of silently inventing defaults.
    """

    current_option_price: float = 15.0
    current_theoretical_price: float = 16.0
    current_option_iv: float = 0.20

    current_gamma: float = 0.01
    current_theta: float = -0.20

    target_theoretical_price: float = 24.0
    taylor_first_order_price: float = 23.0
    taylor_second_order_price: float = 23.5

    current_futures_price: float = 900.0


def test_missing_required_symbol_attribute_is_rejected() -> None:
    """
    The current duck-typed contract requires symbol.

    Production validation raises TypeError when a required attribute
    is missing.
    """

    evaluator = ComprehensiveEvaluator()

    with pytest.raises(
        TypeError,
        match=(
            "valuation_result is missing "
            "required attribute: symbol"
        ),
    ):
        evaluator.evaluate(
            MissingSymbolValuationResult()
        )


# ============================================================
# 25. Missing Current Futures Price Is Rejected
# ============================================================


@dataclass
class MissingCurrentFuturesPriceValuationResult:
    """
    Deliberately incomplete duck-typed valuation result.

    current_futures_price is consumed by the risk-analysis adapter.
    It is therefore intentionally absent from this fixture.
    """

    symbol: str = "AU2608-C-968"

    current_option_price: float = 15.0
    current_theoretical_price: float = 16.0
    current_option_iv: float = 0.20

    current_gamma: float = 0.01
    current_theta: float = -0.20

    target_theoretical_price: float = 24.0
    taylor_first_order_price: float = 23.0
    taylor_second_order_price: float = 23.5


def test_missing_current_futures_price_is_rejected() -> None:
    """
    Risk analysis consumes current_futures_price.

    The evaluator must not silently create a replacement value.
    """

    evaluator = ComprehensiveEvaluator()

    with pytest.raises(
        AttributeError,
    ):
        evaluator.evaluate(
            MissingCurrentFuturesPriceValuationResult()
        )


# ============================================================
# 26. Symbol Value Is Preserved
# ============================================================


def test_symbol_value_is_consumed_without_silent_replacement() -> None:
    """
    The evaluator preserves the supplied symbol value rather than
    replacing it with a default symbol.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result(
            symbol="CUSTOM-SYMBOL",
        )
    )

    assert result.symbol == "CUSTOM-SYMBOL"


# ============================================================
# 27. Existing Decision Values Are Restricted
# ============================================================


def test_decision_value_belongs_to_existing_decision_contract() -> None:
    """
    The evaluator must return one of the existing production decision
    values.
    """

    evaluator = ComprehensiveEvaluator()

    result = evaluator.evaluate(
        make_valuation_result()
    )

    allowed_values = {
        decision.value
        for decision in ComprehensiveDecision
    }

    assert result.decision.value in allowed_values