"""
Tests for automatic option-chain scanning.

Commit 0025
------------

These tests verify only the scanner boundary.

The tests intentionally mock:

- TDXOptionReader
- RecommendationWorkflow

The existing valuation and recommendation engines are therefore
not duplicated here.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from core.auto_option_scanner import (
    AutoOptionScanParameters,
    AutoOptionScanner,
)
from core.recommendation_workflow import (
    RecommendationWorkflowResult,
)
from data.option_chain import OptionQuote


# ==========================================================
# Fixtures
# ==========================================================


@pytest.fixture
def quotes() -> list[OptionQuote]:
    """Return representative normalized option quotes."""

    return [
        OptionQuote(
            symbol="A2609-C-3400",
            underlying="A",
            option_type="CALL",
            strike=3400.0,
            last_price=85.0,
            bid_price=84.0,
            ask_price=86.0,
            volume=1200,
            open_interest=3000,
        ),
        OptionQuote(
            symbol="A2609-P-3400",
            underlying="A",
            option_type="PUT",
            strike=3400.0,
            last_price=72.0,
            bid_price=71.0,
            ask_price=73.0,
            volume=900,
            open_interest=2800,
        ),
    ]


@pytest.fixture
def workflow() -> Mock:
    """Return a mocked RecommendationWorkflow."""

    mock = Mock(spec=__import__(
        "core.recommendation_workflow",
        fromlist=["RecommendationWorkflow"],
    ).RecommendationWorkflow)

    return mock


@pytest.fixture
def scanner(
    workflow: Mock,
) -> AutoOptionScanner:
    """Return scanner with injected workflow."""

    return AutoOptionScanner(
        workflow=workflow,
    )


# ==========================================================
# Parameters
# ==========================================================


def test_scan_parameters_accept_valid_values() -> None:
    """Valid parameters should pass validation."""

    parameters = AutoOptionScanParameters(
        underlying_price=3400.0,
        days=30,
        volatility=0.25,
    )

    parameters.validate()


def test_scan_parameters_reject_invalid_underlying_price() -> None:
    """Underlying price must be positive."""

    parameters = AutoOptionScanParameters(
        underlying_price=0.0,
        days=30,
        volatility=0.25,
    )

    with pytest.raises(
        ValueError,
        match="underlying_price",
    ):
        parameters.validate()


def test_scan_parameters_reject_invalid_days() -> None:
    """Remaining days must be positive."""

    parameters = AutoOptionScanParameters(
        underlying_price=3400.0,
        days=0,
        volatility=0.25,
    )

    with pytest.raises(
        ValueError,
        match="days",
    ):
        parameters.validate()


def test_scan_parameters_reject_invalid_volatility() -> None:
    """Volatility must be positive."""

    parameters = AutoOptionScanParameters(
        underlying_price=3400.0,
        days=30,
        volatility=0.0,
    )

    with pytest.raises(
        ValueError,
        match="volatility",
    ):
        parameters.validate()


def test_scan_parameters_reject_negative_min_volume() -> None:
    """Minimum volume cannot be negative."""

    parameters = AutoOptionScanParameters(
        underlying_price=3400.0,
        days=30,
        volatility=0.25,
        min_volume=-1,
    )

    with pytest.raises(
        ValueError,
        match="min_volume",
    ):
        parameters.validate()


def test_scan_parameters_reject_invalid_top_n() -> None:
    """TOP N must be positive when specified."""

    parameters = AutoOptionScanParameters(
        underlying_price=3400.0,
        days=30,
        volatility=0.25,
        top_n=0,
    )

    with pytest.raises(
        ValueError,
        match="top_n",
    ):
        parameters.validate()


# ==========================================================
# Quote conversion
# ==========================================================


def test_quote_to_record(
    scanner: AutoOptionScanner,
    quotes: list[OptionQuote],
) -> None:
    """OptionQuote should convert to the existing market schema."""

    record = scanner.quote_to_record(
        quotes[0]
    )

    assert record == {
        "symbol": "A2609-C-3400",
        "direction": "CALL",
        "strike": 3400.0,
        "price": 85.0,
        "volume": 1200,
        "open_interest": 3000,
        "bid": 84.0,
        "ask": 86.0,
    }


def test_quote_to_record_rejects_invalid_type(
    scanner: AutoOptionScanner,
) -> None:
    """Only OptionQuote objects are accepted."""

    with pytest.raises(
        TypeError,
        match="OptionQuote",
    ):
        scanner.quote_to_record(
            object()  # type: ignore[arg-type]
        )


def test_quotes_to_records(
    scanner: AutoOptionScanner,
    quotes: list[OptionQuote],
) -> None:
    """Multiple quotes should be converted in order."""

    records = scanner.quotes_to_records(
        quotes
    )

    assert len(records) == 2

    assert records[0]["symbol"] == (
        "A2609-C-3400"
    )

    assert records[1]["symbol"] == (
        "A2609-P-3400"
    )


def test_quote_to_record_uses_zero_for_missing_bid_ask(
    scanner: AutoOptionScanner,
) -> None:
    """Missing bid/ask values should map to zero."""

    quote = OptionQuote(
        symbol="A2609-C-3400",
        underlying="A",
        option_type="CALL",
        strike=3400.0,
        last_price=85.0,
        volume=100,
    )

    record = scanner.quote_to_record(
        quote
    )

    assert record["bid"] == 0.0
    assert record["ask"] == 0.0


# ==========================================================
# Scan
# ==========================================================


def test_scan_quotes_calls_existing_workflow(
    scanner: AutoOptionScanner,
    workflow: Mock,
    quotes: list[OptionQuote],
) -> None:
    """Scanner should delegate recommendation generation."""

    expected = Mock(
        spec=RecommendationWorkflowResult
    )

    workflow.run.return_value = expected

    parameters = AutoOptionScanParameters(
        underlying_price=3400.0,
        days=30,
        volatility=0.25,
        risk_free_rate=0.025,
        min_volume=100,
        top_n=10,
    )

    result = scanner.scan_quotes(
        quotes,
        parameters=parameters,
    )

    assert result is expected

    workflow.run.assert_called_once()

    kwargs = workflow.run.call_args.kwargs

    assert kwargs["underlying_price"] == 3400.0
    assert kwargs["days"] == 30
    assert kwargs["volatility"] == 0.25
    assert kwargs["risk_free_rate"] == 0.025
    assert kwargs["min_volume"] == 100
    assert kwargs["top_n"] == 10

    assert len(kwargs["records"]) == 2


def test_scan_quotes_preserves_direction_filter(
    scanner: AutoOptionScanner,
    workflow: Mock,
    quotes: list[OptionQuote],
) -> None:
    """Direction filter should be passed unchanged."""

    expected = Mock(
        spec=RecommendationWorkflowResult
    )

    workflow.run.return_value = expected

    parameters = AutoOptionScanParameters(
        underlying_price=3400.0,
        days=30,
        volatility=0.25,
        direction="CALL",
    )

    scanner.scan_quotes(
        quotes,
        parameters=parameters,
    )

    kwargs = workflow.run.call_args.kwargs

    assert kwargs["direction"] == "CALL"


def test_scan_reads_tdx_file(
    scanner: AutoOptionScanner,
    workflow: Mock,
    quotes: list[OptionQuote],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """scan() should read the TDX file before running workflow."""

    expected = Mock(
        spec=RecommendationWorkflowResult
    )

    workflow.run.return_value = expected

    read_quotes = Mock(
        return_value=quotes
    )

    monkeypatch.setattr(
        scanner,
        "read_quotes",
        read_quotes,
    )

    file_path = (
        tmp_path
        / "option_chain.xls"
    )

    result = scanner.scan(
        file_path=file_path,
        underlying_price=3400.0,
        days=30,
        volatility=0.25,
    )

    assert result is expected

    read_quotes.assert_called_once_with(
        file_path
    )

    workflow.run.assert_called_once()


def test_scan_rejects_invalid_parameters_before_reading(
    scanner: AutoOptionScanner,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Parameter validation should happen before file loading."""

    read_quotes = Mock()

    monkeypatch.setattr(
        scanner,
        "read_quotes",
        read_quotes,
    )

    with pytest.raises(
        ValueError,
        match="underlying_price",
    ):
        scanner.scan(
            file_path=tmp_path / "option_chain.xls",
            underlying_price=0.0,
            days=30,
            volatility=0.25,
        )

    read_quotes.assert_not_called()


def test_scan_quotes_accepts_generator(
    scanner: AutoOptionScanner,
    workflow: Mock,
    quotes: list[OptionQuote],
) -> None:
    """scan_quotes() should accept any iterable of quotes."""

    expected = Mock(
        spec=RecommendationWorkflowResult
    )

    workflow.run.return_value = expected

    parameters = AutoOptionScanParameters(
        underlying_price=3400.0,
        days=30,
        volatility=0.25,
    )

    result = scanner.scan_quotes(
        (quote for quote in quotes),
        parameters=parameters,
    )

    assert result is expected

    workflow.run.assert_called_once()

    records = (
        workflow.run.call_args.kwargs["records"]
    )

    assert len(records) == 2


def test_scan_uses_default_risk_free_rate(
    scanner: AutoOptionScanner,
    workflow: Mock,
    quotes: list[OptionQuote],
) -> None:
    """The existing workflow default risk-free rate should be preserved."""

    workflow.run.return_value = Mock(
        spec=RecommendationWorkflowResult
    )

    scanner.scan_quotes(
        quotes,
        parameters=AutoOptionScanParameters(
            underlying_price=3400.0,
            days=30,
            volatility=0.25,
        ),
    )

    kwargs = workflow.run.call_args.kwargs

    assert kwargs["risk_free_rate"] == 0.025