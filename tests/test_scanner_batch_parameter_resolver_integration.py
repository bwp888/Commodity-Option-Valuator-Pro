"""
Commodity Option Valuator Pro
=============================

Scanner Batch Parameter Resolver Integration Tests.

Commit 0032 - Phase 2
----------------------

Verify that the scanner batch valuation workflow can use the
existing ScannerBatchParameterResolver as the parameter
coverage boundary.

Architecture
------------

OptionQuote
    ↓
ScannerBatchValuator
    ↓
ScannerBatchParameterResolver
    ↓
BatchValuationParameters
    ↓
SingleOptionValuationInput
    ↓
SingleOptionValuator

Important
---------
This test module does not introduce a new valuation interface.

It verifies the intended integration boundary before modifying
ScannerBatchValuator production execution.

The resolver must remain responsible for:

- discovering required underlyings;
- checking parameter coverage;
- rejecting incomplete parameter sets.

The batch valuator remains responsible for:

- selecting candidates;
- creating valuation inputs;
- executing SingleOptionValuator;
- returning BatchValuationResult.

No pricing calculation is implemented here.

Author : Simon
Version : 0.1.0
Python : 3.12
"""

from __future__ import annotations

import pytest

from core.scanner_batch_parameter_resolver import (
    ScannerBatchParameterCoverage,
    ScannerBatchParameterResolver,
)
from core.scanner_batch_valuation import (
    BatchValuationParameters,
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
# Test Constants
# ==========================================================


AU = "AU2608"
CU = "CU2608"

RISK_FREE_RATE = 0.025


# ==========================================================
# Fixtures
# ==========================================================


def make_quote(
    *,
    underlying: str = AU,
    symbol: str = "AU2608-C-900",
    strike: float = 900.0,
    last_price: float = 35.0,
    volume: int = 100,
) -> OptionQuote:
    """
    Create a deterministic OptionQuote.

    The underlying is supplied explicitly and is never derived
    from the option symbol.
    """

    return OptionQuote(
        symbol=symbol,
        underlying=underlying,
        option_type="CALL",
        strike=strike,
        last_price=last_price,
        bid_price=34.5,
        ask_price=35.5,
        volume=volume,
        open_interest=500,
    )


def make_parameters(
    *,
    include_current: bool = True,
    include_target: bool = True,
    include_remaining_days: bool = True,
    include_reference_volatility: bool = True,
    underlying: str = AU,
) -> BatchValuationParameters:
    """
    Build deterministic batch valuation parameters.

    Individual mappings can deliberately omit one required
    parameter so the resolver boundary can be tested.
    """

    current_futures_prices: dict[str, float] = {}

    target_futures_prices: dict[str, float] = {}

    remaining_days: dict[str, int] = {}

    reference_volatility: dict[
        str,
        ReferenceVolatilityScenario,
    ] = {}

    if include_current:
        current_futures_prices[
            underlying
        ] = 900.0

    if include_target:
        target_futures_prices[
            underlying
        ] = 1000.0

    if include_remaining_days:
        remaining_days[
            underlying
        ] = 30

    if include_reference_volatility:
        reference_volatility[
            underlying
        ] = ReferenceVolatilityScenario(
            current=0.267,
            target=0.2955,
        )

    return BatchValuationParameters(
        current_futures_prices=current_futures_prices,
        target_futures_prices=target_futures_prices,
        remaining_days=remaining_days,
        reference_volatility=reference_volatility,
        risk_free_rate=RISK_FREE_RATE,
        direction=OptionDirection.LONG,
    )


# ==========================================================
# Coverage Boundary
# ==========================================================


def test_complete_quote_parameters_are_complete() -> None:
    """
    A scanner quote with all required underlying-level
    parameters must produce complete coverage.
    """

    quote = make_quote()

    parameters = make_parameters()

    coverage = ScannerBatchParameterResolver.inspect(
        [quote],
        parameters,
    )

    assert isinstance(
        coverage,
        ScannerBatchParameterCoverage,
    )

    assert coverage.required_underlyings == (
        AU,
    )

    assert coverage.is_complete is True

    assert coverage.missing_underlyings == ()


def test_missing_current_futures_price_is_detected() -> None:
    """
    Missing current futures price must be detected before
    valuation.
    """

    quote = make_quote()

    parameters = make_parameters(
        include_current=False,
    )

    coverage = ScannerBatchParameterResolver.inspect(
        [quote],
        parameters,
    )

    assert coverage.is_complete is False

    assert coverage.missing_current_futures_prices == (
        AU,
    )

    assert coverage.missing_underlyings == (
        AU,
    )


def test_missing_target_futures_price_is_detected() -> None:
    """
    Missing target futures price must be detected before
    valuation.
    """

    quote = make_quote()

    parameters = make_parameters(
        include_target=False,
    )

    coverage = ScannerBatchParameterResolver.inspect(
        [quote],
        parameters,
    )

    assert coverage.is_complete is False

    assert coverage.missing_target_futures_prices == (
        AU,
    )


def test_missing_remaining_days_is_detected() -> None:
    """
    Missing remaining days must be detected before valuation.
    """

    quote = make_quote()

    parameters = make_parameters(
        include_remaining_days=False,
    )

    coverage = ScannerBatchParameterResolver.inspect(
        [quote],
        parameters,
    )

    assert coverage.is_complete is False

    assert coverage.missing_remaining_days == (
        AU,
    )


def test_missing_reference_volatility_is_detected() -> None:
    """
    Missing reference volatility must be detected before
    valuation.
    """

    quote = make_quote()

    parameters = make_parameters(
        include_reference_volatility=False,
    )

    coverage = ScannerBatchParameterResolver.inspect(
        [quote],
        parameters,
    )

    assert coverage.is_complete is False

    assert coverage.missing_reference_volatility == (
        AU,
    )


# ==========================================================
# Complete Validation
# ==========================================================


def test_complete_parameters_pass_validate_complete() -> None:
    """
    Complete scanner parameters must pass the resolver's
    validation boundary.
    """

    quote = make_quote()

    parameters = make_parameters()

    coverage = (
        ScannerBatchParameterResolver.validate_complete(
            [quote],
            parameters,
        )
    )

    assert coverage.is_complete is True


@pytest.mark.parametrize(
    "parameter_name,kwargs",
    [
        (
            "current_futures_prices",
            {
                "include_current": False,
            },
        ),
        (
            "target_futures_prices",
            {
                "include_target": False,
            },
        ),
        (
            "remaining_days",
            {
                "include_remaining_days": False,
            },
        ),
        (
            "reference_volatility",
            {
                "include_reference_volatility": False,
            },
        ),
    ],
)
def test_incomplete_parameter_sets_are_rejected(
    parameter_name: str,
    kwargs: dict[str, bool],
) -> None:
    """
    Every required parameter category must independently
    prevent complete validation.
    """

    quote = make_quote()

    parameters = make_parameters(
        **kwargs,
    )

    with pytest.raises(ValueError) as exc_info:
        ScannerBatchParameterResolver.validate_complete(
            [quote],
            parameters,
        )

    assert parameter_name in str(
        exc_info.value
    )


# ==========================================================
# Multiple Underlyings
# ==========================================================


def test_multiple_scanner_underlyings_require_independent_coverage() -> None:
    """
    Automatic scanning may contain multiple futures underlyings.

    Each underlying must have its own complete parameter set.
    """

    quotes = [
        make_quote(
            underlying=AU,
            symbol="AU2608-C-900",
        ),
        make_quote(
            underlying=CU,
            symbol="CU2608-C-80000",
            strike=80000.0,
            last_price=1200.0,
        ),
    ]

    parameters = BatchValuationParameters(
        current_futures_prices={
            AU: 900.0,
            CU: 80000.0,
        },
        target_futures_prices={
            AU: 1000.0,
            CU: 82000.0,
        },
        remaining_days={
            AU: 30,
            CU: 45,
        },
        reference_volatility={
            AU: ReferenceVolatilityScenario(
                current=0.267,
                target=0.2955,
            ),
            CU: ReferenceVolatilityScenario(
                current=0.18,
                target=0.20,
            ),
        },
        risk_free_rate=RISK_FREE_RATE,
        direction=OptionDirection.LONG,
    )

    coverage = (
        ScannerBatchParameterResolver.validate_complete(
            quotes,
            parameters,
        )
    )

    assert coverage.required_underlyings == (
        AU,
        CU,
    )

    assert coverage.is_complete is True


def test_one_missing_underlying_parameter_rejects_whole_batch() -> None:
    """
    If one scanned underlying lacks a required parameter,
    the batch must not be considered complete.

    This prevents partial parameter coverage from silently
    reaching valuation.
    """

    quotes = [
        make_quote(
            underlying=AU,
            symbol="AU2608-C-900",
        ),
        make_quote(
            underlying=CU,
            symbol="CU2608-C-80000",
            strike=80000.0,
            last_price=1200.0,
        ),
    ]

    parameters = BatchValuationParameters(
        current_futures_prices={
            AU: 900.0,
            CU: 80000.0,
        },
        target_futures_prices={
            AU: 1000.0,
            # CU deliberately missing.
        },
        remaining_days={
            AU: 30,
            CU: 45,
        },
        reference_volatility={
            AU: ReferenceVolatilityScenario(
                current=0.267,
                target=0.2955,
            ),
            CU: ReferenceVolatilityScenario(
                current=0.18,
                target=0.20,
            ),
        },
        risk_free_rate=RISK_FREE_RATE,
        direction=OptionDirection.LONG,
    )

    coverage = ScannerBatchParameterResolver.inspect(
        quotes,
        parameters,
    )

    assert coverage.is_complete is False

    assert coverage.missing_target_futures_prices == (
        CU,
    )

    assert coverage.missing_underlyings == (
        CU,
    )


# ==========================================================
# Explicit Underlying Boundary
# ==========================================================


def test_resolver_uses_explicit_quote_underlying() -> None:
    """
    The resolver must use OptionQuote.underlying directly.

    The option symbol intentionally contains an unrelated
    format so symbol parsing cannot accidentally satisfy the
    test.
    """

    quote = make_quote(
        underlying=AU,
        symbol="OPTION-TEST-001",
    )

    parameters = make_parameters()

    coverage = ScannerBatchParameterResolver.inspect(
        [quote],
        parameters,
    )

    assert coverage.required_underlyings == (
        AU,
    )


def test_empty_underlying_is_rejected_before_parameter_resolution() -> None:
    """
    Empty OptionQuote.underlying values must be rejected at
    the scanner-data boundary.
    """

    quote = make_quote(
        underlying="   ",
        symbol="OPTION-TEST-002",
    )

    parameters = make_parameters()

    with pytest.raises(ValueError):
        ScannerBatchParameterResolver.inspect(
            [quote],
            parameters,
        )


# ==========================================================
# UI Independence
# ==========================================================


def test_resolver_returns_core_data_only() -> None:
    """
    Resolver output must remain presentation-independent.
    """

    quote = make_quote()

    parameters = make_parameters()

    coverage = ScannerBatchParameterResolver.inspect(
        [quote],
        parameters,
    )

    assert isinstance(
        coverage.required_underlyings,
        tuple,
    )

    assert isinstance(
        coverage.missing_underlyings,
        tuple,
    )

    assert not hasattr(
        coverage,
        "entry",
    )

    assert not hasattr(
        coverage,
        "widget",
    )


# ==========================================================
# Deterministic Output
# ==========================================================


def test_required_underlyings_are_deterministically_sorted() -> None:
    """
    Underlying discovery must remain deterministic regardless
    of quote input order.
    """

    quotes = [
        make_quote(
            underlying=CU,
            symbol="CU2608-C-80000",
            strike=80000.0,
        ),
        make_quote(
            underlying=AU,
            symbol="AU2608-C-900",
        ),
    ]

    parameters = BatchValuationParameters(
        current_futures_prices={
            AU: 900.0,
            CU: 80000.0,
        },
        target_futures_prices={
            AU: 1000.0,
            CU: 82000.0,
        },
        remaining_days={
            AU: 30,
            CU: 45,
        },
        reference_volatility={
            AU: ReferenceVolatilityScenario(
                current=0.267,
                target=0.2955,
            ),
            CU: ReferenceVolatilityScenario(
                current=0.18,
                target=0.20,
            ),
        },
    )

    coverage = ScannerBatchParameterResolver.inspect(
        quotes,
        parameters,
    )

    assert coverage.required_underlyings == (
        AU,
        CU,
    )


# ==========================================================
# No UI / No Pricing Contract
# ==========================================================


def test_resolver_does_not_produce_valuation_result() -> None:
    """
    Resolver is a parameter-coverage service only.

    It must not expose pricing or valuation-result objects.
    """

    assert not hasattr(
        ScannerBatchParameterResolver,
        "evaluate",
    )

    assert not hasattr(
        ScannerBatchParameterResolver,
        "price",
    )

    assert not hasattr(
        ScannerBatchParameterResolver,
        "calculate_greeks",
    )