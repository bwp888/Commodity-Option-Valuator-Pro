"""
Tests for Commit 0027 Phase 2.

Batch Scanner Valuation Workflow.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from core.scanner_batch_valuation import (
    BatchValuationItem,
    BatchValuationParameters,
    BatchValuationResult,
    ScannerBatchValuator,
)
from core.single_option_valuation import (
    ReferenceVolatilityScenario,
    SingleOptionValuationResult,
)
from data.option_chain import OptionQuote


# ==========================================================
# Helpers
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

    This keeps the tests focused on the batch workflow.
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
    """Create a multi-underlying option chain."""

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
            symbol="AU2608-C-970",
            underlying="AU2608",
            option_type="CALL",
            strike=970.0,
            last_price=13.0,
            volume=3000,
            implied_volatility=0.1900,
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
        make_quote(
            symbol="AU2608-P-970",
            underlying="AU2608",
            option_type="PUT",
            strike=970.0,
            last_price=12.0,
            volume=2000,
            implied_volatility=0.1980,
        ),
        make_quote(
            symbol="CU2609-C-80000",
            underlying="CU2609",
            option_type="CALL",
            strike=80000.0,
            last_price=1000.0,
            volume=7000,
            implied_volatility=0.2200,
        ),
        make_quote(
            symbol="CU2609-C-81000",
            underlying="CU2609",
            option_type="CALL",
            strike=81000.0,
            last_price=800.0,
            volume=5000,
            implied_volatility=0.2150,
        ),
        make_quote(
            symbol="CU2609-P-80000",
            underlying="CU2609",
            option_type="PUT",
            strike=80000.0,
            last_price=900.0,
            volume=6000,
            implied_volatility=0.2250,
        ),
        make_quote(
            symbol="CU2609-P-81000",
            underlying="CU2609",
            option_type="PUT",
            strike=81000.0,
            last_price=700.0,
            volume=4000,
            implied_volatility=0.2180,
        ),
    ]


def make_parameters() -> BatchValuationParameters:
    """Create batch valuation parameters."""

    return BatchValuationParameters(
        current_futures_prices={
            "AU2608": 900.0,
            "CU2609": 80000.0,
        },
        target_futures_prices={
            "AU2608": 1000.0,
            "CU2609": 85000.0,
        },
        remaining_days={
            "AU2608": 30,
            "CU2609": 45,
        },
        reference_volatility={
            "AU2608": ReferenceVolatilityScenario(
                current=26.70,
                target=29.55,
            ),
            "CU2609": ReferenceVolatilityScenario(
                current=20.0,
                target=22.0,
            ),
        },
    )


# ==========================================================
# Parameter Tests
# ==========================================================


def test_batch_parameters_validate() -> None:
    parameters = make_parameters()

    parameters.validate()


def test_batch_parameters_reject_negative_rate() -> None:
    parameters = BatchValuationParameters(
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
                current=20.0,
                target=21.0,
            ),
        },
        risk_free_rate=-0.01,
    )

    with pytest.raises(
        ValueError,
        match="risk_free_rate",
    ):
        parameters.validate()


def test_batch_parameters_reject_invalid_reference_type() -> None:
    parameters = BatchValuationParameters(
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
            "AU2608": 0.20,  # type: ignore[arg-type]
        },
    )

    with pytest.raises(
        TypeError,
        match="ReferenceVolatilityScenario",
    ):
        parameters.validate()


# ==========================================================
# Selection
# ==========================================================


def test_select_candidates_groups_by_underlying_and_type() -> None:
    valuator = ScannerBatchValuator()

    candidates = valuator.select_candidates(
        make_quotes(),
        top_n=1,
    )

    symbols = {
        candidate.symbol
        for candidate in candidates
    }

    assert symbols == {
        "AU2608-C-968",
        "AU2608-P-968",
        "CU2609-C-80000",
        "CU2609-P-80000",
    }


def test_select_candidates_top_two() -> None:
    valuator = ScannerBatchValuator()

    candidates = valuator.select_candidates(
        make_quotes(),
        top_n=2,
    )

    assert len(candidates) == 8


def test_select_candidates_rejects_invalid_top_n() -> None:
    valuator = ScannerBatchValuator()

    with pytest.raises(ValueError):
        valuator.select_candidates(
            make_quotes(),
            top_n=0,
        )


# ==========================================================
# Input Creation
# ==========================================================


def test_create_valuation_input_resolves_underlying_parameters() -> None:
    valuator = ScannerBatchValuator()

    candidates = valuator.select_candidates(
        make_quotes(),
        top_n=1,
    )

    candidate = next(
        item
        for item in candidates
        if item.symbol == "AU2608-C-968"
    )

    valuation_input = (
        valuator.create_valuation_input(
            candidate,
            make_parameters(),
        )
    )

    assert (
        valuation_input.symbol
        == "AU2608-C-968"
    )

    assert (
        valuation_input.current_futures_price
        == 900.0
    )

    assert (
        valuation_input.target_futures_price
        == 1000.0
    )

    assert (
        valuation_input.strike
        == 968.0
    )

    assert (
        valuation_input.current_option_price
        == 15.0
    )

    assert (
        valuation_input.current_option_iv
        == 0.1954
    )

    assert (
        valuation_input.remaining_days
        == 30
    )


def test_create_valuation_input_rejects_missing_current_price() -> None:
    valuator = ScannerBatchValuator()

    candidate = valuator.select_candidates(
        make_quotes(),
        top_n=1,
    )[0]

    parameters = make_parameters()

    parameters = BatchValuationParameters(
        current_futures_prices={},
        target_futures_prices=(
            parameters.target_futures_prices
        ),
        remaining_days=(
            parameters.remaining_days
        ),
        reference_volatility=(
            parameters.reference_volatility
        ),
    )

    with pytest.raises(
        ValueError,
        match="current_futures_prices",
    ):
        valuator.create_valuation_input(
            candidate,
            parameters,
        )


def test_create_valuation_input_rejects_missing_target_price() -> None:
    valuator = ScannerBatchValuator()

    candidate = valuator.select_candidates(
        make_quotes(),
        top_n=1,
    )[0]

    parameters = make_parameters()

    parameters = BatchValuationParameters(
        current_futures_prices=(
            parameters.current_futures_prices
        ),
        target_futures_prices={},
        remaining_days=(
            parameters.remaining_days
        ),
        reference_volatility=(
            parameters.reference_volatility
        ),
    )

    with pytest.raises(
        ValueError,
        match="target_futures_prices",
    ):
        valuator.create_valuation_input(
            candidate,
            parameters,
        )


def test_create_valuation_input_rejects_missing_remaining_days() -> None:
    valuator = ScannerBatchValuator()

    candidate = valuator.select_candidates(
        make_quotes(),
        top_n=1,
    )[0]

    parameters = make_parameters()

    parameters = BatchValuationParameters(
        current_futures_prices=(
            parameters.current_futures_prices
        ),
        target_futures_prices=(
            parameters.target_futures_prices
        ),
        remaining_days={},
        reference_volatility=(
            parameters.reference_volatility
        ),
    )

    with pytest.raises(
        ValueError,
        match="remaining_days",
    ):
        valuator.create_valuation_input(
            candidate,
            parameters,
        )


def test_create_valuation_input_rejects_missing_reference_volatility() -> None:
    valuator = ScannerBatchValuator()

    candidate = valuator.select_candidates(
        make_quotes(),
        top_n=1,
    )[0]

    parameters = make_parameters()

    parameters = BatchValuationParameters(
        current_futures_prices=(
            parameters.current_futures_prices
        ),
        target_futures_prices=(
            parameters.target_futures_prices
        ),
        remaining_days=(
            parameters.remaining_days
        ),
        reference_volatility={},
    )

    with pytest.raises(
        ValueError,
        match="reference_volatility",
    ):
        valuator.create_valuation_input(
            candidate,
            parameters,
        )


# ==========================================================
# Batch Input Creation
# ==========================================================


def test_create_valuation_inputs() -> None:
    valuator = ScannerBatchValuator()

    candidates = valuator.select_candidates(
        make_quotes(),
        top_n=1,
    )

    inputs = valuator.create_valuation_inputs(
        candidates,
        make_parameters(),
    )

    assert len(inputs) == 4

    assert {
        item.symbol
        for item in inputs
    } == {
        "AU2608-C-968",
        "AU2608-P-968",
        "CU2609-C-80000",
        "CU2609-P-80000",
    }


# ==========================================================
# Batch Evaluation
# ==========================================================


def test_evaluate_candidates() -> None:
    valuator = ScannerBatchValuator()

    candidates = valuator.select_candidates(
        make_quotes(),
        top_n=1,
    )

    result = valuator.evaluate_candidates(
        candidates,
        make_parameters(),
    )

    assert isinstance(
        result,
        BatchValuationResult,
    )

    assert result.count == 4


def test_evaluate_candidates_returns_complete_results() -> None:
    valuator = ScannerBatchValuator()

    candidates = valuator.select_candidates(
        make_quotes(),
        top_n=1,
    )

    result = valuator.evaluate_candidates(
        candidates,
        make_parameters(),
    )

    assert all(
        isinstance(
            item,
            BatchValuationItem,
        )
        for item in result.items
    )

    assert all(
        isinstance(
            item.result,
            SingleOptionValuationResult,
        )
        for item in result.items
    )


def test_evaluate_candidates_preserves_selected_symbols() -> None:
    valuator = ScannerBatchValuator()

    candidates = valuator.select_candidates(
        make_quotes(),
        top_n=1,
    )

    result = valuator.evaluate_candidates(
        candidates,
        make_parameters(),
    )

    assert result.symbols == tuple(
        candidate.symbol
        for candidate in candidates
    )


# ==========================================================
# Scan And Evaluate
# ==========================================================


def test_scan_and_evaluate() -> None:
    valuator = ScannerBatchValuator()

    result = valuator.scan_and_evaluate(
        make_quotes(),
        top_n=1,
        parameters=make_parameters(),
    )

    assert result.count == 4


def test_scan_and_evaluate_uses_reference_volatility() -> None:
    valuator = ScannerBatchValuator()

    result = valuator.scan_and_evaluate(
        make_quotes(),
        top_n=1,
        parameters=make_parameters(),
    )

    au_call = next(
        item
        for item in result.items
        if item.symbol == "AU2608-C-968"
    )

    expected = (
        0.1954
        * (
            29.55 / 26.70
        )
    )

    assert (
        au_call.result.target_option_iv
        == pytest.approx(
            expected,
            rel=1e-10,
        )
    )


# ==========================================================
# Grouping
# ==========================================================


def test_result_by_underlying() -> None:
    valuator = ScannerBatchValuator()

    result = valuator.scan_and_evaluate(
        make_quotes(),
        top_n=1,
        parameters=make_parameters(),
    )

    grouped = result.by_underlying()

    assert set(
        grouped.keys()
    ) == {
        "AU2608",
        "CU2609",
    }

    assert len(
        grouped["AU2608"]
    ) == 2

    assert len(
        grouped["CU2609"]
    ) == 2


# ==========================================================
# Export
# ==========================================================


def test_result_to_dict() -> None:
    valuator = ScannerBatchValuator()

    result = valuator.scan_and_evaluate(
        make_quotes(),
        top_n=1,
        parameters=make_parameters(),
    )

    data = result.to_dict()

    assert len(data) == 4

    assert data[0]["symbol"] in {
        "AU2608-C-968",
        "AU2608-P-968",
        "CU2609-C-80000",
        "CU2609-P-80000",
    }

    assert (
        "target_theoretical_price"
        in data[0]
    )


# ==========================================================
# Public API
# ==========================================================


def test_public_exports() -> None:
    from core.scanner_batch_valuation import (
        BatchValuationItem,
        BatchValuationParameters,
        BatchValuationResult,
        ScannerBatchValuator,
    )

    assert BatchValuationItem is not None
    assert BatchValuationParameters is not None
    assert BatchValuationResult is not None
    assert ScannerBatchValuator is not None