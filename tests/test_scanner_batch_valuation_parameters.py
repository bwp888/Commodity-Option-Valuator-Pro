"""
Commodity Option Valuator Pro
=============================

Scanner Batch Valuation Parameter Contract Tests.

Commit 0031 - Phase 1
----------------------

Verify the existing BatchValuationParameters contract before
connecting the scanner UI parameter controls to the real
OptionQuote / underlying data pipeline.

Important
---------
This test module does not introduce a new valuation interface.

It verifies the existing public interface:

    BatchValuationParameters
        ↓
    validate()
        ↓
    ScannerBatchValuator

The test intentionally keeps the current architecture unchanged.
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
from models.option import (
    OptionDirection,
)


# ==========================================================
# Fixtures
# ==========================================================


UNDERLYING = "AU2608"


def make_parameters(
    *,
    current_futures_price: float = 900.0,
    target_futures_price: float = 1000.0,
    remaining_days: int = 30,
    reference_current: float = 26.70,
    reference_target: float = 29.55,
    risk_free_rate: float = 0.025,
    direction: OptionDirection | str = OptionDirection.LONG,
) -> BatchValuationParameters:
    """
    Build a deterministic BatchValuationParameters instance.
    """

    return BatchValuationParameters(
        current_futures_prices={
            UNDERLYING: current_futures_price,
        },
        target_futures_prices={
            UNDERLYING: target_futures_price,
        },
        remaining_days={
            UNDERLYING: remaining_days,
        },
        reference_volatility={
            UNDERLYING: ReferenceVolatilityScenario(
                current=reference_current,
                target=reference_target,
            ),
        },
        risk_free_rate=risk_free_rate,
        direction=direction,
    )


# ==========================================================
# Public Contract
# ==========================================================


def test_batch_valuation_parameters_can_be_created() -> None:
    """
    Existing BatchValuationParameters must remain constructible.
    """

    parameters = make_parameters()

    assert isinstance(
        parameters,
        BatchValuationParameters,
    )


def test_batch_valuation_parameters_validate_valid_values() -> None:
    """
    Valid batch parameters must pass validation.
    """

    parameters = make_parameters()

    parameters.validate()


def test_default_risk_free_rate_is_preserved() -> None:
    """
    The existing internal risk-free rate default must remain
    0.025.
    """

    parameters = BatchValuationParameters(
        current_futures_prices={
            UNDERLYING: 900.0,
        },
        target_futures_prices={
            UNDERLYING: 1000.0,
        },
        remaining_days={
            UNDERLYING: 30,
        },
        reference_volatility={
            UNDERLYING: ReferenceVolatilityScenario(
                current=26.70,
                target=29.55,
            ),
        },
    )

    assert parameters.risk_free_rate == 0.025


# ==========================================================
# Futures Price Validation
# ==========================================================


def test_negative_risk_free_rate_is_rejected() -> None:
    """
    Existing BatchValuationParameters contract must reject
    a negative risk-free rate.
    """

    parameters = make_parameters(
        risk_free_rate=-0.001,
    )

    with pytest.raises(ValueError):
        parameters.validate()


def test_missing_current_futures_price_is_detected_by_batch_valuator() -> None:
    """
    ScannerBatchValuator must preserve the existing mapping
    contract and reject a missing underlying.
    """

    parameters = BatchValuationParameters(
        current_futures_prices={},
        target_futures_prices={
            UNDERLYING: 1000.0,
        },
        remaining_days={
            UNDERLYING: 30,
        },
        reference_volatility={
            UNDERLYING: ReferenceVolatilityScenario(
                current=26.70,
                target=29.55,
            ),
        },
    )

    parameters.validate()

    valuator = ScannerBatchValuator()

    # The parameter object itself validates mapping structure,
    # while the valuation workflow resolves the required
    # underlying-specific value.
    with pytest.raises(ValueError):
        valuator._get_required_mapping_value(
            parameters.current_futures_prices,
            UNDERLYING,
            "current_futures_prices",
        )


# ==========================================================
# Remaining Days
# ==========================================================


def test_zero_remaining_days_is_not_rejected_by_parameter_layer() -> None:
    """
    BatchValuationParameters currently validates mapping
    structure rather than option-level numerical maturity.

    The actual SingleOptionValuationInput contract is responsible
    for requiring remaining_days > 0.

    This test documents that boundary rather than inventing a
    new validation rule inside BatchValuationParameters.
    """

    parameters = make_parameters(
        remaining_days=0,
    )

    parameters.validate()

    assert parameters.remaining_days[UNDERLYING] == 0


# ==========================================================
# Reference Volatility
# ==========================================================


def test_reference_volatility_is_required_to_be_scenario_object() -> None:
    """
    The existing public contract requires
    ReferenceVolatilityScenario values.
    """

    parameters = BatchValuationParameters(
        current_futures_prices={
            UNDERLYING: 900.0,
        },
        target_futures_prices={
            UNDERLYING: 1000.0,
        },
        remaining_days={
            UNDERLYING: 30,
        },
        reference_volatility={
            UNDERLYING: object(),
        },
    )

    with pytest.raises(TypeError):
        parameters.validate()


def test_reference_volatility_values_must_be_positive() -> None:
    """
    Reference volatility validation remains delegated to the
    existing ReferenceVolatilityScenario.
    """

    parameters = make_parameters(
        reference_current=0.0,
    )

    with pytest.raises(ValueError):
        parameters.validate()


def test_reference_target_volatility_must_be_positive() -> None:
    """
    Target reference volatility must remain positive.
    """

    parameters = make_parameters(
        reference_target=0.0,
    )

    with pytest.raises(ValueError):
        parameters.validate()


# ==========================================================
# Direction
# ==========================================================


@pytest.mark.parametrize(
    "direction",
    [
        OptionDirection.LONG,
        OptionDirection.SHORT,
        "LONG",
        "SHORT",
        "long",
        "short",
    ],
)
def test_valid_direction_values_are_preserved(
    direction: OptionDirection | str,
) -> None:
    """
    Existing LONG / SHORT direction contract must remain
    compatible with both enum and string values.
    """

    parameters = make_parameters(
        direction=direction,
    )

    parameters.validate()


def test_invalid_direction_is_rejected() -> None:
    """
    Invalid direction values must be rejected by the existing
    parameter contract.
    """

    parameters = make_parameters(
        direction="CALL",
    )

    with pytest.raises(ValueError):
        parameters.validate()


# ==========================================================
# Multiple Underlyings
# ==========================================================


def test_multiple_underlyings_are_supported() -> None:
    """
    BatchValuationParameters must support the existing mapping
    design for more than one underlying.

    This is important for the future Scanner UI because the
    scanner can contain multiple futures option series.
    """

    parameters = BatchValuationParameters(
        current_futures_prices={
            "AU2608": 900.0,
            "CU2608": 80000.0,
        },
        target_futures_prices={
            "AU2608": 1000.0,
            "CU2608": 82000.0,
        },
        remaining_days={
            "AU2608": 30,
            "CU2608": 45,
        },
        reference_volatility={
            "AU2608": ReferenceVolatilityScenario(
                current=26.70,
                target=29.55,
            ),
            "CU2608": ReferenceVolatilityScenario(
                current=18.0,
                target=20.0,
            ),
        },
    )

    parameters.validate()

    assert set(
        parameters.current_futures_prices
    ) == {
        "AU2608",
        "CU2608",
    }

    assert set(
        parameters.target_futures_prices
    ) == {
        "AU2608",
        "CU2608",
    }

    assert set(
        parameters.remaining_days
    ) == {
        "AU2608",
        "CU2608",
    }

    assert set(
        parameters.reference_volatility
    ) == {
        "AU2608",
        "CU2608",
    }


# ==========================================================
# Empty Underlying Key
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
def test_empty_underlying_key_is_rejected(
    mapping_name: str,
) -> None:
    """
    Existing mapping validation must reject an empty underlying.
    """

    parameters = BatchValuationParameters(
        current_futures_prices={
            UNDERLYING: 900.0,
        },
        target_futures_prices={
            UNDERLYING: 1000.0,
        },
        remaining_days={
            UNDERLYING: 30,
        },
        reference_volatility={
            UNDERLYING: ReferenceVolatilityScenario(
                current=26.70,
                target=29.55,
            ),
        },
    )

    mappings = {
        "current_futures_prices": parameters.current_futures_prices,
        "target_futures_prices": parameters.target_futures_prices,
        "remaining_days": parameters.remaining_days,
        "reference_volatility": parameters.reference_volatility,
    }

    mappings[mapping_name][""] = (
        mappings[mapping_name][UNDERLYING]
    )

    with pytest.raises(ValueError):
        parameters.validate()


# ==========================================================
# Immutability
# ==========================================================


def test_batch_parameters_are_frozen() -> None:
    """
    BatchValuationParameters remains an immutable dataclass.
    """

    parameters = make_parameters()

    with pytest.raises(AttributeError):
        parameters.risk_free_rate = 0.03  # type: ignore[misc]


# ==========================================================
# Future UI Boundary
# ==========================================================


def test_parameter_contract_does_not_expose_ui_specific_fields() -> None:
    """
    The core parameter object must remain independent from
    CustomTkinter/UI implementation details.

    This intentionally prevents the UI layer from leaking
    widgets or strings into the core valuation contract.
    """

    parameters = make_parameters()

    assert hasattr(
        parameters,
        "current_futures_prices",
    )

    assert hasattr(
        parameters,
        "target_futures_prices",
    )

    assert hasattr(
        parameters,
        "remaining_days",
    )

    assert hasattr(
        parameters,
        "reference_volatility",
    )

    assert not hasattr(
        parameters,
        "entry",
    )

    assert not hasattr(
        parameters,
        "widget",
    )