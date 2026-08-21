"""
Commodity Option Valuator Pro
=============================

Scanner Batch Parameter Resolver Tests.

Commit 0032
-----------

Tests the automatic-scanner parameter coverage boundary.

The resolver must:

1. Use OptionQuote.underlying explicitly.
2. Never derive underlying from option symbol.
3. Discover unique underlyings.
4. Detect missing batch parameters.
5. Accept complete parameters.
"""

from __future__ import annotations

from core.scanner_batch_parameter_resolver import (
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


UNDERLYING_A = "AU2608"
UNDERLYING_B = "AU2609"


def make_quote(
    *,
    symbol: str,
    underlying: str,
    volume: int = 100,
) -> OptionQuote:
    """Create a deterministic scanner quote."""

    return OptionQuote(
        symbol=symbol,
        underlying=underlying,
        option_type="CALL",
        strike=900.0,
        last_price=35.0,
        bid_price=34.5,
        ask_price=35.5,
        volume=volume,
        open_interest=500,
        implied_volatility=0.20,
    )


def make_parameters(
    *,
    underlyings: tuple[str, ...] = (
        UNDERLYING_A,
        UNDERLYING_B,
    ),
) -> BatchValuationParameters:
    """Create complete deterministic batch parameters."""

    return BatchValuationParameters(
        current_futures_prices={
            underlying: 900.0
            for underlying in underlyings
        },
        target_futures_prices={
            underlying: 920.0
            for underlying in underlyings
        },
        remaining_days={
            underlying: 30
            for underlying in underlyings
        },
        reference_volatility={
            underlying: ReferenceVolatilityScenario(
                current=0.20,
                target=0.22,
            )
            for underlying in underlyings
        },
    )


def test_required_underlyings_uses_explicit_field() -> None:
    """Underlying must come directly from OptionQuote.underlying."""

    quotes = (
        make_quote(
            symbol="OPTION-TEST-001",
            underlying=UNDERLYING_A,
        ),
        make_quote(
            symbol="COMPLETELY-DIFFERENT-SYMBOL",
            underlying=UNDERLYING_B,
        ),
    )

    result = ScannerBatchParameterResolver.required_underlyings(
        quotes
    )

    assert result == (
        UNDERLYING_A,
        UNDERLYING_B,
    )


def test_required_underlyings_is_unique_and_sorted() -> None:
    """Duplicate quotes must not duplicate the underlying."""

    quotes = (
        make_quote(
            symbol="A",
            underlying=UNDERLYING_B,
        ),
        make_quote(
            symbol="B",
            underlying=UNDERLYING_A,
        ),
        make_quote(
            symbol="C",
            underlying=UNDERLYING_B,
        ),
    )

    result = ScannerBatchParameterResolver.required_underlyings(
        quotes
    )

    assert result == (
        UNDERLYING_A,
        UNDERLYING_B,
    )


def test_complete_parameters_are_detected() -> None:
    """Complete parameter coverage must be accepted."""

    quotes = (
        make_quote(
            symbol="A",
            underlying=UNDERLYING_A,
        ),
        make_quote(
            symbol="B",
            underlying=UNDERLYING_B,
        ),
    )

    parameters = make_parameters()

    coverage = ScannerBatchParameterResolver.inspect(
        quotes,
        parameters,
    )

    assert coverage.is_complete
    assert coverage.required_underlyings == (
        UNDERLYING_A,
        UNDERLYING_B,
    )
    assert coverage.missing_underlyings == ()


def test_missing_current_price_is_detected() -> None:
    """Missing current futures price must be reported."""

    parameters = BatchValuationParameters(
        current_futures_prices={
            UNDERLYING_A: 900.0,
        },
        target_futures_prices={
            UNDERLYING_A: 920.0,
            UNDERLYING_B: 920.0,
        },
        remaining_days={
            UNDERLYING_A: 30,
            UNDERLYING_B: 30,
        },
        reference_volatility={
            UNDERLYING_A: ReferenceVolatilityScenario(
                current=0.20,
                target=0.22,
            ),
            UNDERLYING_B: ReferenceVolatilityScenario(
                current=0.20,
                target=0.22,
            ),
        },
    )

    quotes = (
        make_quote(
            symbol="A",
            underlying=UNDERLYING_A,
        ),
        make_quote(
            symbol="B",
            underlying=UNDERLYING_B,
        ),
    )

    coverage = ScannerBatchParameterResolver.inspect(
        quotes,
        parameters,
    )

    assert not coverage.is_complete
    assert coverage.missing_current_futures_prices == (
        UNDERLYING_B,
    )
    assert coverage.missing_underlyings == (
        UNDERLYING_B,
    )


def test_missing_multiple_parameter_groups_are_detected() -> None:
    """Multiple missing parameter groups must be reported."""

    parameters = BatchValuationParameters(
        current_futures_prices={
            UNDERLYING_A: 900.0,
        },
        target_futures_prices={
            UNDERLYING_A: 920.0,
        },
        remaining_days={
            UNDERLYING_A: 30,
            UNDERLYING_B: 30,
        },
        reference_volatility={
            UNDERLYING_A: ReferenceVolatilityScenario(
                current=0.20,
                target=0.22,
            ),
        },
    )

    quotes = (
        make_quote(
            symbol="A",
            underlying=UNDERLYING_A,
        ),
        make_quote(
            symbol="B",
            underlying=UNDERLYING_B,
        ),
    )

    coverage = ScannerBatchParameterResolver.inspect(
        quotes,
        parameters,
    )

    assert coverage.missing_current_futures_prices == (
        UNDERLYING_B,
    )

    assert coverage.missing_target_futures_prices == (
        UNDERLYING_B,
    )

    assert coverage.missing_reference_volatility == (
        UNDERLYING_B,
    )

    assert coverage.missing_underlyings == (
        UNDERLYING_B,
    )


def test_validate_complete_accepts_complete_parameters() -> None:
    """Complete coverage must pass validation."""

    quotes = (
        make_quote(
            symbol="A",
            underlying=UNDERLYING_A,
        ),
        make_quote(
            symbol="B",
            underlying=UNDERLYING_B,
        ),
    )

    coverage = (
        ScannerBatchParameterResolver.validate_complete(
            quotes,
            make_parameters(),
        )
    )

    assert coverage.is_complete


def test_validate_complete_rejects_missing_parameters() -> None:
    """Incomplete coverage must raise ValueError."""

    quotes = (
        make_quote(
            symbol="A",
            underlying=UNDERLYING_A,
        ),
        make_quote(
            symbol="B",
            underlying=UNDERLYING_B,
        ),
    )

    parameters = make_parameters(
        underlyings=(UNDERLYING_A,)
    )

    try:
        ScannerBatchParameterResolver.validate_complete(
            quotes,
            parameters,
        )
    except ValueError as exc:
        message = str(exc)
        assert UNDERLYING_B in message
        assert "current_futures_prices" in message
        assert "target_futures_prices" in message
        assert "remaining_days" in message
        assert "reference_volatility" in message
    else:
        raise AssertionError(
            "Expected incomplete parameters to raise ValueError."
        )


def test_empty_quotes_have_complete_empty_coverage() -> None:
    """No scanner candidates means no required underlyings."""

    parameters = make_parameters()

    coverage = ScannerBatchParameterResolver.inspect(
        (),
        parameters,
    )

    assert coverage.required_underlyings == ()
    assert coverage.is_complete
    assert coverage.missing_underlyings == ()


def test_invalid_quote_type_is_rejected() -> None:
    """Resolver must reject non-OptionQuote values."""

    try:
        ScannerBatchParameterResolver.required_underlyings(
            [object()]  # type: ignore[list-item]
        )
    except TypeError as exc:
        assert "OptionQuote" in str(exc)
    else:
        raise AssertionError(
            "Expected TypeError."
        )


def test_empty_underlying_is_rejected() -> None:
    """An empty explicit underlying must be rejected."""

    quote = make_quote(
        symbol="OPTION-001",
        underlying="",
    )

    try:
        ScannerBatchParameterResolver.required_underlyings(
            [quote]
        )
    except ValueError as exc:
        assert "underlying" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError."
        )