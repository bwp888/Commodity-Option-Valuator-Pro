"""
Commodity Option Valuator Pro
=============================

Scanner Comprehensive Evaluator Contract Tests.

Commit 0035/0036 - Phase 1
--------------------------

Purpose
-------
Lock the existing production contract of
ScannerComprehensiveEvaluator before boundary testing.

Production contract
-------------------
The tested workflow is:

    OptionQuote
        ↓
    ScannerCandidate
        ↓
    BatchValuationItem
        ↓
    ComprehensiveEvaluationResult
        ↓
    ScannerEvaluationItem
        ↓
    ScannerEvaluationResult
        ↓
    ScannerComprehensiveEvaluator

Important
---------
These tests are written against the existing production
constructors and properties.

They do NOT redesign:

- OptionQuote
- ScannerCandidate
- BatchValuationItem
- BatchValuationResult
- ComprehensiveEvaluationResult
- ComprehensiveEvaluator
- ScannerEvaluationItem
- ScannerEvaluationResult
- ScannerComprehensiveEvaluator
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pytest

from core.comprehensive_evaluation import (
    ComprehensiveDecision,
    ComprehensiveEvaluationResult,
    EvaluationComponents,
    EvaluationReason,
)
from core.scanner_batch_valuation import (
    BatchValuationItem,
    BatchValuationResult,
)
from core.scanner_comprehensive_evaluation import (
    ScannerComprehensiveEvaluator,
    ScannerEvaluationItem,
    ScannerEvaluationResult,
)
from core.scanner_valuation_bridge import (
    ScannerCandidate,
)
from core.single_option_valuation import (
    SingleOptionValuationResult,
)
from data.option_chain import OptionQuote
from models.option import OptionType
from models.risk import RiskLevel


# ==========================================================
# Fixtures
# ==========================================================


def make_quote(
    *,
    symbol: str = "AU2608-C-968",
    underlying: str = "AU2608",
    option_type: str = "CALL",
    strike: float = 968.0,
    last_price: float = 15.0,
    volume: int = 100,
    open_interest: int = 200,
    implied_volatility: float | None = 0.20,
) -> OptionQuote:
    """
    Create an OptionQuote using the real production contract.

    OptionQuote lives in data.option_chain.
    """

    return OptionQuote(
        symbol=symbol,
        underlying=underlying,
        option_type=option_type,  # type: ignore[arg-type]
        strike=strike,
        last_price=last_price,
        bid_price=14.5,
        ask_price=15.5,
        volume=volume,
        open_interest=open_interest,
        implied_volatility=implied_volatility,
    )


def make_candidate(
    *,
    symbol: str = "AU2608-C-968",
    underlying: str = "AU2608",
    option_type: str = "CALL",
    strike: float = 968.0,
    last_price: float = 15.0,
    volume: int = 100,
    open_interest: int = 200,
    implied_volatility: float | None = 0.20,
) -> ScannerCandidate:
    """
    Create ScannerCandidate through the real production
    ScannerCandidate(quote=...) constructor.
    """

    quote = make_quote(
        symbol=symbol,
        underlying=underlying,
        option_type=option_type,
        strike=strike,
        last_price=last_price,
        volume=volume,
        open_interest=open_interest,
        implied_volatility=implied_volatility,
    )

    return ScannerCandidate(
        quote=quote,
    )


def make_valuation_result(
    *,
    symbol: str = "AU2608-C-968",
    current_option_price: float = 15.0,
    current_theoretical_price: float = 16.0,
    current_option_iv: float = 0.20,
    current_gamma: float = 0.01,
    current_theta: float = 0.01,
    target_theoretical_price: float = 24.0,
    taylor_first_order_price: float = 23.5,
    taylor_second_order_price: float = 23.8,
    current_futures_price: float = 900.0,
    target_futures_price: float = 930.0,
) -> SingleOptionValuationResult:
    """
    Create the real SingleOptionValuationResult contract.

    The ScannerComprehensiveEvaluator consumes the existing
    BatchValuationItem.result and delegates that result to
    ComprehensiveEvaluator.
    """

    return SingleOptionValuationResult(
        symbol=symbol,
        current_futures_price=current_futures_price,
        target_futures_price=target_futures_price,
        strike=968.0,
        current_option_price=current_option_price,
        current_option_iv=current_option_iv,
        target_option_iv=0.22,
        reference_volatility_current=0.20,
        reference_volatility_target=0.22,
        reference_volatility_change_percent=10.0,
        current_theoretical_price=current_theoretical_price,
        target_theoretical_price=target_theoretical_price,
        current_delta=0.50,
        current_gamma=current_gamma,
        current_theta=current_theta,
        target_delta=0.55,
        target_gamma=0.012,
        target_theta=0.011,
        taylor_first_order_price=taylor_first_order_price,
        taylor_second_order_price=taylor_second_order_price,
    )


def make_batch_item(
    *,
    symbol: str = "AU2608-C-968",
    underlying: str = "AU2608",
    option_type: str = "CALL",
    strike: float = 968.0,
    last_price: float = 15.0,
    volume: int = 100,
    open_interest: int = 200,
    implied_volatility: float | None = 0.20,
    valuation_result: SingleOptionValuationResult | None = None,
) -> BatchValuationItem:
    """
    Create BatchValuationItem using the real production
    BatchValuationItem(candidate=..., result=...) contract.
    """

    candidate = make_candidate(
        symbol=symbol,
        underlying=underlying,
        option_type=option_type,
        strike=strike,
        last_price=last_price,
        volume=volume,
        open_interest=open_interest,
        implied_volatility=implied_volatility,
    )

    result = valuation_result
    if result is None:
        result = make_valuation_result(
            symbol=symbol,
        )

    return BatchValuationItem(
        candidate=candidate,
        result=result,
    )


def make_components(
    *,
    valuation_score: float = 25.0,
    iv_score: float = 18.0,
    theta_score: float = 18.0,
    gamma_score: float = 14.0,
    taylor_score: float = 9.0,
) -> EvaluationComponents:
    """
    Create EvaluationComponents using the real production
    constructor.
    """

    return EvaluationComponents(
        valuation_score=valuation_score,
        iv_score=iv_score,
        theta_score=theta_score,
        gamma_score=gamma_score,
        taylor_score=taylor_score,
    )


def make_evaluation(
    *,
    symbol: str = "AU2608-C-968",
    decision: ComprehensiveDecision = (
        ComprehensiveDecision.WATCH
    ),
    score: float = 84.0,
    risk_score: float = 20.0,
    risk_level: RiskLevel = RiskLevel.MEDIUM,
    components: EvaluationComponents | None = None,
    reasons: tuple[EvaluationReason, ...] | None = None,
) -> ComprehensiveEvaluationResult:
    """
    Create ComprehensiveEvaluationResult through its complete
    production contract.

    ``components`` is intentionally supplied because it is a
    required production constructor argument.
    """

    if components is None:
        components = make_components()

    if reasons is None:
        reasons = (
            EvaluationReason(
                category="valuation",
                positive=True,
                message="市场价格低于理论价格，存在一定估值优势。",
            ),
            EvaluationReason(
                category="iv",
                positive=True,
                message="IV处于较低或合理区间。",
            ),
            EvaluationReason(
                category="risk",
                positive=True,
                message="综合风险处于可接受范围。",
            ),
        )

    return ComprehensiveEvaluationResult(
        symbol=symbol,
        decision=decision,
        score=score,
        risk_score=risk_score,
        risk_level=risk_level,
        components=components,
        reasons=reasons,
    )


def make_evaluation_item(
    *,
    symbol: str = "AU2608-C-968",
    underlying: str = "AU2608",
    option_type: str = "CALL",
    strike: float = 968.0,
    last_price: float = 15.0,
    volume: int = 100,
    open_interest: int = 200,
    implied_volatility: float | None = 0.20,
    valuation_result: SingleOptionValuationResult | None = None,
    evaluation: ComprehensiveEvaluationResult | None = None,
) -> ScannerEvaluationItem:
    """
    Build the complete production object chain.
    """

    batch_item = make_batch_item(
        symbol=symbol,
        underlying=underlying,
        option_type=option_type,
        strike=strike,
        last_price=last_price,
        volume=volume,
        open_interest=open_interest,
        implied_volatility=implied_volatility,
        valuation_result=valuation_result,
    )

    if evaluation is None:
        evaluation = make_evaluation(
            symbol=symbol,
        )

    return ScannerEvaluationItem(
        batch_item=batch_item,
        evaluation=evaluation,
    )


def make_result(
    items: Iterable[ScannerEvaluationItem] = (),
) -> ScannerEvaluationResult:
    """
    Create ScannerEvaluationResult using its real production
    tuple-based contract.
    """

    return ScannerEvaluationResult(
        items=tuple(items),
    )


# ==========================================================
# ScannerEvaluationItem
# ==========================================================


def test_evaluation_item_preserves_batch_item_identity() -> None:
    batch_item = make_batch_item()

    evaluation_item = ScannerEvaluationItem(
        batch_item=batch_item,
        evaluation=make_evaluation(),
    )

    assert evaluation_item.batch_item is batch_item


def test_evaluation_item_preserves_evaluation_identity() -> None:
    evaluation = make_evaluation()

    evaluation_item = ScannerEvaluationItem(
        batch_item=make_batch_item(),
        evaluation=evaluation,
    )

    assert evaluation_item.evaluation is evaluation


def test_evaluation_item_symbol_delegates_to_batch_item() -> None:
    batch_item = make_batch_item(
        symbol="AU2608-C-970",
    )

    item = ScannerEvaluationItem(
        batch_item=batch_item,
        evaluation=make_evaluation(
            symbol="AU2608-C-970",
        ),
    )

    assert item.symbol == batch_item.symbol


def test_evaluation_item_underlying_delegates_to_batch_item() -> None:
    batch_item = make_batch_item(
        underlying="CU2609",
    )

    item = ScannerEvaluationItem(
        batch_item=batch_item,
        evaluation=make_evaluation(),
    )

    assert item.underlying == batch_item.underlying


def test_evaluation_item_option_type_delegates_to_batch_item() -> None:
    batch_item = make_batch_item(
        option_type="PUT",
    )

    item = ScannerEvaluationItem(
        batch_item=batch_item,
        evaluation=make_evaluation(),
    )

    assert item.option_type == batch_item.option_type


def test_evaluation_item_strike_delegates_to_batch_item() -> None:
    batch_item = make_batch_item(
        strike=980.0,
    )

    item = ScannerEvaluationItem(
        batch_item=batch_item,
        evaluation=make_evaluation(),
    )

    assert item.strike == 980.0


def test_evaluation_item_volume_delegates_to_batch_item() -> None:
    batch_item = make_batch_item(
        volume=321,
    )

    item = ScannerEvaluationItem(
        batch_item=batch_item,
        evaluation=make_evaluation(),
    )

    assert item.volume == 321


def test_evaluation_item_open_interest_delegates_to_candidate() -> None:
    batch_item = make_batch_item(
        open_interest=654,
    )

    item = ScannerEvaluationItem(
        batch_item=batch_item,
        evaluation=make_evaluation(),
    )

    assert item.open_interest == 654


def test_evaluation_item_option_price_delegates_to_candidate() -> None:
    batch_item = make_batch_item(
        last_price=17.5,
    )

    item = ScannerEvaluationItem(
        batch_item=batch_item,
        evaluation=make_evaluation(),
    )

    assert item.option_price == 17.5


def test_evaluation_item_implied_volatility_delegates_to_candidate() -> None:
    batch_item = make_batch_item(
        implied_volatility=0.27,
    )

    item = ScannerEvaluationItem(
        batch_item=batch_item,
        evaluation=make_evaluation(),
    )

    assert item.implied_volatility == 0.27


def test_evaluation_item_none_implied_volatility_is_preserved() -> None:
    batch_item = make_batch_item(
        implied_volatility=None,
    )

    item = ScannerEvaluationItem(
        batch_item=batch_item,
        evaluation=make_evaluation(),
    )

    assert item.implied_volatility is None


def test_evaluation_item_decision_delegates_to_evaluation() -> None:
    evaluation = make_evaluation(
        decision=ComprehensiveDecision.RECOMMEND,
    )

    item = ScannerEvaluationItem(
        batch_item=make_batch_item(),
        evaluation=evaluation,
    )

    assert item.decision is evaluation.decision


def test_evaluation_item_score_delegates_to_evaluation() -> None:
    evaluation = make_evaluation(
        score=91.5,
    )

    item = ScannerEvaluationItem(
        batch_item=make_batch_item(),
        evaluation=evaluation,
    )

    assert item.score == 91.5


def test_evaluation_item_risk_score_delegates_to_evaluation() -> None:
    evaluation = make_evaluation(
        risk_score=37.5,
    )

    item = ScannerEvaluationItem(
        batch_item=make_batch_item(),
        evaluation=evaluation,
    )

    assert item.risk_score == 37.5


def test_evaluation_item_risk_level_delegates_to_evaluation() -> None:
    evaluation = make_evaluation(
        risk_level=RiskLevel.LOW,
    )

    item = ScannerEvaluationItem(
        batch_item=make_batch_item(),
        evaluation=evaluation,
    )

    assert item.risk_level is RiskLevel.LOW


def test_evaluation_item_reason_text_is_derived_from_evaluation() -> None:
    evaluation = make_evaluation()

    item = ScannerEvaluationItem(
        batch_item=make_batch_item(),
        evaluation=evaluation,
    )

    assert item.reason_text == evaluation.reason_text


def test_evaluation_item_reason_messages_are_derived_from_evaluation() -> None:
    evaluation = make_evaluation()

    item = ScannerEvaluationItem(
        batch_item=make_batch_item(),
        evaluation=evaluation,
    )

    assert item.reason_messages == evaluation.reason_messages


def test_evaluation_item_valuation_result_preserves_batch_result_identity() -> None:
    valuation_result = make_valuation_result()

    item = make_evaluation_item(
        valuation_result=valuation_result,
    )

    assert item.valuation_result is valuation_result
    assert item.batch_item.result is valuation_result


def test_evaluation_item_to_dict_contains_current_contract_keys() -> None:
    item = make_evaluation_item()

    data = item.to_dict()

    expected_keys = {
        "symbol",
        "underlying",
        "option_type",
        "strike",
        "volume",
        "open_interest",
        "option_price",
        "implied_volatility",
        "decision",
        "score",
        "risk_score",
        "risk_level",
        "reason_text",
        "reason_messages",
        "valuation",
        "evaluation",
    }

    assert expected_keys.issubset(
        data.keys()
    )


def test_evaluation_item_to_dict_uses_valuation_result_to_dict() -> None:
    valuation_result = make_valuation_result()

    item = make_evaluation_item(
        valuation_result=valuation_result,
    )

    data = item.to_dict()

    assert data["valuation"] == (
        valuation_result.to_dict()
    )


def test_evaluation_item_to_dict_uses_evaluation_to_dict() -> None:
    evaluation = make_evaluation()

    item = make_evaluation_item(
        evaluation=evaluation,
    )

    data = item.to_dict()

    assert data["evaluation"] == (
        evaluation.to_dict()
    )


# ==========================================================
# ScannerEvaluationResult
# ==========================================================


def test_evaluation_result_items_are_stored_as_tuple() -> None:
    item = make_evaluation_item()

    result = make_result(
        [item],
    )

    assert isinstance(
        result.items,
        tuple,
    )


def test_evaluation_result_count_matches_items() -> None:
    items = (
        make_evaluation_item(
            symbol="AU2608-C-968",
        ),
        make_evaluation_item(
            symbol="AU2608-C-970",
        ),
    )

    result = make_result(items)

    assert result.count == 2


def test_evaluation_result_symbols_preserve_item_order() -> None:
    items = (
        make_evaluation_item(
            symbol="AU2608-C-968",
        ),
        make_evaluation_item(
            symbol="AU2608-C-970",
        ),
        make_evaluation_item(
            symbol="AU2608-C-972",
        ),
    )

    result = make_result(items)

    assert result.symbols == (
        "AU2608-C-968",
        "AU2608-C-970",
        "AU2608-C-972",
    )


def test_evaluation_result_recommendations_filter_decision() -> None:
    recommend = make_evaluation_item(
        symbol="RECOMMEND",
        evaluation=make_evaluation(
            symbol="RECOMMEND",
            decision=ComprehensiveDecision.RECOMMEND,
        ),
    )

    watch = make_evaluation_item(
        symbol="WATCH",
        evaluation=make_evaluation(
            symbol="WATCH",
            decision=ComprehensiveDecision.WATCH,
        ),
    )

    result = make_result(
        [recommend, watch],
    )

    assert result.recommendations == (
        recommend,
    )


def test_evaluation_result_watches_filter_decision() -> None:
    recommend = make_evaluation_item(
        symbol="RECOMMEND",
        evaluation=make_evaluation(
            symbol="RECOMMEND",
            decision=ComprehensiveDecision.RECOMMEND,
        ),
    )

    watch = make_evaluation_item(
        symbol="WATCH",
        evaluation=make_evaluation(
            symbol="WATCH",
            decision=ComprehensiveDecision.WATCH,
        ),
    )

    result = make_result(
        [recommend, watch],
    )

    assert result.watches == (
        watch,
    )


def test_evaluation_result_cautions_filter_decision() -> None:
    caution = make_evaluation_item(
        symbol="CAUTION",
        evaluation=make_evaluation(
            symbol="CAUTION",
            decision=ComprehensiveDecision.CAUTION,
        ),
    )

    watch = make_evaluation_item(
        symbol="WATCH",
        evaluation=make_evaluation(
            symbol="WATCH",
            decision=ComprehensiveDecision.WATCH,
        ),
    )

    result = make_result(
        [caution, watch],
    )

    assert result.cautions == (
        caution,
    )


def test_evaluation_result_decision_counts_match_filtered_results() -> None:
    items = (
        make_evaluation_item(
            symbol="R1",
            evaluation=make_evaluation(
                symbol="R1",
                decision=ComprehensiveDecision.RECOMMEND,
            ),
        ),
        make_evaluation_item(
            symbol="R2",
            evaluation=make_evaluation(
                symbol="R2",
                decision=ComprehensiveDecision.RECOMMEND,
            ),
        ),
        make_evaluation_item(
            symbol="W1",
            evaluation=make_evaluation(
                symbol="W1",
                decision=ComprehensiveDecision.WATCH,
            ),
        ),
        make_evaluation_item(
            symbol="C1",
            evaluation=make_evaluation(
                symbol="C1",
                decision=ComprehensiveDecision.CAUTION,
            ),
        ),
    )

    result = make_result(items)

    assert result.recommendation_count == 2
    assert result.watch_count == 1
    assert result.caution_count == 1


def test_evaluation_result_best_returns_highest_score_item() -> None:
    low = make_evaluation_item(
        symbol="LOW",
        evaluation=make_evaluation(
            symbol="LOW",
            score=61.0,
        ),
    )

    high = make_evaluation_item(
        symbol="HIGH",
        evaluation=make_evaluation(
            symbol="HIGH",
            score=92.0,
        ),
    )

    middle = make_evaluation_item(
        symbol="MIDDLE",
        evaluation=make_evaluation(
            symbol="MIDDLE",
            score=75.0,
        ),
    )

    result = make_result(
        [low, high, middle],
    )

    assert result.best is high


def test_evaluation_result_best_returns_none_for_empty_result() -> None:
    result = make_result()

    assert result.best is None


def test_evaluation_result_by_underlying_groups_matching_items() -> None:
    au_call = make_evaluation_item(
        symbol="AU-C",
        underlying="AU2608",
    )

    au_put = make_evaluation_item(
        symbol="AU-P",
        underlying="AU2608",
        option_type="PUT",
    )

    cu_call = make_evaluation_item(
        symbol="CU-C",
        underlying="CU2609",
    )

    result = make_result(
        [au_call, au_put, cu_call],
    )

    grouped = result.by_underlying()

    assert grouped["AU2608"] == [
        au_call,
        au_put,
    ]

    assert grouped["CU2609"] == [
        cu_call,
    ]


def test_evaluation_result_filter_decision_returns_new_tuple() -> None:
    item = make_evaluation_item(
        evaluation=make_evaluation(
            decision=ComprehensiveDecision.WATCH,
        ),
    )

    result = make_result(
        [item],
    )

    filtered = result.filter_decision(
        ComprehensiveDecision.WATCH,
    )

    assert filtered == (item,)
    assert isinstance(
        filtered,
        tuple,
    )


def test_evaluation_result_filter_score_returns_matching_items() -> None:
    low = make_evaluation_item(
        symbol="LOW",
        evaluation=make_evaluation(
            symbol="LOW",
            score=55.0,
        ),
    )

    middle = make_evaluation_item(
        symbol="MIDDLE",
        evaluation=make_evaluation(
            symbol="MIDDLE",
            score=72.0,
        ),
    )

    high = make_evaluation_item(
        symbol="HIGH",
        evaluation=make_evaluation(
            symbol="HIGH",
            score=91.0,
        ),
    )

    result = make_result(
        [low, middle, high],
    )

    filtered = result.filter_score(
        minimum_score=60.0,
        maximum_score=80.0,
    )

    assert filtered == (
        middle,
    )


def test_evaluation_result_filter_score_without_bounds_returns_all() -> None:
    items = (
        make_evaluation_item(
            symbol="A",
            evaluation=make_evaluation(
                symbol="A",
                score=55.0,
            ),
        ),
        make_evaluation_item(
            symbol="B",
            evaluation=make_evaluation(
                symbol="B",
                score=85.0,
            ),
        ),
    )

    result = make_result(items)

    assert result.filter_score() == items


def test_evaluation_result_filter_score_rejects_reversed_bounds() -> None:
    result = make_result(
        [
            make_evaluation_item(),
        ],
    )

    with pytest.raises(
        ValueError,
        match=(
            "minimum_score cannot be greater "
            "than maximum_score"
        ),
    ):
        result.filter_score(
            minimum_score=90.0,
            maximum_score=80.0,
        )


def test_sort_by_score_descending_preserves_original_result() -> None:
    low = make_evaluation_item(
        symbol="LOW",
        evaluation=make_evaluation(
            symbol="LOW",
            score=60.0,
        ),
    )

    high = make_evaluation_item(
        symbol="HIGH",
        evaluation=make_evaluation(
            symbol="HIGH",
            score=90.0,
        ),
    )

    result = make_result(
        [low, high],
    )

    sorted_result = result.sort_by_score()

    assert sorted_result.items == (
        high,
        low,
    )

    assert result.items == (
        low,
        high,
    )

    assert sorted_result is not result


def test_sort_by_score_ascending() -> None:
    low = make_evaluation_item(
        symbol="LOW",
        evaluation=make_evaluation(
            symbol="LOW",
            score=60.0,
        ),
    )

    high = make_evaluation_item(
        symbol="HIGH",
        evaluation=make_evaluation(
            symbol="HIGH",
            score=90.0,
        ),
    )

    result = make_result(
        [high, low],
    )

    sorted_result = result.sort_by_score(
        descending=False,
    )

    assert sorted_result.items == (
        low,
        high,
    )


def test_sort_by_volume_returns_new_result() -> None:
    low_volume = make_evaluation_item(
        symbol="LOW_VOLUME",
        volume=10,
    )

    high_volume = make_evaluation_item(
        symbol="HIGH_VOLUME",
        volume=1000,
    )

    result = make_result(
        [low_volume, high_volume],
    )

    sorted_result = result.sort_by_volume()

    assert sorted_result.items == (
        high_volume,
        low_volume,
    )

    assert result.items == (
        low_volume,
        high_volume,
    )


def test_sort_by_risk_returns_new_result() -> None:
    low_risk = make_evaluation_item(
        symbol="LOW_RISK",
        evaluation=make_evaluation(
            symbol="LOW_RISK",
            risk_score=10.0,
        ),
    )

    high_risk = make_evaluation_item(
        symbol="HIGH_RISK",
        evaluation=make_evaluation(
            symbol="HIGH_RISK",
            risk_score=80.0,
        ),
    )

    result = make_result(
        [high_risk, low_risk],
    )

    sorted_result = result.sort_by_risk()

    assert sorted_result.items == (
        low_risk,
        high_risk,
    )


def test_evaluation_result_to_dict_contains_items_and_count() -> None:
    item = make_evaluation_item()

    result = make_result(
        [item],
    )

    data = result.to_dict()

    assert isinstance(
        data,
        list,
    )

    assert len(data) == 1
    assert data[0]["symbol"] == item.symbol


# ==========================================================
# ScannerComprehensiveEvaluator
# ==========================================================


def test_scanner_comprehensive_evaluator_can_inject_evaluator() -> None:
    class StubEvaluator:
        def evaluate(
            self,
            valuation_result: object,
        ) -> ComprehensiveEvaluationResult:
            return make_evaluation(
                symbol=valuation_result.symbol,  # type: ignore[attr-defined]
            )

    evaluator = StubEvaluator()

    scanner_evaluator = ScannerComprehensiveEvaluator(
        evaluator=evaluator,  # type: ignore[arg-type]
    )

    assert scanner_evaluator.evaluator is evaluator


def test_evaluate_item_delegates_to_existing_comprehensive_evaluator() -> None:
    valuation_result = make_valuation_result()

    batch_item = make_batch_item(
        valuation_result=valuation_result,
    )

    expected = make_evaluation(
        symbol=valuation_result.symbol,
    )

    class StubEvaluator:
        def __init__(self) -> None:
            self.calls: list[object] = []

        def evaluate(
            self,
            value: object,
        ) -> ComprehensiveEvaluationResult:
            self.calls.append(value)
            return expected

    stub = StubEvaluator()

    scanner_evaluator = ScannerComprehensiveEvaluator(
        evaluator=stub,  # type: ignore[arg-type]
    )

    result = scanner_evaluator.evaluate_item(
        batch_item,
    )

    assert stub.calls == [
        valuation_result,
    ]

    assert result.evaluation is expected


def test_evaluate_item_returns_scanner_evaluation_item() -> None:
    batch_item = make_batch_item()

    scanner_evaluator = ScannerComprehensiveEvaluator()

    result = scanner_evaluator.evaluate_item(
        batch_item,
    )

    assert isinstance(
        result,
        ScannerEvaluationItem,
    )


def test_evaluate_item_preserves_batch_item_identity() -> None:
    batch_item = make_batch_item()

    scanner_evaluator = ScannerComprehensiveEvaluator()

    result = scanner_evaluator.evaluate_item(
        batch_item,
    )

    assert result.batch_item is batch_item


def test_evaluate_item_preserves_delegated_evaluation_identity() -> None:
    expected = make_evaluation()

    class StubEvaluator:
        def evaluate(
            self,
            value: object,
        ) -> ComprehensiveEvaluationResult:
            return expected

    scanner_evaluator = ScannerComprehensiveEvaluator(
        evaluator=StubEvaluator(),  # type: ignore[arg-type]
    )

    result = scanner_evaluator.evaluate_item(
        make_batch_item(),
    )

    assert result.evaluation is expected


def test_evaluate_items_accepts_list() -> None:
    items = [
        make_batch_item(
            symbol="A",
        ),
        make_batch_item(
            symbol="B",
        ),
    ]

    scanner_evaluator = ScannerComprehensiveEvaluator()

    result = scanner_evaluator.evaluate_items(
        items,
    )

    assert result.count == 2


def test_evaluate_items_accepts_tuple() -> None:
    items = (
        make_batch_item(
            symbol="A",
        ),
        make_batch_item(
            symbol="B",
        ),
    )

    scanner_evaluator = ScannerComprehensiveEvaluator()

    result = scanner_evaluator.evaluate_items(
        items,
    )

    assert result.count == 2


def test_evaluate_items_accepts_generator() -> None:
    items = (
        make_batch_item(
            symbol="A",
        ),
        make_batch_item(
            symbol="B",
        ),
    )

    scanner_evaluator = ScannerComprehensiveEvaluator()

    result = scanner_evaluator.evaluate_items(
        item
        for item in items
    )

    assert result.count == 2


def test_evaluate_items_returns_tuple_items() -> None:
    items = [
        make_batch_item(),
    ]

    scanner_evaluator = ScannerComprehensiveEvaluator()

    result = scanner_evaluator.evaluate_items(
        items,
    )

    assert isinstance(
        result.items,
        tuple,
    )


def test_evaluate_items_preserves_input_order() -> None:
    items = [
        make_batch_item(
            symbol="FIRST",
        ),
        make_batch_item(
            symbol="SECOND",
        ),
        make_batch_item(
            symbol="THIRD",
        ),
    ]

    scanner_evaluator = ScannerComprehensiveEvaluator()

    result = scanner_evaluator.evaluate_items(
        items,
    )

    assert result.symbols == (
        "FIRST",
        "SECOND",
        "THIRD",
    )


def test_evaluate_items_delegates_every_item() -> None:
    items = [
        make_batch_item(
            symbol="A",
        ),
        make_batch_item(
            symbol="B",
        ),
        make_batch_item(
            symbol="C",
        ),
    ]

    class StubEvaluator:
        def __init__(self) -> None:
            self.calls: list[object] = []

        def evaluate(
            self,
            value: object,
        ) -> ComprehensiveEvaluationResult:
            self.calls.append(value)
            return make_evaluation(
                symbol=value.symbol,  # type: ignore[attr-defined]
            )

    stub = StubEvaluator()

    scanner_evaluator = ScannerComprehensiveEvaluator(
        evaluator=stub,  # type: ignore[arg-type]
    )

    result = scanner_evaluator.evaluate_items(
        items,
    )

    assert len(stub.calls) == 3

    assert stub.calls == [
        item.result
        for item in items
    ]

    assert result.symbols == (
        "A",
        "B",
        "C",
    )


def test_evaluate_empty_iterable_returns_empty_result() -> None:
    scanner_evaluator = ScannerComprehensiveEvaluator()

    result = scanner_evaluator.evaluate_items(
        [],
    )

    assert isinstance(
        result,
        ScannerEvaluationResult,
    )

    assert result.items == ()
    assert result.count == 0


def test_evaluate_accepts_batch_valuation_result() -> None:
    items = (
        make_batch_item(
            symbol="A",
        ),
        make_batch_item(
            symbol="B",
        ),
    )

    batch_result = BatchValuationResult(
        items=items,
    )

    scanner_evaluator = ScannerComprehensiveEvaluator()

    result = scanner_evaluator.evaluate(
        batch_result,
    )

    assert isinstance(
        result,
        ScannerEvaluationResult,
    )

    assert result.count == 2


def test_evaluate_uses_batch_result_items() -> None:
    first = make_batch_item(
        symbol="FIRST",
    )

    second = make_batch_item(
        symbol="SECOND",
    )

    batch_result = BatchValuationResult(
        items=(
            first,
            second,
        ),
    )

    scanner_evaluator = ScannerComprehensiveEvaluator()

    result = scanner_evaluator.evaluate(
        batch_result,
    )

    assert result.items[0].batch_item is first
    assert result.items[1].batch_item is second


def test_evaluate_preserves_batch_result_order() -> None:
    items = (
        make_batch_item(
            symbol="FIRST",
        ),
        make_batch_item(
            symbol="SECOND",
        ),
        make_batch_item(
            symbol="THIRD",
        ),
    )

    batch_result = BatchValuationResult(
        items=items,
    )

    scanner_evaluator = ScannerComprehensiveEvaluator()

    result = scanner_evaluator.evaluate(
        batch_result,
    )

    assert result.symbols == (
        "FIRST",
        "SECOND",
        "THIRD",
    )


def test_evaluate_empty_batch_result_returns_empty_result() -> None:
    batch_result = BatchValuationResult(
        items=(),
    )

    scanner_evaluator = ScannerComprehensiveEvaluator()

    result = scanner_evaluator.evaluate(
        batch_result,
    )

    assert result.items == ()
    assert result.count == 0


def test_evaluate_and_sort_delegates_to_evaluate_then_score_sort() -> None:
    first = make_batch_item(
        symbol="FIRST",
    )

    second = make_batch_item(
        symbol="SECOND",
    )

    batch_result = BatchValuationResult(
        items=(
            first,
            second,
        ),
    )

    class StubEvaluator:
        def evaluate(
            self,
            value: object,
        ) -> ComprehensiveEvaluationResult:
            if value.symbol == "FIRST":  # type: ignore[attr-defined]
                return make_evaluation(
                    symbol="FIRST",
                    score=60.0,
                )

            return make_evaluation(
                symbol="SECOND",
                score=90.0,
            )

    scanner_evaluator = ScannerComprehensiveEvaluator(
        evaluator=StubEvaluator(),  # type: ignore[arg-type]
    )

    result = scanner_evaluator.evaluate_and_sort(
        batch_result,
    )

    assert result.symbols == (
        "SECOND",
        "FIRST",
    )


def test_evaluate_and_sort_defaults_to_descending_score() -> None:
    first = make_batch_item(
        symbol="FIRST",
    )

    second = make_batch_item(
        symbol="SECOND",
    )

    batch_result = BatchValuationResult(
        items=(
            first,
            second,
        ),
    )

    class StubEvaluator:
        def evaluate(
            self,
            value: object,
        ) -> ComprehensiveEvaluationResult:
            if value.symbol == "FIRST":  # type: ignore[attr-defined]
                return make_evaluation(
                    symbol="FIRST",
                    score=50.0,
                )

            return make_evaluation(
                symbol="SECOND",
                score=95.0,
            )

    scanner_evaluator = ScannerComprehensiveEvaluator(
        evaluator=StubEvaluator(),  # type: ignore[arg-type]
    )

    result = scanner_evaluator.evaluate_and_sort(
        batch_result,
    )

    assert result.symbols == (
        "SECOND",
        "FIRST",
    )


def test_evaluate_and_sort_can_sort_ascending() -> None:
    first = make_batch_item(
        symbol="FIRST",
    )

    second = make_batch_item(
        symbol="SECOND",
    )

    batch_result = BatchValuationResult(
        items=(
            first,
            second,
        ),
    )

    class StubEvaluator:
        def evaluate(
            self,
            value: object,
        ) -> ComprehensiveEvaluationResult:
            if value.symbol == "FIRST":  # type: ignore[attr-defined]
                return make_evaluation(
                    symbol="FIRST",
                    score=50.0,
                )

            return make_evaluation(
                symbol="SECOND",
                score=95.0,
            )

    scanner_evaluator = ScannerComprehensiveEvaluator(
        evaluator=StubEvaluator(),  # type: ignore[arg-type]
    )

    result = scanner_evaluator.evaluate_and_sort(
        batch_result,
        descending=False,
    )

    assert result.symbols == (
        "FIRST",
        "SECOND",
    )


# ==========================================================
# Contract rejection boundaries
# ==========================================================


def test_evaluate_item_rejects_invalid_item_type_with_existing_type_error() -> None:
    scanner_evaluator = ScannerComprehensiveEvaluator()

    with pytest.raises(
        TypeError,
        match="item must be a BatchValuationItem",
    ):
        scanner_evaluator.evaluate_item(
            object(),  # type: ignore[arg-type]
        )


def test_evaluate_rejects_invalid_batch_result_type_with_existing_type_error() -> None:
    scanner_evaluator = ScannerComprehensiveEvaluator()

    with pytest.raises(
        TypeError,
        match="batch_result must be a BatchValuationResult",
    ):
        scanner_evaluator.evaluate(
            object(),  # type: ignore[arg-type]
        )