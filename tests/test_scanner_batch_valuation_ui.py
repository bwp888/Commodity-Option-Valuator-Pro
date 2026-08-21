"""
Commodity Option Valuator Pro
=============================

Scanner Batch Valuation UI Integration Tests.

Commit 0029-B
-------------

Verify that ScannerPage can invoke the existing
ScannerBatchValuator workflow without reimplementing
valuation logic in the UI layer.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from core.scanner_batch_valuation import (
    BatchValuationParameters,
    ScannerBatchValuator,
)
from core.single_option_valuation import (
    ReferenceVolatilityScenario,
)
from data.option_chain import OptionQuote
from ui.scanner import ScannerPage


def make_quote(
    *,
    symbol: str = "AU2608-C-968",
    option_type: str = "CALL",
) -> OptionQuote:
    """Build a deterministic OptionQuote fixture."""

    quote = object.__new__(OptionQuote)

    values = {
        "symbol": symbol,
        "underlying": "AU2608",
        "option_type": option_type,
        "strike": 968.0,
        "last_price": 15.0,
        "volume": 5000,
        "open_interest": 1000,
        "implied_volatility": 0.1954,
    }

    for name, value in values.items():
        object.__setattr__(quote, name, value)

    return quote


def make_parameters() -> BatchValuationParameters:
    """Build deterministic batch valuation parameters."""

    return BatchValuationParameters(
        current_futures_prices={"AU2608": 900.0},
        target_futures_prices={"AU2608": 1000.0},
        remaining_days={"AU2608": 30},
        reference_volatility={
            "AU2608": ReferenceVolatilityScenario(
                current=26.70,
                target=29.55,
            ),
        },
    )


def make_page() -> ScannerPage:
    """Create a ScannerPage without initializing Tk."""

    page = ScannerPage.__new__(ScannerPage)
    page.display_valuation_results = Mock()
    return page


def test_evaluate_quotes_uses_existing_batch_valuator() -> None:
    """ScannerPage must delegate execution to ScannerBatchValuator."""

    page = make_page()
    batch_valuator = Mock(spec=ScannerBatchValuator)
    expected = Mock()
    expected.count = 1
    batch_valuator.scan_and_evaluate.return_value = expected

    result = page.evaluate_quotes(
        [make_quote()],
        top_n=1,
        parameters=make_parameters(),
        valuator=batch_valuator,
    )

    assert result is expected
    assert page.valuation_result is expected
    batch_valuator.scan_and_evaluate.assert_called_once()
    page.display_valuation_results.assert_called_once_with(expected)


def test_evaluate_quotes_real_workflow_produces_comprehensive_result() -> None:
    """The UI execution boundary must preserve the real batch workflow."""

    page = make_page()

    result = page.evaluate_quotes(
        [make_quote()],
        top_n=1,
        parameters=make_parameters(),
    )

    assert result.count == 1
    assert result.items[0].result.comprehensive_evaluation is not None


def test_evaluate_quotes_rejects_invalid_quote_container() -> None:
    """The execution boundary must reject an invalid quote container."""

    page = make_page()

    with pytest.raises(TypeError):
        page.evaluate_quotes(
            iter([make_quote()]),  # type: ignore[arg-type]
            top_n=1,
            parameters=make_parameters(),
        )


def test_evaluate_quotes_rejects_invalid_parameters() -> None:
    """The execution boundary must preserve the batch parameter contract."""

    page = make_page()

    with pytest.raises(TypeError):
        page.evaluate_quotes(
            [make_quote()],
            top_n=1,
            parameters=object(),  # type: ignore[arg-type]
        )
