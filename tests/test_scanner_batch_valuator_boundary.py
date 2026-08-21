"""
Commodity Option Valuator Pro
=============================

Scanner Batch Valuator Boundary Tests.

Commit 0034 - Phase 2
---------------------

Purpose
-------
Validate the real result boundaries and exception boundaries of
ScannerBatchValuator.

Covered boundaries
------------------
1. Empty candidate selection
2. Missing current futures price
3. Missing target futures price
4. Missing remaining days
5. Missing reference volatility
6. Multiple missing parameter mappings
7. Invalid direction
8. Invalid reference volatility scenario type
9. Invalid candidate type through the actual production path
10. Invalid quote type through the existing bridge
11. Valuation exception propagation

Important
---------
These tests follow the existing production contracts.

They do NOT:
- redesign ScannerBatchValuator
- redesign ScannerBatchParameterResolver
- redesign ScannerValuationBridge
- redesign SingleOptionValuator
- modify ScannerBatchWorkflow
- modify ui/scanner.py
- introduce new exception contracts
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from core.scanner_batch_valuation import (
    BatchValuationParameters,
    ScannerBatchValuator,
)
from core.scanner_valuation_bridge import (
    ScannerCandidate,
    ScannerValuationBridge,
)
from core.single_option_valuation import (
    ReferenceVolatilityScenario,
    SingleOptionValuationInput,
    SingleOptionValuationResult,
    SingleOptionValuator,
)
from data.option_chain import OptionQuote
from models.option import OptionDirection


# ============================================================
# Helpers
# ============================================================


def make_quote(
    symbol: str,
    *,
    underlying: str = "AU2608",
    option_type: str = "CALL",
    strike: float = 100.0,
    last_price: float = 5.0,
    volume: int = 100,
    open_interest: int = 500,
    implied_volatility: float = 0.20,
) -> OptionQuote:
    """
    Create the real production OptionQuote.
    """
    return OptionQuote(
        symbol=symbol,
        underlying=underlying,
        option_type=option_type,
        strike=strike,
        last_price=last_price,
        volume=volume,
        open_interest=open_interest,
        implied_volatility=implied_volatility,
    )


def make_candidate(
    symbol: str = "AU2608-C-100",
    *,
    underlying: str = "AU2608",
    option_type: str = "CALL",
    strike: float = 100.0,
    volume: int = 100,
) -> ScannerCandidate:
    """
    Create the real production ScannerCandidate.
    """
    return ScannerCandidate(
        quote=make_quote(
            symbol,
            underlying=underlying,
            option_type=option_type,
            strike=strike,
            volume=volume,
        )
    )


def make_parameters(
    *,
    current_futures_prices: dict[str, float] | None = None,
    target_futures_prices: dict[str, float] | None = None,
    remaining_days: dict[str, int] | None = None,
    reference_volatility: (
        dict[str, ReferenceVolatilityScenario] | None
    ) = None,
    risk_free_rate: float = 0.025,
    direction: OptionDirection | str = OptionDirection.LONG,
) -> BatchValuationParameters:
    """
    Create the real production BatchValuationParameters.
    """
    return BatchValuationParameters(
        current_futures_prices=(
            current_futures_prices
            if current_futures_prices is not None
            else {
                "AU2608": 100.0,
            }
        ),
        target_futures_prices=(
            target_futures_prices
            if target_futures_prices is not None
            else {
                "AU2608": 105.0,
            }
        ),
        remaining_days=(
            remaining_days
            if remaining_days is not None
            else {
                "AU2608": 30,
            }
        ),
        reference_volatility=(
            reference_volatility
            if reference_volatility is not None
            else {
                "AU2608": ReferenceVolatilityScenario(
                    current=0.20,
                    target=0.22,
                ),
            }
        ),
        risk_free_rate=risk_free_rate,
        direction=direction,
    )


def make_batch_valuator(
    *,
    candidate: ScannerCandidate | None = None,
) -> tuple[
    ScannerBatchValuator,
    Mock,
    Mock,
]:
    """
    Create ScannerBatchValuator with production-compatible
    dependency boundaries.

    The bridge mock returns the real grouped selection contract.
    """
    selected = (
        candidate
        if candidate is not None
        else make_candidate()
    )

    bridge = Mock(
        spec=ScannerValuationBridge,
    )

    bridge.select_top_by_underlying_and_type.return_value = {
        (
            selected.underlying,
            selected.option_type,
        ): [
            selected,
        ],
    }

    def create_input(
        candidate: ScannerCandidate,
        **kwargs: object,
    ) -> SingleOptionValuationInput:
        """
        Delegate input construction to the real bridge implementation.
        """
        return ScannerValuationBridge.create_valuation_input(
            candidate,
            **kwargs,
        )

    bridge.create_valuation_input.side_effect = create_input

    valuator = Mock(
        spec=SingleOptionValuator,
    )

    valuator.evaluate.return_value = Mock(
        spec=SingleOptionValuationResult,
    )

    batch_valuator = ScannerBatchValuator(
        bridge=bridge,
        valuator=valuator,
    )

    return (
        batch_valuator,
        bridge,
        valuator,
    )


# ============================================================
# 1. Empty Candidate Selection
# ============================================================


def test_empty_candidate_selection_returns_empty_batch_result() -> None:
    """
    Empty scanner selection must produce an empty batch result.

    No valuation call is allowed because there is no candidate.
    """
    bridge = Mock(
        spec=ScannerValuationBridge,
    )

    bridge.select_top_by_underlying_and_type.return_value = {}

    valuator = Mock(
        spec=SingleOptionValuator,
    )

    batch_valuator = ScannerBatchValuator(
        bridge=bridge,
        valuator=valuator,
    )

    result = batch_valuator.scan_and_evaluate(
        [],
        top_n=1,
        parameters=make_parameters(),
    )

    assert result.count == 0
    assert result.items == ()
    assert result.results == ()
    assert result.symbols == ()

    valuator.evaluate.assert_not_called()


# ============================================================
# 2. Missing Current Futures Price
# ============================================================


def test_missing_current_futures_price_raises_value_error() -> None:
    """
    Missing current futures price for a selected underlying is a
    real parameter-coverage failure.
    """
    candidate = make_candidate()

    batch_valuator, _, valuator = make_batch_valuator(
        candidate=candidate,
    )

    parameters = make_parameters(
        current_futures_prices={},
    )

    with pytest.raises(
        ValueError,
        match="current_futures_prices=AU2608",
    ):
        batch_valuator.scan_and_evaluate(
            [candidate.quote],
            top_n=1,
            parameters=parameters,
        )

    valuator.evaluate.assert_not_called()


# ============================================================
# 3. Missing Target Futures Price
# ============================================================


def test_missing_target_futures_price_raises_value_error() -> None:
    """
    Missing target futures price must stop valuation before the
    SingleOptionValuator is reached.
    """
    candidate = make_candidate()

    batch_valuator, _, valuator = make_batch_valuator(
        candidate=candidate,
    )

    parameters = make_parameters(
        target_futures_prices={},
    )

    with pytest.raises(
        ValueError,
        match="target_futures_prices=AU2608",
    ):
        batch_valuator.scan_and_evaluate(
            [candidate.quote],
            top_n=1,
            parameters=parameters,
        )

    valuator.evaluate.assert_not_called()


# ============================================================
# 4. Missing Remaining Days
# ============================================================


def test_missing_remaining_days_raises_value_error() -> None:
    """
    Missing remaining-day information must stop valuation before
    SingleOptionValuator is reached.
    """
    candidate = make_candidate()

    batch_valuator, _, valuator = make_batch_valuator(
        candidate=candidate,
    )

    parameters = make_parameters(
        remaining_days={},
    )

    with pytest.raises(
        ValueError,
        match="remaining_days=AU2608",
    ):
        batch_valuator.scan_and_evaluate(
            [candidate.quote],
            top_n=1,
            parameters=parameters,
        )

    valuator.evaluate.assert_not_called()


# ============================================================
# 5. Missing Reference Volatility
# ============================================================


def test_missing_reference_volatility_raises_value_error() -> None:
    """
    Missing reference volatility must be treated as incomplete
    underlying-level valuation coverage.
    """
    candidate = make_candidate()

    batch_valuator, _, valuator = make_batch_valuator(
        candidate=candidate,
    )

    parameters = make_parameters(
        reference_volatility={},
    )

    with pytest.raises(
        ValueError,
        match="reference_volatility=AU2608",
    ):
        batch_valuator.scan_and_evaluate(
            [candidate.quote],
            top_n=1,
            parameters=parameters,
        )

    valuator.evaluate.assert_not_called()


# ============================================================
# 6. Multiple Missing Parameter Mappings
# ============================================================


def test_multiple_missing_parameter_mappings_are_reported_together() -> None:
    """
    Multiple missing parameter categories must be reported by the
    existing ScannerBatchParameterResolver boundary.
    """
    candidate = make_candidate()

    batch_valuator, _, valuator = make_batch_valuator(
        candidate=candidate,
    )

    parameters = make_parameters(
        current_futures_prices={},
        remaining_days={},
    )

    with pytest.raises(
        ValueError,
        match=(
            r"current_futures_prices=AU2608.*"
            r"remaining_days=AU2608"
        ),
    ):
        batch_valuator.scan_and_evaluate(
            [candidate.quote],
            top_n=1,
            parameters=parameters,
        )

    valuator.evaluate.assert_not_called()


# ============================================================
# 7. Invalid Direction
# ============================================================


def test_invalid_direction_raises_existing_value_error() -> None:
    """
    BatchValuationParameters already defines the direction
    validation contract.

    ScannerBatchValuator must preserve that contract.
    """
    candidate = make_candidate()

    batch_valuator, _, valuator = make_batch_valuator(
        candidate=candidate,
    )

    parameters = make_parameters(
        direction="INVALID_DIRECTION",
    )

    with pytest.raises(
        ValueError,
        match="direction must be LONG or SHORT",
    ):
        batch_valuator.scan_and_evaluate(
            [candidate.quote],
            top_n=1,
            parameters=parameters,
        )

    valuator.evaluate.assert_not_called()


# ============================================================
# 8. Invalid Reference Volatility Scenario Type
# ============================================================


def test_invalid_reference_volatility_type_raises_existing_type_error() -> None:
    """
    BatchValuationParameters validates the type of each
    reference-volatility scenario.
    """
    candidate = make_candidate()

    batch_valuator, _, valuator = make_batch_valuator(
        candidate=candidate,
    )

    parameters = make_parameters(
        reference_volatility={
            "AU2608": 0.20,  # type: ignore[arg-type]
        },
    )

    with pytest.raises(
        TypeError,
        match="ReferenceVolatilityScenario",
    ):
        batch_valuator.scan_and_evaluate(
            [candidate.quote],
            top_n=1,
            parameters=parameters,
        )

    valuator.evaluate.assert_not_called()


# ============================================================
# 9. Invalid Candidate Type
# ============================================================


def test_invalid_candidate_type_propagates_existing_attribute_error() -> None:
    """
    Record the actual ScannerBatchValuator.evaluate_candidates()
    boundary.

    Important
    ---------
    ScannerBatchValuator.evaluate_candidates() currently validates
    BatchValuationParameters but does NOT perform the resolver's
    ScannerCandidate type validation.

    Its actual execution path reaches create_valuation_input(),
    where candidate.underlying is accessed directly.

    Therefore an arbitrary object currently produces AttributeError.

    This test intentionally records that existing behavior instead
    of introducing a new TypeError contract.
    """
    batch_valuator, _, valuator = make_batch_valuator()

    invalid_candidate = object()

    with pytest.raises(
        AttributeError,
        match=r"object has no attribute 'underlying'",
    ):
        batch_valuator.evaluate_candidates(
            [invalid_candidate],  # type: ignore[list-item]
            make_parameters(),
        )

    valuator.evaluate.assert_not_called()


# ============================================================
# 10. Invalid Quote Type Through Existing Bridge
# ============================================================


def test_invalid_quote_type_uses_existing_bridge_type_error() -> None:
    """
    ScannerBatchValuator delegates candidate selection to the
    existing ScannerValuationBridge.

    The bridge explicitly validates OptionQuote instances and
    therefore owns this TypeError boundary.
    """
    batch_valuator = ScannerBatchValuator(
        bridge=ScannerValuationBridge(),
        valuator=Mock(
            spec=SingleOptionValuator,
        ),
    )

    with pytest.raises(
        TypeError,
        match="quotes must contain OptionQuote",
    ):
        batch_valuator.select_candidates(
            [object()],  # type: ignore[list-item]
            top_n=1,
        )


# ============================================================
# 11. Valuation Exception Propagation
# ============================================================


def test_single_option_valuation_exception_is_not_silently_swallowed() -> None:
    """
    ScannerBatchValuator delegates valuation to the existing
    SingleOptionValuator.

    If downstream valuation raises an exception, the batch layer
    must not silently convert the failure into an empty result or
    fabricate a successful BatchValuationItem.
    """
    candidate = make_candidate()

    batch_valuator, _, valuator = make_batch_valuator(
        candidate=candidate,
    )

    valuation_error = RuntimeError(
        "downstream valuation failure"
    )

    valuator.evaluate.side_effect = valuation_error

    with pytest.raises(
        RuntimeError,
        match="downstream valuation failure",
    ):
        batch_valuator.evaluate_candidate(
            candidate,
            make_parameters(),
        )

    valuator.evaluate.assert_called_once()