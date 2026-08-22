"""
Commodity Option Valuator Pro
=============================

Comprehensive Evaluator Boundary Tests.

Commit 0036 - Phase 2
---------------------

Purpose
-------
Validate the real result boundaries and exception boundaries of
ComprehensiveEvaluator.

Engineering Principle
---------------------
These tests MUST follow the existing production contract.

The order is:

    production contract
        ↓
    actual call path
        ↓
    exception ownership
        ↓
    boundary assertion

Tests must NOT invent a new contract merely because an assertion
would be convenient.

Important
---------
This module does NOT redesign or modify:

- ComprehensiveEvaluator
- RiskAnalyzer
- SingleOptionValuator
- RecommendationEngine
- RecommendationWorkflow
- UI modules

Production contract reference
------------------------------
ComprehensiveEvaluator.evaluate()
    ↓
_validate_result()
    ↓
_build_risk_analysis()
    ↓
component scoring
    ↓
_decision()
    ↓
_build_reasons()
    ↓
ComprehensiveEvaluationResult

Phase 2 boundary coverage
-------------------------
1. Missing required attributes
2. Missing current futures price
3. Invalid valuation result object
4. Invalid numeric values
5. Boundary scoring
6. Decision boundary
7. Risk gate boundary
8. Reason boundary
9. Taylor boundary
10. IV boundary
11. Theta boundary
12. Gamma boundary
13. Result immutability
14. Existing production exception ownership

Author : Simon
Version : 0.1.0
Python : 3.12
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import SimpleNamespace
from typing import Any

import pytest

from core.comprehensive_evaluation import (
    ComprehensiveDecision,
    ComprehensiveEvaluator,
    ComprehensiveEvaluationResult,
    EvaluationComponents,
    EvaluationReason,
)
from models.risk import RiskLevel


# ==========================================================
# Test Result Fixtures
# ==========================================================


@dataclass
class FixtureValuationResult:
    """
    Local test object matching the actual duck-typed
    ComprehensiveEvaluator contract.

    Important:
    Required attributes are instance fields.

    They intentionally do not use class-level fallback
    attributes because boundary tests must be able to
    represent a genuinely missing attribute.
    """

    symbol: str
    current_option_price: float
    current_theoretical_price: float
    current_option_iv: float
    current_gamma: float
    current_theta: float
    target_theoretical_price: float
    taylor_first_order_price: float
    taylor_second_order_price: float
    current_futures_price: float


def make_result(
    *,
    symbol: str = "AU2608-C-968",
    current_option_price: float = 15.0,
    current_theoretical_price: float = 16.0,
    current_option_iv: float = 0.20,
    current_gamma: float = 0.01,
    current_theta: float = 0.01,
    target_theoretical_price: float = 24.0,
    taylor_first_order_price: float = 23.0,
    taylor_second_order_price: float = 23.5,
    current_futures_price: float = 900.0,
) -> TestValuationResult:
    """
    Create a valid valuation result according to the
    current production duck-typed contract.
    """

    return FixtureValuationResult(
        symbol=symbol,
        current_option_price=current_option_price,
        current_theoretical_price=current_theoretical_price,
        current_option_iv=current_option_iv,
        current_gamma=current_gamma,
        current_theta=current_theta,
        target_theoretical_price=target_theoretical_price,
        taylor_first_order_price=taylor_first_order_price,
        taylor_second_order_price=taylor_second_order_price,
        current_futures_price=current_futures_price,
    )


# ==========================================================
# Helpers
# ==========================================================


def evaluate(
    result: Any,
) -> ComprehensiveEvaluationResult:
    """
    Evaluate through the real public production entry point.
    """

    evaluator = ComprehensiveEvaluator()

    return evaluator.evaluate(
        result
    )


def valuation_reasons(
    result: ComprehensiveEvaluationResult,
) -> list[EvaluationReason]:
    """
    Return valuation-category reasons.

    Production result.reasons is a tuple.
    The helper converts it to a list only for convenient
    filtering inside the test.
    """

    return [
        reason
        for reason in result.reasons
        if reason.category == "valuation"
    ]


def reason_for(
    result: ComprehensiveEvaluationResult,
    category: str,
) -> EvaluationReason:
    """
    Return the first reason for a category.
    """

    reasons = [
        reason
        for reason in result.reasons
        if reason.category == category
    ]

    assert reasons

    return reasons[0]


# ==========================================================
# Production Contract
# ==========================================================


def test_evaluator_exists() -> None:
    """
    ComprehensiveEvaluator remains available.
    """

    evaluator = ComprehensiveEvaluator()

    assert isinstance(
        evaluator,
        ComprehensiveEvaluator,
    )


def test_valid_result_is_accepted() -> None:
    """
    A result satisfying the current production contract
    must be accepted.
    """

    result = evaluate(
        make_result()
    )

    assert isinstance(
        result,
        ComprehensiveEvaluationResult,
    )


def test_result_symbol_is_preserved() -> None:
    """
    Symbol must pass through unchanged as text.
    """

    result = evaluate(
        make_result(
            symbol="TEST-C-100"
        )
    )

    assert result.symbol == "TEST-C-100"


def test_result_contains_components() -> None:
    """
    Comprehensive result retains component scores.
    """

    result = evaluate(
        make_result()
    )

    assert isinstance(
        result.components,
        EvaluationComponents,
    )


def test_result_contains_risk_information() -> None:
    """
    Risk information remains part of the final result.
    """

    result = evaluate(
        make_result()
    )

    assert isinstance(
        result.risk_score,
        float,
    )

    assert isinstance(
        result.risk_level,
        RiskLevel,
    )


# ==========================================================
# Required Attribute Boundary
# ==========================================================


@pytest.mark.parametrize(
    "missing_attribute",
    [
        "symbol",
        "current_option_price",
        "current_theoretical_price",
        "current_option_iv",
        "current_gamma",
        "current_theta",
        "target_theoretical_price",
        "taylor_first_order_price",
        "taylor_second_order_price",
    ],
)
def test_missing_required_attribute_is_rejected(
    missing_attribute: str,
) -> None:
    """
    Every attribute in the REAL production
    ComprehensiveEvaluator._validate_result() contract
    must be present.

    The test deliberately removes the instance attribute
    from a local test object.

    This avoids accidentally exposing a dataclass class-level
    default and thereby invalidating the boundary test itself.
    """

    result = make_result()

    delattr(
        result,
        missing_attribute,
    )

    evaluator = ComprehensiveEvaluator()

    with pytest.raises(
        TypeError,
        match=(
            "valuation_result is missing "
            f"required attribute: {missing_attribute}"
        ),
    ):
        evaluator.evaluate(
            result
        )


def test_empty_symbol_is_rejected() -> None:
    """
    The production validator explicitly rejects an empty
    symbol with ValueError.
    """

    evaluator = ComprehensiveEvaluator()

    with pytest.raises(
        ValueError,
        match="valuation_result.symbol must not be empty",
    ):
        evaluator.evaluate(
            make_result(
                symbol="   "
            )
        )


# ==========================================================
# current_futures_price Boundary
# ==========================================================


def test_missing_current_futures_price_reaches_risk_adapter() -> None:
    """
    current_futures_price is NOT part of _validate_result().

    It is consumed later by _build_risk_analysis().

    Therefore the expected exception belongs to the actual
    risk-adapter access path.
    """

    result = make_result()

    delattr(
        result,
        "current_futures_price",
    )

    evaluator = ComprehensiveEvaluator()

    with pytest.raises(
        AttributeError,
    ):
        evaluator.evaluate(
            result
        )


def test_current_futures_price_is_consumed_by_risk_adapter() -> None:
    """
    A valid current futures price must be accepted by the
    existing risk adapter.
    """

    result = make_result(
        current_futures_price=950.0
    )

    evaluation = evaluate(
        result
    )

    assert isinstance(
        evaluation,
        ComprehensiveEvaluationResult,
    )


# ==========================================================
# Invalid Object Boundary
# ==========================================================


def test_none_result_is_rejected() -> None:
    """
    None does not satisfy the duck-typed valuation-result
    contract.
    """

    evaluator = ComprehensiveEvaluator()

    with pytest.raises(
        TypeError,
        match="valuation_result is missing required attribute",
    ):
        evaluator.evaluate(
            None
        )


def test_arbitrary_object_is_rejected() -> None:
    """
    An arbitrary object must not be converted into a valuation
    result.
    """

    evaluator = ComprehensiveEvaluator()

    with pytest.raises(
        TypeError,
        match="valuation_result is missing required attribute",
    ):
        evaluator.evaluate(
            object()
        )


# ==========================================================
# Reasons Contract
# ==========================================================


def test_reasons_are_structured_reason_objects() -> None:
    """
    Production ComprehensiveEvaluationResult.reasons is a
    tuple of EvaluationReason objects.
    """

    result = evaluate(
        make_result()
    )

    assert isinstance(
        result.reasons,
        tuple,
    )

    assert result.reasons

    assert all(
        isinstance(
            reason,
            EvaluationReason,
        )
        for reason in result.reasons
    )


def test_reason_categories_are_strings() -> None:
    """
    Each reason category is structured as text.
    """

    result = evaluate(
        make_result()
    )

    assert all(
        isinstance(
            reason.category,
            str,
        )
        for reason in result.reasons
    )


def test_reason_positive_flag_is_boolean() -> None:
    """
    Every reason retains an explicit positive/negative flag.
    """

    result = evaluate(
        make_result()
    )

    assert all(
        isinstance(
            reason.positive,
            bool,
        )
        for reason in result.reasons
    )


def test_reason_message_is_non_empty() -> None:
    """
    Every reason must contain human-readable text.
    """

    result = evaluate(
        make_result()
    )

    assert all(
        reason.message.strip()
        for reason in result.reasons
    )


def test_reason_text_is_available() -> None:
    """
    Existing convenience property remains available.
    """

    result = evaluate(
        make_result()
    )

    assert isinstance(
        result.reason_text,
        str,
    )

    assert result.reason_text.strip()


def test_reason_messages_are_available() -> None:
    """
    Existing reason_messages property remains available.
    """

    result = evaluate(
        make_result()
    )

    assert isinstance(
        result.reason_messages,
        tuple,
    )

    assert result.reason_messages


# ==========================================================
# Valuation Reason Boundary
# ==========================================================


def test_valuation_reason_positive_when_market_below_theoretical() -> None:
    """
    Positive valuation gap:

        theoretical > market

    must produce a positive valuation reason.
    """

    result = evaluate(
        make_result(
            current_option_price=90.0,
            current_theoretical_price=100.0,
        )
    )

    reason = reason_for(
        result,
        "valuation",
    )

    assert reason.positive is True


def test_valuation_reason_is_neutral_when_prices_are_close() -> None:
    """
    A small negative valuation gap must remain in the
    'prices relatively close' branch.

    Important:
    The production formula uses market_price as denominator.
    """

    result = evaluate(
        make_result(
            current_option_price=105.0,
            current_theoretical_price=100.0,
        )
    )

    reason = reason_for(
        result,
        "valuation",
    )

    assert reason.positive is False

    assert (
        "较为接近"
        in reason.message
    )


def test_valuation_reason_changes_at_true_negative_ten_percent_boundary() -> None:
    """
    Production boundary:

        valuation_gap <= -0.10

    Because the denominator is market_price, a market price
    of 112 against theoretical price 100 produces:

        (100 - 112) / 112
        = -10.714...%

    which is genuinely beyond the production -10% boundary.

    This intentionally avoids the previous invalid fixture:

        market=110
        theoretical=100

    because that equals only -9.09%.
    """

    result = evaluate(
        make_result(
            current_option_price=112.0,
            current_theoretical_price=100.0,
        )
    )

    reason = reason_for(
        result,
        "valuation",
    )

    assert reason.positive is False

    assert (
        "明显高于理论价格"
        in reason.message
    )


def test_valuation_reason_changes_at_positive_ten_percent_boundary() -> None:
    """
    Production positive boundary:

        valuation_gap >= 0.10

    A market price of 90 against theoretical price 100 gives:

        (100 - 90) / 90
        = 11.11...%
    """

    result = evaluate(
        make_result(
            current_option_price=90.0,
            current_theoretical_price=100.0,
        )
    )

    reason = reason_for(
        result,
        "valuation",
    )

    assert reason.positive is True

    assert (
        "明显低于理论价格"
        in reason.message
    )


# ==========================================================
# IV Boundaries
# ==========================================================


@pytest.mark.parametrize(
    "iv",
    [
        0.0,
        0.10,
        0.20,
    ],
)
def test_iv_at_or_below_low_boundary_is_favorable(
    iv: float,
) -> None:
    """
    Production IV_LOW = 0.20.
    """

    result = evaluate(
        make_result(
            current_option_iv=iv
        )
    )

    reason = reason_for(
        result,
        "iv",
    )

    assert reason.positive is True

    assert (
        "较低或合理"
        in reason.message
    )


def test_iv_between_low_and_high_is_cautionary() -> None:
    """
    0.20 < IV < 0.50 is the production middle branch.
    """

    result = evaluate(
        make_result(
            current_option_iv=0.35
        )
    )

    reason = reason_for(
        result,
        "iv",
    )

    assert reason.positive is False


@pytest.mark.parametrize(
    "iv",
    [
        0.50,
        0.60,
        1.00,
    ],
)
def test_iv_at_or_above_high_boundary_is_unfavorable(
    iv: float,
) -> None:
    """
    Production IV_HIGH = 0.50.
    """

    result = evaluate(
        make_result(
            current_option_iv=iv
        )
    )

    reason = reason_for(
        result,
        "iv",
    )

    assert reason.positive is False

    assert (
        "偏高"
        in reason.message
    )


# ==========================================================
# Theta Boundaries
# ==========================================================


@pytest.mark.parametrize(
    "theta",
    [
        0.0,
        0.005,
        0.01,
        -0.01,
    ],
)
def test_theta_at_or_below_low_boundary_is_favorable(
    theta: float,
) -> None:
    """
    Theta uses absolute value in production.
    """

    result = evaluate(
        make_result(
            current_theta=theta
        )
    )

    reason = reason_for(
        result,
        "theta",
    )

    assert reason.positive is True


def test_theta_middle_boundary_is_unfavorable() -> None:
    """
    0.01 < abs(theta) < 0.10.
    """

    result = evaluate(
        make_result(
            current_theta=0.05
        )
    )

    reason = reason_for(
        result,
        "theta",
    )

    assert reason.positive is False


@pytest.mark.parametrize(
    "theta",
    [
        0.10,
        0.20,
        -0.10,
    ],
)
def test_theta_at_or_above_high_boundary_is_unfavorable(
    theta: float,
) -> None:
    """
    Production THETA_HIGH = 0.10.
    """

    result = evaluate(
        make_result(
            current_theta=theta
        )
    )

    reason = reason_for(
        result,
        "theta",
    )

    assert reason.positive is False

    assert (
        "较大"
        in reason.message
    )


# ==========================================================
# Gamma Boundaries
# ==========================================================


@pytest.mark.parametrize(
    "gamma",
    [
        0.0,
        0.005,
        0.01,
        -0.01,
    ],
)
def test_gamma_at_or_below_low_boundary_is_favorable(
    gamma: float,
) -> None:
    """
    Gamma uses absolute value in production.
    """

    result = evaluate(
        make_result(
            current_gamma=gamma
        )
    )

    reason = reason_for(
        result,
        "gamma",
    )

    assert reason.positive is True


def test_gamma_middle_boundary_is_unfavorable() -> None:
    """
    0.01 < abs(gamma) < 0.10.
    """

    result = evaluate(
        make_result(
            current_gamma=0.05
        )
    )

    reason = reason_for(
        result,
        "gamma",
    )

    assert reason.positive is False


@pytest.mark.parametrize(
    "gamma",
    [
        0.10,
        0.20,
        -0.10,
    ],
)
def test_gamma_at_or_above_high_boundary_is_unfavorable(
    gamma: float,
) -> None:
    """
    Production GAMMA_HIGH = 0.10.
    """

    result = evaluate(
        make_result(
            current_gamma=gamma
        )
    )

    reason = reason_for(
        result,
        "gamma",
    )

    assert reason.positive is False

    assert (
        "较高"
        in reason.message
    )


# ==========================================================
# Taylor Boundaries
# ==========================================================


def test_taylor_reason_is_positive_with_small_error() -> None:
    """
    Average relative error <= 2% is the production favorable
    boundary.
    """

    result = evaluate(
        make_result(
            target_theoretical_price=100.0,
            taylor_first_order_price=100.0,
            taylor_second_order_price=101.0,
        )
    )

    reason = reason_for(
        result,
        "taylor",
    )

    assert reason.positive is True


def test_taylor_reason_is_negative_with_middle_error() -> None:
    """
    2% < average error < 10%.
    """

    result = evaluate(
        make_result(
            target_theoretical_price=100.0,
            taylor_first_order_price=95.0,
            taylor_second_order_price=95.0,
        )
    )

    reason = reason_for(
        result,
        "taylor",
    )

    assert reason.positive is False

    assert (
        "一定偏差"
        in reason.message
    )


def test_taylor_reason_is_negative_with_large_error() -> None:
    """
    Average error >= 10%.
    """

    result = evaluate(
        make_result(
            target_theoretical_price=100.0,
            taylor_first_order_price=80.0,
            taylor_second_order_price=80.0,
        )
    )

    reason = reason_for(
        result,
        "taylor",
    )

    assert reason.positive is False

    assert (
        "偏差较大"
        in reason.message
    )


def test_taylor_zero_target_does_not_generate_taylor_reason() -> None:
    """
    Production _build_reasons() only generates Taylor reason
    when target > 0.
    """

    result = evaluate(
        make_result(
            target_theoretical_price=0.0,
            taylor_first_order_price=0.0,
            taylor_second_order_price=0.0,
        )
    )

    reasons = [
        reason
        for reason in result.reasons
        if reason.category == "taylor"
    ]

    assert reasons == []


# ==========================================================
# Decision Boundary
# ==========================================================


@pytest.mark.parametrize(
    "score",
    [
        0.0,
        30.0,
        59.999,
    ],
)
def test_low_score_produces_caution(
    score: float,
) -> None:
    """
    Score below WATCH_THRESHOLD produces CAUTION.

    This directly tests the private production decision
    boundary without changing it.
    """

    evaluator = ComprehensiveEvaluator()

    decision = evaluator._decision(
        score=score,
        risk_level=RiskLevel.LOW,
    )

    assert (
        decision
        == ComprehensiveDecision.CAUTION
    )


@pytest.mark.parametrize(
    "score",
    [
        60.0,
        70.0,
        79.999,
    ],
)
def test_watch_score_produces_watch(
    score: float,
) -> None:
    """
    Score >= 60 and < 80 produces WATCH.
    """

    evaluator = ComprehensiveEvaluator()

    decision = evaluator._decision(
        score=score,
        risk_level=RiskLevel.LOW,
    )

    assert (
        decision
        == ComprehensiveDecision.WATCH
    )


def test_recommend_threshold_with_low_risk_produces_recommend() -> None:
    """
    Score >= 80 with LOW risk passes the recommendation gate.
    """

    evaluator = ComprehensiveEvaluator()

    decision = evaluator._decision(
        score=80.0,
        risk_level=RiskLevel.LOW,
    )

    assert (
        decision
        == ComprehensiveDecision.RECOMMEND
    )


def test_recommend_threshold_with_medium_risk_produces_recommend() -> None:
    """
    MEDIUM is also explicitly allowed by
    MAX_RECOMMEND_RISK_LEVELS.
    """

    evaluator = ComprehensiveEvaluator()

    decision = evaluator._decision(
        score=80.0,
        risk_level=RiskLevel.MEDIUM,
    )

    assert (
        decision
        == ComprehensiveDecision.RECOMMEND
    )


def test_high_risk_blocks_recommendation() -> None:
    """
    HIGH risk cannot receive RECOMMEND.
    """

    evaluator = ComprehensiveEvaluator()

    decision = evaluator._decision(
        score=100.0,
        risk_level=RiskLevel.HIGH,
    )

    assert (
        decision
        != ComprehensiveDecision.RECOMMEND
    )


def test_extreme_risk_blocks_recommendation() -> None:
    """
    EXTREME risk cannot receive RECOMMEND.
    """

    evaluator = ComprehensiveEvaluator()

    decision = evaluator._decision(
        score=100.0,
        risk_level=RiskLevel.EXTREME,
    )

    assert (
        decision
        != ComprehensiveDecision.RECOMMEND
    )


# ==========================================================
# Score Boundary
# ==========================================================


def test_total_score_is_clamped_to_zero() -> None:
    """
    Existing EvaluationComponents contract clamps total score
    to the [0, 100] range.
    """

    components = EvaluationComponents(
        valuation_score=-10.0,
        iv_score=-10.0,
        theta_score=-10.0,
        gamma_score=-10.0,
        taylor_score=-10.0,
    )

    assert (
        components.total_score
        == 0.0
    )


def test_total_score_is_clamped_to_hundred() -> None:
    """
    Existing EvaluationComponents contract clamps total score
    to 100.
    """

    components = EvaluationComponents(
        valuation_score=100.0,
        iv_score=100.0,
        theta_score=100.0,
        gamma_score=100.0,
        taylor_score=100.0,
    )

    assert (
        components.total_score
        == 100.0
    )


# ==========================================================
# Result Immutability
# ==========================================================


def test_evaluation_result_is_frozen() -> None:
    """
    ComprehensiveEvaluationResult is a frozen dataclass.
    """

    result = evaluate(
        make_result()
    )

    with pytest.raises(
        AttributeError,
    ):
        result.symbol = "CHANGED"  # type: ignore[misc]


def test_evaluation_reason_is_frozen() -> None:
    """
    EvaluationReason is a frozen dataclass.
    """

    reason = EvaluationReason(
        category="test",
        positive=True,
        message="test",
    )

    with pytest.raises(
        AttributeError,
    ):
        reason.message = "changed"  # type: ignore[misc]


# ==========================================================
# Serialization Boundary
# ==========================================================


def test_result_to_dict_preserves_reason_structure() -> None:
    """
    Existing to_dict() converts structured reasons into
    dictionaries.
    """

    result = evaluate(
        make_result()
    )

    payload = result.to_dict()

    assert isinstance(
        payload,
        dict,
    )

    assert isinstance(
        payload["reasons"],
        list,
    )

    assert payload["reasons"]

    first_reason = payload["reasons"][0]

    assert isinstance(
        first_reason,
        dict,
    )

    assert {
        "category",
        "positive",
        "message",
    }.issubset(
        first_reason.keys()
    )


def test_result_to_dict_preserves_symbol() -> None:
    """
    Symbol survives serialization.
    """

    result = evaluate(
        make_result(
            symbol="TEST-C-100"
        )
    )

    payload = result.to_dict()

    assert (
        payload["symbol"]
        == "TEST-C-100"
    )


# ==========================================================
# Convenience API
# ==========================================================


def test_evaluate_to_dict_matches_evaluate_result_contract() -> None:
    """
    Existing convenience API must return the same public
    dictionary representation as ComprehensiveEvaluationResult.
    """

    evaluator = ComprehensiveEvaluator()

    result = make_result()

    direct = evaluator.evaluate(
        result
    ).to_dict()

    convenience = evaluator.evaluate_to_dict(
        result
    )

    assert convenience == direct


# ==========================================================
# Numeric Boundary / Production Exception Ownership
# ==========================================================


@pytest.mark.parametrize(
    "attribute",
    [
        "current_option_price",
        "current_theoretical_price",
        "current_option_iv",
        "current_gamma",
        "current_theta",
        "target_theoretical_price",
        "taylor_first_order_price",
        "taylor_second_order_price",
        "current_futures_price",
    ],
)
def test_none_numeric_attribute_reaches_existing_numeric_boundary(
    attribute: str,
) -> None:
    """
    The evaluator does not invent conversions for None.

    The exact downstream exception is intentionally allowed
    to originate from the existing float() conversion path.

    This test only verifies that the evaluator does not silently
    replace None with a fabricated numeric value.
    """

    result = make_result()

    setattr(
        result,
        attribute,
        None,
    )

    evaluator = ComprehensiveEvaluator()

    with pytest.raises(
        (TypeError, ValueError, AttributeError),
    ):
        evaluator.evaluate(
            result
        )


# ==========================================================
# Negative Numeric Values
# ==========================================================


def test_negative_market_price_uses_existing_valuation_score_boundary() -> None:
    """
    Production _valuation_score() treats market_price <= 0
    as full valuation score.

    This test locks that existing behavior rather than
    introducing a new validation rule.
    """

    evaluator = ComprehensiveEvaluator()

    result = make_result(
        current_option_price=-1.0,
        current_theoretical_price=10.0,
    )

    score = evaluator._valuation_score(
        result
    )

    assert (
        score
        == evaluator.VALUATION_MAX_SCORE
    )


def test_non_positive_theoretical_price_produces_zero_valuation_score() -> None:
    """
    Production _valuation_score() returns zero when theoretical
    price <= 0, unless the market price branch has already
    returned.
    """

    evaluator = ComprehensiveEvaluator()

    result = make_result(
        current_option_price=10.0,
        current_theoretical_price=0.0,
    )

    score = evaluator._valuation_score(
        result
    )

    assert score == 0.0


def test_non_positive_taylor_target_produces_zero_taylor_score() -> None:
    """
    Existing production Taylor score boundary.
    """

    evaluator = ComprehensiveEvaluator()

    result = make_result(
        target_theoretical_price=0.0,
    )

    score = evaluator._taylor_score(
        result
    )

    assert score == 0.0


# ==========================================================
# Ordering / Determinism
# ==========================================================


def test_reason_order_is_deterministic() -> None:
    """
    The current production reason builder appends reasons in
    deterministic category order.
    """

    result = evaluate(
        make_result()
    )

    categories = [
        reason.category
        for reason in result.reasons
    ]

    assert categories == [
        "valuation",
        "iv",
        "theta",
        "gamma",
        "taylor",
        "risk",
    ]


def test_repeated_evaluation_produces_same_reason_order() -> None:
    """
    Repeated evaluation must not reorder reason categories.
    """

    evaluator = ComprehensiveEvaluator()

    first = evaluator.evaluate(
        make_result()
    )

    second = evaluator.evaluate(
        make_result()
    )

    assert (
        first.reasons
        == second.reasons
    )


# ==========================================================
# Existing Public API Stability
# ==========================================================


def test_public_exports_remain_available() -> None:
    """
    Existing public evaluation types remain constructible.
    """

    assert ComprehensiveDecision.RECOMMEND.value == "RECOMMEND"
    assert ComprehensiveDecision.WATCH.value == "WATCH"
    assert ComprehensiveDecision.CAUTION.value == "CAUTION"

    reason = EvaluationReason(
        category="test",
        positive=True,
        message="test",
    )

    assert reason.category == "test"


def test_reason_text_preserves_reason_order() -> None:
    """
    reason_text must follow the same ordering as reasons.
    """

    result = evaluate(
        make_result()
    )

    lines = result.reason_text.splitlines()

    assert len(lines) == len(
        result.reasons
    )

    for line, reason in zip(
        lines,
        result.reasons,
    ):
        assert reason.message in line