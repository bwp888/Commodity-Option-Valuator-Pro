"""
Commodity Option Valuator Pro
=============================

Scanner Comprehensive Evaluator Boundary Tests.

These tests verify boundary behavior against the
existing production contract locked by
test_scanner_comprehensive_evaluator_contract.py.

They do NOT modify production behavior.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from core.comprehensive_evaluation import (
    ComprehensiveDecision,
)
from core.scanner_batch_valuation import (
    BatchValuationResult,
)
from core.scanner_comprehensive_evaluation import (
    ScannerComprehensiveEvaluator,
    ScannerEvaluationItem,
    ScannerEvaluationResult,
)

from tests.test_scanner_comprehensive_evaluator_contract import (
    make_batch_item,
    make_evaluation,
    make_evaluation_item,
    make_result,
)


# ==========================================================
# ScannerComprehensiveEvaluator.evaluate_item
# ==========================================================


def test_evaluate_item_delegates_to_existing_evaluator() -> None:
    batch_item = make_batch_item()

    evaluation = make_evaluation(
        symbol=batch_item.symbol,
    )

    evaluator = Mock()
    evaluator.evaluate.return_value = evaluation

    scanner_evaluator = ScannerComprehensiveEvaluator(
        evaluator=evaluator,
    )

    result = scanner_evaluator.evaluate_item(
        batch_item,
    )

    evaluator.evaluate.assert_called_once_with(
        batch_item.result,
    )

    assert isinstance(
        result,
        ScannerEvaluationItem,
    )
    assert result.batch_item is batch_item
    assert result.evaluation is evaluation


def test_evaluate_item_rejects_invalid_input() -> None:
    scanner_evaluator = ScannerComprehensiveEvaluator()

    with pytest.raises(
        TypeError,
        match="item must be a BatchValuationItem",
    ):
        scanner_evaluator.evaluate_item(
            object(),  # type: ignore[arg-type]
        )


def test_evaluate_item_propagates_evaluator_exception() -> None:
    batch_item = make_batch_item()

    evaluator = Mock()
    evaluator.evaluate.side_effect = RuntimeError(
        "evaluation failed",
    )

    scanner_evaluator = ScannerComprehensiveEvaluator(
        evaluator=evaluator,
    )

    with pytest.raises(
        RuntimeError,
        match="evaluation failed",
    ):
        scanner_evaluator.evaluate_item(
            batch_item,
        )


# ==========================================================
# ScannerComprehensiveEvaluator.evaluate_items
# ==========================================================


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

    evaluator = Mock()

    evaluator.evaluate.side_effect = [
        make_evaluation(symbol="FIRST"),
        make_evaluation(symbol="SECOND"),
        make_evaluation(symbol="THIRD"),
    ]

    scanner_evaluator = ScannerComprehensiveEvaluator(
        evaluator=evaluator,
    )

    result = scanner_evaluator.evaluate_items(
        items,
    )

    assert result.symbols == (
        "FIRST",
        "SECOND",
        "THIRD",
    )


def test_evaluate_items_accepts_generator() -> None:
    items = (
        make_batch_item(symbol=symbol)
        for symbol in (
            "FIRST",
            "SECOND",
            "THIRD",
        )
    )

    evaluator = Mock()

    evaluator.evaluate.side_effect = [
        make_evaluation(symbol="FIRST"),
        make_evaluation(symbol="SECOND"),
        make_evaluation(symbol="THIRD"),
    ]

    scanner_evaluator = ScannerComprehensiveEvaluator(
        evaluator=evaluator,
    )

    result = scanner_evaluator.evaluate_items(
        items,
    )

    assert result.count == 3
    assert result.symbols == (
        "FIRST",
        "SECOND",
        "THIRD",
    )


def test_evaluate_items_empty_iterable_returns_empty_result() -> None:
    scanner_evaluator = ScannerComprehensiveEvaluator()

    result = scanner_evaluator.evaluate_items(
        (),
    )

    assert isinstance(
        result,
        ScannerEvaluationResult,
    )
    assert result.items == ()
    assert result.count == 0


# ==========================================================
# ScannerComprehensiveEvaluator.evaluate
# ==========================================================


def test_evaluate_delegates_to_batch_result_items() -> None:
    items = (
        make_batch_item(symbol="FIRST"),
        make_batch_item(symbol="SECOND"),
    )

    batch_result = BatchValuationResult(
        items=items,
    )

    evaluator = Mock()
    evaluator.evaluate.side_effect = [
        make_evaluation(symbol="FIRST"),
        make_evaluation(symbol="SECOND"),
    ]

    scanner_evaluator = ScannerComprehensiveEvaluator(
        evaluator=evaluator,
    )

    result = scanner_evaluator.evaluate(
        batch_result,
    )

    assert result.count == 2
    assert result.symbols == (
        "FIRST",
        "SECOND",
    )

    assert evaluator.evaluate.call_count == 2


def test_evaluate_rejects_invalid_batch_result() -> None:
    scanner_evaluator = ScannerComprehensiveEvaluator()

    with pytest.raises(
        TypeError,
        match="batch_result must be a BatchValuationResult",
    ):
        scanner_evaluator.evaluate(
            object(),  # type: ignore[arg-type]
        )


# ==========================================================
# ScannerComprehensiveEvaluator.evaluate_and_sort
# ==========================================================


def test_evaluate_and_sort_defaults_to_descending_score() -> None:
    items = (
        make_batch_item(symbol="LOW"),
        make_batch_item(symbol="HIGH"),
    )

    batch_result = BatchValuationResult(
        items=items,
    )

    evaluator = Mock()
    evaluator.evaluate.side_effect = [
        make_evaluation(
            symbol="LOW",
            score=60.0,
        ),
        make_evaluation(
            symbol="HIGH",
            score=90.0,
        ),
    ]

    scanner_evaluator = ScannerComprehensiveEvaluator(
        evaluator=evaluator,
    )

    result = scanner_evaluator.evaluate_and_sort(
        batch_result,
    )

    assert result.symbols == (
        "HIGH",
        "LOW",
    )


def test_evaluate_and_sort_can_sort_ascending() -> None:
    items = (
        make_batch_item(symbol="LOW"),
        make_batch_item(symbol="HIGH"),
    )

    batch_result = BatchValuationResult(
        items=items,
    )

    evaluator = Mock()
    evaluator.evaluate.side_effect = [
        make_evaluation(
            symbol="LOW",
            score=60.0,
        ),
        make_evaluation(
            symbol="HIGH",
            score=90.0,
        ),
    ]

    scanner_evaluator = ScannerComprehensiveEvaluator(
        evaluator=evaluator,
    )

    result = scanner_evaluator.evaluate_and_sort(
        batch_result,
        descending=False,
    )

    assert result.symbols == (
        "LOW",
        "HIGH",
    )

# ==========================================================
# ScannerEvaluationResult boundary behavior
# ==========================================================


def test_filter_decision_returns_matching_items_only() -> None:
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

    caution = make_evaluation_item(
        symbol="CAUTION",
        evaluation=make_evaluation(
            symbol="CAUTION",
            decision=ComprehensiveDecision.CAUTION,
        ),
    )

    result = make_result(
        [recommend, watch, caution],
    )

    filtered = result.filter_decision(
        ComprehensiveDecision.WATCH,
    )

    assert filtered == (watch,)
    assert isinstance(filtered, tuple)


def test_filter_score_without_boundaries_returns_all() -> None:
    items = (
        make_evaluation_item(
            symbol="LOW",
            evaluation=make_evaluation(
                symbol="LOW",
                score=10.0,
            ),
        ),
        make_evaluation_item(
            symbol="HIGH",
            evaluation=make_evaluation(
                symbol="HIGH",
                score=90.0,
            ),
        ),
    )

    result = make_result(items)

    filtered = result.filter_score()

    assert filtered == items


def test_filter_score_minimum_boundary_is_inclusive() -> None:
    boundary = make_evaluation_item(
        symbol="BOUNDARY",
        evaluation=make_evaluation(
            symbol="BOUNDARY",
            score=50.0,
        ),
    )

    result = make_result(
        [boundary],
    )

    filtered = result.filter_score(
        minimum_score=50.0,
    )

    assert filtered == (boundary,)


def test_filter_score_maximum_boundary_is_inclusive() -> None:
    boundary = make_evaluation_item(
        symbol="BOUNDARY",
        evaluation=make_evaluation(
            symbol="BOUNDARY",
            score=50.0,
        ),
    )

    result = make_result(
        [boundary],
    )

    filtered = result.filter_score(
        maximum_score=50.0,
    )

    assert filtered == (boundary,)


def test_filter_score_excludes_values_outside_range() -> None:
    low = make_evaluation_item(
        symbol="LOW",
        evaluation=make_evaluation(
            symbol="LOW",
            score=49.9,
        ),
    )

    inside = make_evaluation_item(
        symbol="INSIDE",
        evaluation=make_evaluation(
            symbol="INSIDE",
            score=50.0,
        ),
    )

    high = make_evaluation_item(
        symbol="HIGH",
        evaluation=make_evaluation(
            symbol="HIGH",
            score=50.1,
        ),
    )

    result = make_result(
        [low, inside, high],
    )

    filtered = result.filter_score(
        minimum_score=50.0,
        maximum_score=50.0,
    )

    assert filtered == (inside,)


def test_filter_score_rejects_reversed_boundaries() -> None:
    result = make_result()

    with pytest.raises(
        ValueError,
        match="minimum_score cannot be greater than maximum_score",
    ):
        result.filter_score(
            minimum_score=90.0,
            maximum_score=10.0,
        )


def test_filter_score_does_not_mutate_original_result() -> None:
    items = (
        make_evaluation_item(
            symbol="LOW",
            evaluation=make_evaluation(
                symbol="LOW",
                score=20.0,
            ),
        ),
        make_evaluation_item(
            symbol="HIGH",
            evaluation=make_evaluation(
                symbol="HIGH",
                score=80.0,
            ),
        ),
    )

    result = make_result(items)

    filtered = result.filter_score(
        minimum_score=50.0,
    )

    assert filtered == (items[1],)
    assert result.items == items


def test_sort_by_score_descending() -> None:
    low = make_evaluation_item(
        symbol="LOW",
        evaluation=make_evaluation(
            symbol="LOW",
            score=20.0,
        ),
    )

    high = make_evaluation_item(
        symbol="HIGH",
        evaluation=make_evaluation(
            symbol="HIGH",
            score=80.0,
        ),
    )

    result = make_result(
        [low, high],
    )

    sorted_result = result.sort_by_score(
        descending=True,
    )

    assert sorted_result.symbols == (
        "HIGH",
        "LOW",
    )


def test_sort_by_score_ascending() -> None:
    low = make_evaluation_item(
        symbol="LOW",
        evaluation=make_evaluation(
            symbol="LOW",
            score=20.0,
        ),
    )

    high = make_evaluation_item(
        symbol="HIGH",
        evaluation=make_evaluation(
            symbol="HIGH",
            score=80.0,
        ),
    )

    result = make_result(
        [low, high],
    )

    sorted_result = result.sort_by_score(
        descending=False,
    )

    assert sorted_result.symbols == (
        "LOW",
        "HIGH",
    )


def test_sort_by_score_does_not_mutate_original_result() -> None:
    low = make_evaluation_item(
        symbol="LOW",
        evaluation=make_evaluation(
            symbol="LOW",
            score=20.0,
        ),
    )

    high = make_evaluation_item(
        symbol="HIGH",
        evaluation=make_evaluation(
            symbol="HIGH",
            score=80.0,
        ),
    )

    result = make_result(
        [low, high],
    )

    sorted_result = result.sort_by_score()

    assert result.items == (
        low,
        high,
    )

    assert sorted_result.items == (
        high,
        low,
    )

    assert sorted_result is not result


def test_sort_by_volume_descending() -> None:
    low_volume = make_evaluation_item(
        symbol="LOW_VOLUME",
        volume=10,
    )

    high_volume = make_evaluation_item(
        symbol="HIGH_VOLUME",
        volume=100,
    )

    result = make_result(
        [low_volume, high_volume],
    )

    sorted_result = result.sort_by_volume(
        descending=True,
    )

    assert sorted_result.symbols == (
        "HIGH_VOLUME",
        "LOW_VOLUME",
    )


def test_sort_by_volume_ascending() -> None:
    low_volume = make_evaluation_item(
        symbol="LOW_VOLUME",
        volume=10,
    )

    high_volume = make_evaluation_item(
        symbol="HIGH_VOLUME",
        volume=100,
    )

    result = make_result(
        [low_volume, high_volume],
    )

    sorted_result = result.sort_by_volume(
        descending=False,
    )

    assert sorted_result.symbols == (
        "LOW_VOLUME",
        "HIGH_VOLUME",
    )


def test_sort_by_risk_defaults_to_lowest_first() -> None:
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
            risk_score=90.0,
        ),
    )

    result = make_result(
        [high_risk, low_risk],
    )

    sorted_result = result.sort_by_risk()

    assert sorted_result.symbols == (
        "LOW_RISK",
        "HIGH_RISK",
    )


def test_sort_by_risk_descending() -> None:
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
            risk_score=90.0,
        ),
    )

    result = make_result(
        [low_risk, high_risk],
    )

    sorted_result = result.sort_by_risk(
        descending=True,
    )

    assert sorted_result.symbols == (
        "HIGH_RISK",
        "LOW_RISK",
    )


def test_sorting_does_not_mutate_original_result() -> None:
    first = make_evaluation_item(
        symbol="FIRST",
        evaluation=make_evaluation(
            symbol="FIRST",
            score=20.0,
        ),
    )

    second = make_evaluation_item(
        symbol="SECOND",
        evaluation=make_evaluation(
            symbol="SECOND",
            score=80.0,
        ),
    )

    result = make_result(
        [first, second],
    )

    sorted_result = result.sort_by_score()

    assert result.items == (
        first,
        second,
    )

    assert sorted_result.items == (
        second,
        first,
    )


def test_by_underlying_groups_items() -> None:
    au_call = make_evaluation_item(
        symbol="AU_CALL",
        underlying="AU2608",
    )

    au_put = make_evaluation_item(
        symbol="AU_PUT",
        underlying="AU2608",
        option_type="PUT",
    )

    cu_call = make_evaluation_item(
        symbol="CU_CALL",
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


def test_recommendations_watches_and_cautions_are_partitioned() -> None:
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

    caution = make_evaluation_item(
        symbol="CAUTION",
        evaluation=make_evaluation(
            symbol="CAUTION",
            decision=ComprehensiveDecision.CAUTION,
        ),
    )

    result = make_result(
        [recommend, watch, caution],
    )

    assert result.recommendations == (
        recommend,
    )

    assert result.watches == (
        watch,
    )

    assert result.cautions == (
        caution,
    )


def test_best_returns_highest_score() -> None:
    low = make_evaluation_item(
        symbol="LOW",
        evaluation=make_evaluation(
            symbol="LOW",
            score=20.0,
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

    assert result.best is high


def test_best_returns_none_for_empty_result() -> None:
    result = make_result()

    assert result.best is None


def test_to_dict_preserves_item_count() -> None:
    items = (
        make_evaluation_item(
            symbol="FIRST",
        ),
        make_evaluation_item(
            symbol="SECOND",
        ),
    )

    result = make_result(items)

    data = result.to_dict()

    assert len(data) == len(items)


def test_to_dict_contains_nested_valuation_and_evaluation() -> None:
    item = make_evaluation_item()

    result = make_result(
        [item],
    )

    data = result.to_dict()

    assert len(data) == 1

    exported = data[0]

    assert exported["valuation"] == (
        item.valuation_result.to_dict()
    )

    assert exported["evaluation"] == (
        item.evaluation.to_dict()
    )
