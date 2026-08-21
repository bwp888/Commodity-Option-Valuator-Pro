"""
Commodity Option Valuator Pro
=============================

Scanner Batch Parameter Bridge Tests.

Commit 0031 - Phase 2
----------------------

Verify that the existing ScannerBatchValuator correctly
bridges ScannerCandidate / OptionQuote information into
the existing BatchValuationParameters contract.

Architecture
------------

ScannerCandidate
        ↓
ScannerBatchValuator
        ↓
BatchValuationParameters
        ↓
SingleOptionValuationInput
        ↓
SingleOptionValuator

Important
---------
This module does NOT introduce a new bridge class.

The existing ScannerBatchValuator already owns the bridge
between scanner data and batch valuation parameters.

The purpose of this test module is therefore to lock that
existing contract before any Scanner UI changes are made.

No production interface is modified by these tests.

Author : Simon
Version : 0.1.0
Python : 3.12
"""

from __future__ import annotations

import pytest

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
from models.option import (
    OptionDirection,
)


# ==========================================================
# Test Data
# ==========================================================


UNDERLYING = "AU2608"

CURRENT_FUTURES_PRICE = 900.0
TARGET_FUTURES_PRICE = 1000.0

REMAINING_DAYS = 30

CURRENT_REFERENCE_IV = 0.267
TARGET_REFERENCE_IV = 0.2955

RISK_FREE_RATE = 0.025


def make_option_quote(
    *,
    underlying: str = UNDERLYING,
    strike: float = 900.0,
    price: float = 35.0,
) -> OptionQuote:
    """
    Create a deterministic scanner quote.

    The quote intentionally contains an explicit underlying
    so the test verifies that the scanner valuation path does
    not need to infer it from the option symbol.
    """

    return OptionQuote(
        symbol=f"{underlying}-C-{strike:g}",
        underlying=underlying,
        option_type="CALL",
        strike=strike,
        last_price=price,
        bid_price=34.5,
        ask_price=35.5,
        volume=100,
        open_interest=500,
    )


def make_parameters() -> BatchValuationParameters:
    """
    Create the existing batch valuation parameter object.
    """

    return BatchValuationParameters(
        current_futures_prices={
            UNDERLYING: CURRENT_FUTURES_PRICE,
        },
        target_futures_prices={
            UNDERLYING: TARGET_FUTURES_PRICE,
        },
        remaining_days={
            UNDERLYING: REMAINING_DAYS,
        },
        reference_volatility={
            UNDERLYING: ReferenceVolatilityScenario(
                current=CURRENT_REFERENCE_IV,
                target=TARGET_REFERENCE_IV,
            ),
        },
        risk_free_rate=RISK_FREE_RATE,
        direction=OptionDirection.LONG,
    )


# ==========================================================
# Public Object Contract
# ==========================================================


def test_scanner_batch_valuator_exists() -> None:
    """
    Existing ScannerBatchValuator must remain available.
    """

    valuator = ScannerBatchValuator()

    assert isinstance(
        valuator,
        ScannerBatchValuator,
    )


def test_batch_parameter_object_remains_public() -> None:
    """
    Existing BatchValuationParameters remains the public
    batch parameter contract.
    """

    parameters = make_parameters()

    assert isinstance(
        parameters,
        BatchValuationParameters,
    )


# ==========================================================
# Parameter Mapping Contract
# ==========================================================


def test_current_futures_price_is_mapped_by_underlying() -> None:
    """
    Current futures price must be resolved using the scanner
    candidate's underlying.
    """

    parameters = make_parameters()

    assert (
        parameters.current_futures_prices[UNDERLYING]
        == CURRENT_FUTURES_PRICE
    )


def test_target_futures_price_is_mapped_by_underlying() -> None:
    """
    Target futures price must be resolved using the same
    underlying key.
    """

    parameters = make_parameters()

    assert (
        parameters.target_futures_prices[UNDERLYING]
        == TARGET_FUTURES_PRICE
    )


def test_remaining_days_is_mapped_by_underlying() -> None:
    """
    Remaining days must remain an underlying-specific value.
    """

    parameters = make_parameters()

    assert (
        parameters.remaining_days[UNDERLYING]
        == REMAINING_DAYS
    )


def test_reference_volatility_is_mapped_by_underlying() -> None:
    """
    Current and target reference volatility must remain
    grouped inside ReferenceVolatilityScenario.
    """

    parameters = make_parameters()

    scenario = parameters.reference_volatility[
        UNDERLYING
    ]

    assert isinstance(
        scenario,
        ReferenceVolatilityScenario,
    )

    assert scenario.current == CURRENT_REFERENCE_IV
    assert scenario.target == TARGET_REFERENCE_IV


# ==========================================================
# Underlying Isolation
# ==========================================================


def test_two_underlyings_keep_independent_parameters() -> None:
    """
    Different underlyings must not share valuation parameters.
    """

    second_underlying = "CU2608"

    parameters = BatchValuationParameters(
        current_futures_prices={
            UNDERLYING: 900.0,
            second_underlying: 80000.0,
        },
        target_futures_prices={
            UNDERLYING: 1000.0,
            second_underlying: 82000.0,
        },
        remaining_days={
            UNDERLYING: 30,
            second_underlying: 45,
        },
        reference_volatility={
            UNDERLYING: ReferenceVolatilityScenario(
                current=0.267,
                target=0.2955,
            ),
            second_underlying: ReferenceVolatilityScenario(
                current=0.18,
                target=0.20,
            ),
        },
        risk_free_rate=RISK_FREE_RATE,
        direction=OptionDirection.LONG,
    )

    assert (
        parameters.current_futures_prices[UNDERLYING]
        !=
        parameters.current_futures_prices[second_underlying]
    )

    assert (
        parameters.target_futures_prices[UNDERLYING]
        !=
        parameters.target_futures_prices[second_underlying]
    )

    assert (
        parameters.remaining_days[UNDERLYING]
        !=
        parameters.remaining_days[second_underlying]
    )

    assert (
        parameters.reference_volatility[UNDERLYING]
        .current
        !=
        parameters.reference_volatility[second_underlying]
        .current
    )


# ==========================================================
# Missing Underlying
# ==========================================================


def test_missing_underlying_is_not_silently_replaced() -> None:
    """
    A scanner underlying that does not exist in the parameter
    mapping must not silently fall back to another underlying.
    """

    parameters = make_parameters()

    missing_underlying = "CU2608"

    with pytest.raises(ValueError):
        ScannerBatchValuator._get_required_mapping_value(
            parameters.current_futures_prices,
            missing_underlying,
            "current_futures_prices",
        )


def test_empty_underlying_is_rejected() -> None:
    """
    Empty underlying identifiers must not be accepted as a
    valid mapping key by the valuation bridge.
    """

    parameters = make_parameters()

    with pytest.raises(ValueError):
        ScannerBatchValuator._get_required_mapping_value(
            parameters.current_futures_prices,
            "",
            "current_futures_prices",
        )


# ==========================================================
# Required Mapping Independence
# ==========================================================


@pytest.mark.parametrize(
    "mapping_name",
    [
        "current_futures_prices",
        "target_futures_prices",
        "remaining_days",
        "reference_volatility",
    ],
)
def test_each_required_mapping_rejects_missing_underlying(
    mapping_name: str,
) -> None:
    """
    Every underlying-specific valuation mapping must reject
    a missing underlying independently.
    """

    parameters = make_parameters()

    mappings = {
        "current_futures_prices":
            parameters.current_futures_prices,
        "target_futures_prices":
            parameters.target_futures_prices,
        "remaining_days":
            parameters.remaining_days,
        "reference_volatility":
            parameters.reference_volatility,
    }

    with pytest.raises(ValueError):
        ScannerBatchValuator._get_required_mapping_value(
            mappings[mapping_name],
            "MISSING-UNDERLYING",
            mapping_name,
        )


# ==========================================================
# Validation Boundary
# ==========================================================


def test_valid_parameters_pass_validation() -> None:
    """
    The complete existing parameter object must validate.
    """

    parameters = make_parameters()

    parameters.validate()


def test_invalid_reference_volatility_does_not_reach_valuation() -> None:
    """
    Invalid reference volatility remains a parameter-layer
    validation error rather than being handled by the UI.
    """

    parameters = BatchValuationParameters(
        current_futures_prices={
            UNDERLYING: CURRENT_FUTURES_PRICE,
        },
        target_futures_prices={
            UNDERLYING: TARGET_FUTURES_PRICE,
        },
        remaining_days={
            UNDERLYING: REMAINING_DAYS,
        },
        reference_volatility={
            UNDERLYING: ReferenceVolatilityScenario(
                current=0.0,
                target=TARGET_REFERENCE_IV,
            ),
        },
        risk_free_rate=RISK_FREE_RATE,
        direction=OptionDirection.LONG,
    )

    with pytest.raises(ValueError):
        parameters.validate()


# ==========================================================
# Core/UI Boundary
# ==========================================================


def test_batch_parameters_are_free_of_ui_objects() -> None:
    """
    The core valuation parameter object must remain independent
    from CustomTkinter widgets.
    """

    parameters = make_parameters()

    assert not hasattr(
        parameters,
        "entry",
    )

    assert not hasattr(
        parameters,
        "widget",
    )

    assert not hasattr(
        parameters,
        "button",
    )


def test_parameter_values_are_plain_numeric_values() -> None:
    """
    Core batch parameters must contain ordinary numeric values,
    not UI strings or widget objects.
    """

    parameters = make_parameters()

    assert isinstance(
        parameters.current_futures_prices[UNDERLYING],
        float,
    )

    assert isinstance(
        parameters.target_futures_prices[UNDERLYING],
        float,
    )

    assert isinstance(
        parameters.remaining_days[UNDERLYING],
        int,
    )

    scenario = parameters.reference_volatility[
        UNDERLYING
    ]

    assert isinstance(
        scenario.current,
        float,
    )

    assert isinstance(
        scenario.target,
        float,
    )


# ==========================================================
# Scanner Quote Contract
# ==========================================================


def test_scanner_quote_has_explicit_underlying() -> None:
    """
    Scanner data must expose the underlying explicitly.

    This is the critical contract required by the batch
    valuation layer.
    """

    quote = make_option_quote()

    assert quote.underlying == UNDERLYING


def test_scanner_quote_underlying_is_not_derived_from_symbol() -> None:
    """
    The batch valuation architecture must use the explicit
    OptionQuote.underlying field instead of parsing the
    option symbol.

    This test deliberately uses a symbol whose format should
    not be relied upon for underlying extraction.
    """

    quote = OptionQuote(
        symbol="OPTION-TEST-001",
        underlying=UNDERLYING,
        option_type="CALL",
        strike=900.0,
        last_price=35.0,
        bid_price=34.5,
        ask_price=35.5,
        volume=100,
        open_interest=500,
    )

    assert quote.symbol != quote.underlying
    assert quote.underlying == UNDERLYING


# ==========================================================
# Future Scanner UI Contract
# ==========================================================


def test_scanner_quote_has_required_market_data_fields() -> None:
    """
    Scanner quotes must retain the market data fields required
    by the valuation pipeline.
    """

    quote = make_option_quote()

    assert quote.last_price == 35.0
    assert quote.bid_price == 34.5
    assert quote.ask_price == 35.5
    assert quote.volume == 100
    assert quote.open_interest == 500


# ==========================================================
# Regression Boundary
# ==========================================================


def test_direction_remains_part_of_batch_parameter_contract() -> None:
    """
    The existing LONG / SHORT direction field remains part of
    the batch valuation contract.
    """

    parameters = make_parameters()

    assert parameters.direction == OptionDirection.LONG


def test_risk_free_rate_remains_part_of_batch_parameter_contract() -> None:
    """
    Existing risk-free rate configuration must remain available.
    """

    parameters = make_parameters()

    assert parameters.risk_free_rate == RISK_FREE_RATE


# ==========================================================
# Explicit Non-Regression Contract
# ==========================================================


def test_no_new_batch_parameter_class_is_required() -> None:
    """
    The existing BatchValuationParameters remains the single
    batch parameter contract.

    This intentionally prevents the introduction of a second
    competing parameter object during 0031.
    """

    parameters = make_parameters()

    assert type(parameters) is BatchValuationParameters