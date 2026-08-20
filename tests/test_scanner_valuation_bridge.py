"""
Tests for Commit 0027.

Scanner → Single Option Valuation Bridge.
"""

from __future__ import annotations

import pytest

from core.scanner_valuation_bridge import (
    ScannerCandidate,
    ScannerValuationBridge,
)
from core.single_option_valuation import (
    ReferenceVolatilityScenario,
    SingleOptionValuationInput,
)
from data.option_chain import OptionQuote
from models.option import (
    OptionDirection,
    OptionType,
)


# ==========================================================
# Fixtures
# ==========================================================


def make_quote(
    symbol: str,
    underlying: str,
    option_type: str,
    strike: float,
    price: float,
    volume: int,
    iv: float | None = 0.1954,
) -> OptionQuote:
    """Create a normalized option quote for testing."""

    return OptionQuote(
        symbol=symbol,
        underlying=underlying,
        option_type=option_type,
        strike=strike,
        last_price=price,
        volume=volume,
        open_interest=volume * 2,
        implied_volatility=iv,
    )


def make_quotes() -> list[OptionQuote]:
    """Create a representative option-chain dataset."""

    return [
        make_quote(
            "AU2608-C-968",
            "AU2608",
            "CALL",
            968.0,
            15.0,
            5000,
            0.1954,
        ),
        make_quote(
            "AU2608-C-970",
            "AU2608",
            "CALL",
            970.0,
            13.0,
            8000,
            0.1900,
        ),
        make_quote(
            "AU2608-C-972",
            "AU2608",
            "CALL",
            972.0,
            11.0,
            3000,
            0.1850,
        ),
        make_quote(
            "AU2608-P-968",
            "AU2608",
            "PUT",
            968.0,
            12.0,
            7000,
            0.2000,
        ),
        make_quote(
            "AU2608-P-970",
            "AU2608",
            "PUT",
            970.0,
            14.0,
            4000,
            0.2050,
        ),
        make_quote(
            "CU2609-C-90000",
            "CU2609",
            "CALL",
            90000.0,
            500.0,
            9000,
            0.2200,
        ),
    ]


# ==========================================================
# Candidate
# ==========================================================


def test_to_candidate() -> None:
    quote = make_quotes()[0]

    candidate = (
        ScannerValuationBridge.to_candidate(
            quote
        )
    )

    assert isinstance(
        candidate,
        ScannerCandidate,
    )

    assert candidate.symbol == "AU2608-C-968"
    assert candidate.underlying == "AU2608"
    assert candidate.option_type == "CALL"
    assert candidate.strike == 968.0
    assert candidate.option_price == 15.0
    assert candidate.volume == 5000
    assert candidate.open_interest == 10000
    assert candidate.implied_volatility == 0.1954


def test_to_candidate_rejects_invalid_type() -> None:
    with pytest.raises(
        TypeError,
        match="OptionQuote",
    ):
        ScannerValuationBridge.to_candidate(
            object()  # type: ignore[arg-type]
        )


# ==========================================================
# TOP N By Volume
# ==========================================================


def test_select_top_by_volume() -> None:
    candidates = (
        ScannerValuationBridge.select_top_by_volume(
            make_quotes(),
            top_n=2,
            underlying="AU2608",
            option_type="CALL",
        )
    )

    assert [
        candidate.symbol
        for candidate in candidates
    ] == [
        "AU2608-C-970",
        "AU2608-C-968",
    ]


def test_select_top_by_volume_put() -> None:
    candidates = (
        ScannerValuationBridge.select_top_by_volume(
            make_quotes(),
            top_n=2,
            underlying="AU2608",
            option_type="PUT",
        )
    )

    assert [
        candidate.symbol
        for candidate in candidates
    ] == [
        "AU2608-P-968",
        "AU2608-P-970",
    ]


def test_select_top_by_volume_rejects_invalid_top_n() -> None:
    with pytest.raises(
        ValueError,
        match="top_n",
    ):
        ScannerValuationBridge.select_top_by_volume(
            make_quotes(),
            top_n=0,
        )


def test_select_top_by_volume_rejects_invalid_option_type() -> None:
    with pytest.raises(
        ValueError,
        match="option_type",
    ):
        ScannerValuationBridge.select_top_by_volume(
            make_quotes(),
            top_n=2,
            option_type="INVALID",
        )


# ==========================================================
# Grouped Selection
# ==========================================================


def test_select_top_by_underlying_and_type() -> None:
    grouped = (
        ScannerValuationBridge
        .select_top_by_underlying_and_type(
            make_quotes(),
            top_n=2,
        )
    )

    assert (
        "AU2608",
        "CALL",
    ) in grouped

    assert (
        "AU2608",
        "PUT",
    ) in grouped

    assert (
        "CU2609",
        "CALL",
    ) in grouped

    assert [
        candidate.symbol
        for candidate in grouped[
            ("AU2608", "CALL")
        ]
    ] == [
        "AU2608-C-970",
        "AU2608-C-968",
    ]

    assert [
        candidate.symbol
        for candidate in grouped[
            ("AU2608", "PUT")
        ]
    ] == [
        "AU2608-P-968",
        "AU2608-P-970",
    ]

    assert [
        candidate.symbol
        for candidate in grouped[
            ("CU2609", "CALL")
        ]
    ] == [
        "CU2609-C-90000",
    ]


def test_grouped_selection_rejects_invalid_top_n() -> None:
    with pytest.raises(
        ValueError,
        match="top_n",
    ):
        ScannerValuationBridge.select_top_by_underlying_and_type(
            make_quotes(),
            top_n=0,
        )


# ==========================================================
# Find Candidate
# ==========================================================


def test_find_candidate() -> None:
    candidate = (
        ScannerValuationBridge.find_candidate(
            make_quotes(),
            "AU2608-C-968",
        )
    )

    assert candidate.symbol == "AU2608-C-968"
    assert candidate.strike == 968.0


def test_find_candidate_rejects_missing_symbol() -> None:
    with pytest.raises(
        ValueError,
        match="not found",
    ):
        ScannerValuationBridge.find_candidate(
            make_quotes(),
            "NOT-EXIST",
        )


# ==========================================================
# Valuation Input
# ==========================================================


def test_create_valuation_input() -> None:
    candidate = (
        ScannerValuationBridge.find_candidate(
            make_quotes(),
            "AU2608-C-968",
        )
    )

    reference_volatility = (
        ReferenceVolatilityScenario(
            current=26.70,
            target=29.55,
        )
    )

    inputs = (
        ScannerValuationBridge
        .create_valuation_input(
            candidate,
            current_futures_price=900.0,
            remaining_days=30,
            target_futures_price=1000.0,
            reference_volatility=(
                reference_volatility
            ),
        )
    )

    assert isinstance(
        inputs,
        SingleOptionValuationInput,
    )

    assert inputs.symbol == "AU2608-C-968"

    assert inputs.option_type == (
        OptionType.CALL
    )

    assert (
        inputs.current_futures_price
        == 900.0
    )

    assert inputs.strike == 968.0

    assert (
        inputs.current_option_price
        == 15.0
    )

    assert (
        inputs.current_option_iv
        == 0.1954
    )

    assert (
        inputs.remaining_days
        == 30
    )

    assert (
        inputs.target_futures_price
        == 1000.0
    )

    assert (
        inputs.reference_volatility
        is reference_volatility
    )

    assert (
        inputs.direction
        == OptionDirection.LONG
    )


def test_create_valuation_input_supports_put() -> None:
    candidate = (
        ScannerValuationBridge.find_candidate(
            make_quotes(),
            "AU2608-P-968",
        )
    )

    inputs = (
        ScannerValuationBridge
        .create_valuation_input(
            candidate,
            current_futures_price=900.0,
            remaining_days=30,
            target_futures_price=1000.0,
            reference_volatility=(
                ReferenceVolatilityScenario(
                    current=26.70,
                    target=29.55,
                )
            ),
        )
    )

    assert inputs.option_type == (
        OptionType.PUT
    )


def test_create_valuation_input_rejects_missing_iv() -> None:
    quote = make_quote(
        "AU2608-C-968",
        "AU2608",
        "CALL",
        968.0,
        15.0,
        5000,
        None,
    )

    candidate = (
        ScannerValuationBridge.to_candidate(
            quote
        )
    )

    with pytest.raises(
        ValueError,
        match="implied volatility",
    ):
        ScannerValuationBridge.create_valuation_input(
            candidate,
            current_futures_price=900.0,
            remaining_days=30,
            target_futures_price=1000.0,
            reference_volatility=(
                ReferenceVolatilityScenario(
                    current=26.70,
                    target=29.55,
                )
            ),
        )


def test_create_valuation_input_rejects_invalid_candidate() -> None:
    with pytest.raises(
        TypeError,
        match="ScannerCandidate",
    ):
        ScannerValuationBridge.create_valuation_input(
            object(),  # type: ignore[arg-type]
            current_futures_price=900.0,
            remaining_days=30,
            target_futures_price=1000.0,
            reference_volatility=(
                ReferenceVolatilityScenario(
                    current=26.70,
                    target=29.55,
                )
            ),
        )


# ==========================================================
# Public API
# ==========================================================


def test_public_exports() -> None:
    from core.scanner_valuation_bridge import (
        ScannerCandidate,
        ScannerValuationBridge,
    )

    assert ScannerCandidate is not None
    assert ScannerValuationBridge is not None