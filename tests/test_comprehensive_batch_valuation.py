"""
Commodity Option Valuator Pro
=============================

Comprehensive Batch Valuation Tests.

Commit 0028
------------

Purpose
-------
Verify that the existing scanner batch valuation workflow
automatically carries the comprehensive evaluation result
produced by SingleOptionValuator.

Architecture
------------

OptionQuote
    ↓
ScannerValuationBridge
    ↓
ScannerBatchValuator
    ↓
SingleOptionValuator
    ↓
SingleOptionValuationResult
    ↓
ComprehensiveEvaluator
    ↓
ComprehensiveEvaluationResult

Important
---------
This test module intentionally does NOT introduce a new
batch comprehensive evaluator.

The production architecture already provides the correct
composition through SingleOptionValuator.

This module only locks the integration contract.

It does not modify:

- ScannerBatchValuator
- SingleOptionValuator
- ComprehensiveEvaluator
- RecommendationEngine
- RiskAnalyzer
- BlackScholes
- Greeks
- TaylorValuator
"""

from __future__ import annotations

import math

from core.comprehensive_evaluation import (
    ComprehensiveDecision,
    ComprehensiveEvaluationResult,
)
from core.scanner_batch_valuation import (
    BatchValuationParameters,
    ScannerBatchValuator,
)
from core.single_option_valuation import (
    ReferenceVolatilityScenario,
)
from data.option_chain import (
    OptionQuote,
)


# ==========================================================
# Test Data Helpers
# ==========================================================


def make_quote(
    *,
    symbol: str,
    underlying: str,
    option_type: str,
    strike: float,
    last_price: float,
    volume: int,
    implied_volatility: float,
) -> OptionQuote:
    """
    Build an OptionQuote without depending on its constructor
    signature.

    The test focuses on the valuation integration rather than
    the OptionQuote constructor implementation.
    """

    quote = object.__new__(
        OptionQuote
    )

    object.__setattr__(
        quote,
        "symbol",
        symbol,
    )

    object.__setattr__(
        quote,
        "underlying",
        underlying,
    )

    object.__setattr__(
        quote,
        "option_type",
        option_type,
    )

    object.__setattr__(
        quote,
        "strike",
        strike,
    )

    object.__setattr__(
        quote,
        "last_price",
        last_price,
    )

    object.__setattr__(
        quote,
        "volume",
        volume,
    )

    object.__setattr__(
        quote,
        "open_interest",
        1000,
    )

    object.__setattr__(
        quote,
        "implied_volatility",
        implied_volatility,
    )

    return quote


def make_quotes() -> list[OptionQuote]:
    """
    Create a small deterministic option chain.

    One CALL and one PUT are provided so that the test covers
    both option types.
    """

    return [
        make_quote(
            symbol="AU2608-C-968",
            underlying="AU2608",
            option_type="CALL",
            strike=968.0,
            last_price=15.0,
            volume=5000,
            implied_volatility=0.1954,
        ),
        make_quote(
            symbol="AU2608-P-968",
            underlying="AU2608",
            option_type="PUT",
            strike=968.0,
            last_price=14.0,
            volume=4000,
            implied_volatility=0.2000,
        ),
    ]


def make_parameters() -> BatchValuationParameters:
    """
    Create deterministic batch valuation parameters.
    """

    return BatchValuationParameters(
        current_futures_prices={
            "AU2608": 900.0,
        },
        target_futures_prices={
            "AU2608": 1000.0,
        },
        remaining_days={
            "AU2608": 30,
        },
        reference_volatility={
            "AU2608": ReferenceVolatilityScenario(
                current=26.70,
                target=29.55,
            ),
        },
    )


def make_batch_result():
    """
    Execute the real production batch valuation workflow.
    """

    valuator = ScannerBatchValuator()

    return valuator.scan_and_evaluate(
        make_quotes(),
        top_n=1,
        parameters=make_parameters(),
    )


# ==========================================================
# Integration Contract
# ==========================================================


def test_batch_valuation_produces_comprehensive_evaluation():
    """
    Every successfully valued scanner option must contain a
    ComprehensiveEvaluationResult.

    This is the primary Commit 0028 integration contract.
    """

    result = make_batch_result()

    assert result.count == 2

    for item in result.items:

        comprehensive = (
            item.result.comprehensive_evaluation
        )

        assert isinstance(
            comprehensive,
            ComprehensiveEvaluationResult,
        )


def test_batch_comprehensive_evaluation_preserves_symbol():
    """
    Comprehensive evaluation must preserve the symbol of the
    original scanner candidate.
    """

    result = make_batch_result()

    for item in result.items:

        comprehensive = (
            item.result.comprehensive_evaluation
        )

        assert comprehensive is not None

        assert (
            comprehensive.symbol
            ==
            item.symbol
        )


def test_batch_comprehensive_evaluation_contains_valid_score():
    """
    Comprehensive score must remain within the documented
    0 - 100 range.
    """

    result = make_batch_result()

    for item in result.items:

        comprehensive = (
            item.result.comprehensive_evaluation
        )

        assert comprehensive is not None

        assert isinstance(
            comprehensive.score,
            float,
        )

        assert math.isfinite(
            comprehensive.score
        )

        assert (
            0.0
            <= comprehensive.score
            <= 100.0
        )


def test_batch_comprehensive_evaluation_contains_valid_decision():
    """
    Comprehensive evaluation must produce one of the
    established business decisions.
    """

    result = make_batch_result()

    valid_decisions = {
        ComprehensiveDecision.RECOMMEND,
        ComprehensiveDecision.WATCH,
        ComprehensiveDecision.CAUTION,
    }

    for item in result.items:

        comprehensive = (
            item.result.comprehensive_evaluation
        )

        assert comprehensive is not None

        assert (
            comprehensive.decision
            in valid_decisions
        )


def test_batch_comprehensive_evaluation_contains_risk_information():
    """
    Comprehensive evaluation must preserve risk score and
    risk level.
    """

    result = make_batch_result()

    for item in result.items:

        comprehensive = (
            item.result.comprehensive_evaluation
        )

        assert comprehensive is not None

        assert isinstance(
            comprehensive.risk_score,
            float,
        )

        assert math.isfinite(
            comprehensive.risk_score
        )

        assert comprehensive.risk_level is not None


def test_batch_comprehensive_evaluation_contains_all_components():
    """
    The comprehensive result must contain all five scoring
    components:

    - valuation
    - IV
    - theta
    - gamma
    - Taylor
    """

    result = make_batch_result()

    for item in result.items:

        comprehensive = (
            item.result.comprehensive_evaluation
        )

        assert comprehensive is not None

        components = (
            comprehensive.components
        )

        assert math.isfinite(
            components.valuation_score
        )

        assert math.isfinite(
            components.iv_score
        )

        assert math.isfinite(
            components.theta_score
        )

        assert math.isfinite(
            components.gamma_score
        )

        assert math.isfinite(
            components.taylor_score
        )

        assert (
            components.total_score
            ==
            comprehensive.score
        )


def test_batch_comprehensive_evaluation_contains_reasons():
    """
    Every comprehensive evaluation must provide at least one
    deterministic human-readable reason.
    """

    result = make_batch_result()

    for item in result.items:

        comprehensive = (
            item.result.comprehensive_evaluation
        )

        assert comprehensive is not None

        assert len(
            comprehensive.reasons
        ) > 0

        assert (
            comprehensive.reason_text.strip()
            != ""
        )

        assert all(
            reason.message.strip()
            != ""
            for reason
            in comprehensive.reasons
        )


def test_batch_comprehensive_evaluation_reason_messages_are_available():
    """
    The convenience reason_messages property must remain
    usable by future scanner/UI layers.
    """

    result = make_batch_result()

    for item in result.items:

        comprehensive = (
            item.result.comprehensive_evaluation
        )

        assert comprehensive is not None

        messages = (
            comprehensive.reason_messages
        )

        assert isinstance(
            messages,
            tuple,
        )

        assert len(messages) > 0

        assert all(
            isinstance(
                message,
                str,
            )
            and message.strip()
            != ""
            for message
            in messages
        )


def test_batch_result_to_dict_contains_comprehensive_evaluation():
    """
    Batch export must expose the comprehensive evaluation.

    This is important because the future Scanner UI and report
    layer will consume BatchValuationResult.to_dict().
    """

    result = make_batch_result()

    data = result.to_dict()

    assert len(data) == 2

    for item in data:

        assert (
            "comprehensive_evaluation"
            in item
        )

        comprehensive = item[
            "comprehensive_evaluation"
        ]

        assert isinstance(
            comprehensive,
            dict,
        )

        assert (
            "symbol"
            in comprehensive
        )

        assert (
            "decision"
            in comprehensive
        )

        assert (
            "score"
            in comprehensive
        )

        assert (
            "risk_score"
            in comprehensive
        )

        assert (
            "risk_level"
            in comprehensive
        )

        assert (
            "components"
            in comprehensive
        )

        assert (
            "reasons"
            in comprehensive
        )


def test_call_and_put_both_receive_comprehensive_evaluation():
    """
    Both CALL and PUT scanner candidates must pass through the
    same comprehensive evaluation workflow.
    """

    result = make_batch_result()

    call_item = next(
        item
        for item in result.items
        if item.option_type == "CALL"
    )

    put_item = next(
        item
        for item in result.items
        if item.option_type == "PUT"
    )

    assert (
        call_item.result.comprehensive_evaluation
        is not None
    )

    assert (
        put_item.result.comprehensive_evaluation
        is not None
    )


def test_comprehensive_evaluation_is_generated_by_real_batch_workflow():
    """
    Integration-level contract.

    The comprehensive result must not be manually injected by
    the test. It must be produced by:

        ScannerBatchValuator
            ↓
        SingleOptionValuator
            ↓
        ComprehensiveEvaluator
    """

    result = make_batch_result()

    for item in result.items:

        valuation_result = item.result

        comprehensive = (
            valuation_result.comprehensive_evaluation
        )

        assert comprehensive is not None

        assert (
            comprehensive.symbol
            ==
            valuation_result.symbol
        )

        assert (
            comprehensive.score
            ==
            comprehensive.components.total_score
        )


# ==========================================================
# Public API Contract
# ==========================================================


def test_comprehensive_batch_public_imports():
    """
    Verify that the production public interfaces required by
    Commit 0028 remain importable.
    """

    from core.comprehensive_evaluation import (
        ComprehensiveDecision,
        ComprehensiveEvaluationResult,
        ComprehensiveEvaluator,
    )

    from core.scanner_batch_valuation import (
        BatchValuationItem,
        BatchValuationParameters,
        BatchValuationResult,
        ScannerBatchValuator,
    )

    from core.single_option_valuation import (
        SingleOptionValuationInput,
        SingleOptionValuationResult,
        SingleOptionValuator,
    )

    assert ComprehensiveDecision is not None
    assert ComprehensiveEvaluationResult is not None
    assert ComprehensiveEvaluator is not None

    assert BatchValuationItem is not None
    assert BatchValuationParameters is not None
    assert BatchValuationResult is not None
    assert ScannerBatchValuator is not None

    assert SingleOptionValuationInput is not None
    assert SingleOptionValuationResult is not None
    assert SingleOptionValuator is not None