"""
Commodity Option Valuator Pro
=============================

Tests for Market Ranking Engine.

Commit 0016
------------

Author : Simon
Version : 0.5.0
"""

from __future__ import annotations

import pytest

from core.market_ranking import (
    MarketRankingEngine,
    RankingItem,
    RankingResult,
)

from core.valuation_engine import (
    ValuationResult,
)

from models.option_scanner import (
    OptionContract,
    OptionDirection,
)


# ==========================================================
# Test Data
# ==========================================================


def make_contract(
    symbol: str = "TEST-C-100",
    direction: OptionDirection = OptionDirection.CALL,
    volume: int = 500,
    open_interest: int = 1000,
) -> OptionContract:
    """Create a test option contract."""

    return OptionContract(
        symbol=symbol,
        direction=direction,
        strike=100.0,
        price=5.0,
        volume=volume,
        open_interest=open_interest,
        bid=0.0,
        ask=0.0,
    )


def make_valuation(
    symbol: str = "TEST-C-100",
    difference: float = 3.0,
    risk_score: float = 1.0,
) -> ValuationResult:
    """Create a test valuation result."""

    return ValuationResult(
        symbol=symbol,
        direction=OptionDirection.CALL,
        premium=5.0,
        theoretical_price=8.0,
        delta=0.5,
        gamma=0.02,
        theta=-0.05,
        vega=0.10,
        difference=difference,
        risk_score=risk_score,
    )


def make_items() -> list[
    tuple[OptionContract, ValuationResult]
]:
    """Create multiple ranking records."""

    return [
        (
            make_contract(
                symbol="TEST-C-100",
                volume=500,
                open_interest=1000,
            ),
            make_valuation(
                symbol="TEST-C-100",
                difference=3.0,
                risk_score=1.0,
            ),
        ),
        (
            make_contract(
                symbol="TEST-C-105",
                volume=300,
                open_interest=800,
            ),
            make_valuation(
                symbol="TEST-C-105",
                difference=5.0,
                risk_score=1.0,
            ),
        ),
        (
            make_contract(
                symbol="TEST-C-110",
                volume=100,
                open_interest=300,
            ),
            make_valuation(
                symbol="TEST-C-110",
                difference=1.0,
                risk_score=2.0,
            ),
        ),
    ]


# ==========================================================
# Import
# ==========================================================


def test_ranking_engine_import() -> None:
    """Ranking engine should be importable."""

    engine = MarketRankingEngine()

    assert engine is not None


# ==========================================================
# Result Structures
# ==========================================================


def test_ranking_item_is_available() -> None:
    """RankingItem should store ranking data."""

    contract = make_contract()

    valuation = make_valuation()

    item = RankingItem(
        contract=contract,
        valuation=valuation,
        score=2.5,
    )

    assert item.contract == contract
    assert item.valuation == valuation
    assert item.score == 2.5


def test_ranking_result_is_available() -> None:
    """RankingResult should expose ranked items."""

    contract = make_contract()

    valuation = make_valuation()

    item = RankingItem(
        contract=contract,
        valuation=valuation,
        score=2.5,
    )

    result = RankingResult(
        items=(item,),
        total_count=1,
    )

    assert result.total_count == 1
    assert result.top_symbol == "TEST-C-100"


def test_ranking_result_scores() -> None:
    """RankingResult should expose scores."""

    contract = make_contract()

    valuation = make_valuation()

    items = (
        RankingItem(
            contract=contract,
            valuation=valuation,
            score=3.0,
        ),
        RankingItem(
            contract=make_contract(
                symbol="TEST-C-105"
            ),
            valuation=make_valuation(
                symbol="TEST-C-105"
            ),
            score=2.0,
        ),
    )

    result = RankingResult(
        items=items,
        total_count=2,
    )

    assert result.scores == (
        3.0,
        2.0,
    )


def test_ranking_result_top() -> None:
    """RankingResult.top should return top N."""

    contract = make_contract()

    valuation = make_valuation()

    items = (
        RankingItem(
            contract=contract,
            valuation=valuation,
            score=3.0,
        ),
        RankingItem(
            contract=make_contract(
                symbol="TEST-C-105"
            ),
            valuation=make_valuation(
                symbol="TEST-C-105"
            ),
            score=2.0,
        ),
    )

    result = RankingResult(
        items=items,
        total_count=2,
    )

    top = result.top(1)

    assert len(top) == 1
    assert top[0].score == 3.0


def test_ranking_result_top_rejects_invalid_n() -> None:
    """RankingResult.top should reject invalid N."""

    result = RankingResult(
        items=(),
        total_count=0,
    )

    with pytest.raises(ValueError):
        result.top(0)


# ==========================================================
# Engine Initialization
# ==========================================================


def test_engine_default_weights() -> None:
    """Default ranking weights should be valid."""

    engine = MarketRankingEngine()

    assert engine.risk_weight == 1.0
    assert engine.liquidity_weight == 0.001


def test_engine_accepts_custom_weights() -> None:
    """Custom ranking weights should be stored."""

    engine = MarketRankingEngine(
        risk_weight=2.0,
        liquidity_weight=0.01,
    )

    assert engine.risk_weight == 2.0
    assert engine.liquidity_weight == 0.01


def test_engine_rejects_negative_risk_weight() -> None:
    """Negative risk weight should be rejected."""

    with pytest.raises(ValueError):
        MarketRankingEngine(
            risk_weight=-1.0
        )


def test_engine_rejects_negative_liquidity_weight() -> None:
    """Negative liquidity weight should be rejected."""

    with pytest.raises(ValueError):
        MarketRankingEngine(
            liquidity_weight=-1.0
        )


# ==========================================================
# Score Calculation
# ==========================================================


def test_calculate_score() -> None:
    """Score should combine difference, risk and liquidity."""

    engine = MarketRankingEngine(
        risk_weight=1.0,
        liquidity_weight=0.001,
    )

    contract = make_contract(
        volume=500,
        open_interest=1000,
    )

    valuation = make_valuation(
        difference=3.0,
        risk_score=1.0,
    )

    score = engine.calculate_score(
        contract,
        valuation,
    )

    expected = (
        3.0
        - 1.0
        + (500 + 1000) * 0.001
    )

    assert score == pytest.approx(
        expected
    )


def test_higher_difference_improves_score() -> None:
    """Higher valuation difference should improve score."""

    engine = MarketRankingEngine(
        risk_weight=0.0,
        liquidity_weight=0.0,
    )

    contract = make_contract()

    low = make_valuation(
        difference=1.0,
        risk_score=0.0,
    )

    high = make_valuation(
        difference=5.0,
        risk_score=0.0,
    )

    assert engine.calculate_score(
        contract,
        high,
    ) > engine.calculate_score(
        contract,
        low,
    )


def test_higher_risk_reduces_score() -> None:
    """Higher risk should reduce score."""

    engine = MarketRankingEngine(
        risk_weight=1.0,
        liquidity_weight=0.0,
    )

    contract = make_contract()

    low_risk = make_valuation(
        difference=3.0,
        risk_score=1.0,
    )

    high_risk = make_valuation(
        difference=3.0,
        risk_score=4.0,
    )

    assert engine.calculate_score(
        contract,
        low_risk,
    ) > engine.calculate_score(
        contract,
        high_risk,
    )


def test_higher_liquidity_improves_score() -> None:
    """Higher liquidity should improve score."""

    engine = MarketRankingEngine(
        risk_weight=0.0,
        liquidity_weight=0.001,
    )

    low_liquidity = make_contract(
        volume=100,
        open_interest=200,
    )

    high_liquidity = make_contract(
        volume=1000,
        open_interest=2000,
    )

    valuation = make_valuation(
        difference=3.0,
        risk_score=0.0,
    )

    assert engine.calculate_score(
        high_liquidity,
        valuation,
    ) > engine.calculate_score(
        low_liquidity,
        valuation,
    )


# ==========================================================
# Ranking
# ==========================================================


def test_rank_orders_by_score() -> None:
    """Rank should order results by descending score."""

    engine = MarketRankingEngine(
        risk_weight=0.0,
        liquidity_weight=0.0,
    )

    result = engine.rank(
        make_items()
    )

    symbols = [
        item.contract.symbol
        for item in result.items
    ]

    assert symbols == [
        "TEST-C-105",
        "TEST-C-100",
        "TEST-C-110",
    ]


def test_rank_returns_ranking_items() -> None:
    """Rank should return RankingItem objects."""

    engine = MarketRankingEngine()

    result = engine.rank(
        make_items()
    )

    assert all(
        isinstance(
            item,
            RankingItem,
        )
        for item in result.items
    )


def test_rank_total_count() -> None:
    """Ranking result should report item count."""

    engine = MarketRankingEngine()

    result = engine.rank(
        make_items()
    )

    assert result.total_count == 3


def test_rank_empty_items() -> None:
    """Ranking empty input should return empty result."""

    engine = MarketRankingEngine()

    result = engine.rank(
        []
    )

    assert result.items == ()
    assert result.total_count == 0
    assert result.top_symbol is None


def test_rank_with_top_n() -> None:
    """Rank should support TOP N."""

    engine = MarketRankingEngine(
        risk_weight=0.0,
        liquidity_weight=0.0,
    )

    result = engine.rank(
        make_items(),
        top_n=2,
    )

    assert len(result.items) == 2

    assert [
        item.contract.symbol
        for item in result.items
    ] == [
        "TEST-C-105",
        "TEST-C-100",
    ]


def test_rank_rejects_invalid_top_n() -> None:
    """Rank should reject invalid TOP N."""

    engine = MarketRankingEngine()

    with pytest.raises(ValueError):
        engine.rank(
            make_items(),
            top_n=0,
        )


def test_rank_accepts_generator() -> None:
    """Rank should accept iterable generators."""

    engine = MarketRankingEngine()

    generator = (
        item
        for item in make_items()
    )

    result = engine.rank(
        generator
    )

    assert result.total_count == 3


# ==========================================================
# Convenience API
# ==========================================================


def test_rank_from_result() -> None:
    """rank_from_result should combine contracts and valuations."""

    engine = MarketRankingEngine(
        risk_weight=0.0,
        liquidity_weight=0.0,
    )

    pairs = make_items()

    contracts = [
        contract
        for contract, _ in pairs
    ]

    valuations = [
        valuation
        for _, valuation in pairs
    ]

    result = engine.rank_from_result(
        contracts=contracts,
        valuations=valuations,
    )

    assert result.total_count == 3

    assert result.top_symbol == (
        "TEST-C-105"
    )


def test_rank_from_result_supports_top_n() -> None:
    """rank_from_result should support TOP N."""

    engine = MarketRankingEngine(
        risk_weight=0.0,
        liquidity_weight=0.0,
    )

    pairs = make_items()

    contracts = [
        contract
        for contract, _ in pairs
    ]

    valuations = [
        valuation
        for _, valuation in pairs
    ]

    result = engine.rank_from_result(
        contracts=contracts,
        valuations=valuations,
        top_n=1,
    )

    assert result.total_count == 1
    assert len(result.items) == 1


def test_rank_from_result_handles_empty_data() -> None:
    """rank_from_result should handle empty input."""

    engine = MarketRankingEngine()

    result = engine.rank_from_result(
        contracts=[],
        valuations=[],
    )

    assert result.items == ()
    assert result.total_count == 0


def test_rank_preserves_contract_and_valuation() -> None:
    """Ranking should preserve original objects."""

    engine = MarketRankingEngine()

    contract = make_contract()

    valuation = make_valuation()

    result = engine.rank(
        [
            (
                contract,
                valuation,
            )
        ]
    )

    assert result.items[0].contract is contract
    assert result.items[0].valuation is valuation