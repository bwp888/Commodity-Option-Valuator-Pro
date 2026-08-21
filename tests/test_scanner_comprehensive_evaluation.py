"""
Commodity Option Valuator Pro
=============================

Scanner Comprehensive Evaluation UI Tests.

Commit 0029-A
-------------
Verify that ScannerPage can consume the existing
BatchValuationResult / ComprehensiveEvaluationResult boundary
without performing valuation itself.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from core.scanner_batch_valuation import BatchValuationResult
from models.risk import RiskLevel
from ui.scanner import ScannerPage


def make_batch_result(
    *,
    with_evaluation: bool = True,
) -> BatchValuationResult:
    """Build a lightweight batch-result fixture."""

    evaluation = None

    if with_evaluation:
        evaluation = SimpleNamespace(
            score=86.5,
            decision=SimpleNamespace(value="RECOMMEND"),
            risk_level=RiskLevel.MEDIUM,
            reason_text="市场价格低于理论价格，存在一定估值优势。",
        )

    result = SimpleNamespace(
        current_theoretical_price=125.123456,
        comprehensive_evaluation=evaluation,
    )

    item = SimpleNamespace(
        symbol="SR609C5600",
        option_type="CALL",
        volume=1234,
        result=result,
    )

    return BatchValuationResult(
        items=(item,),
    )


def test_build_valuation_display_rows_contains_comprehensive_evaluation():
    """Existing comprehensive evaluation is exposed to the UI row."""

    batch_result = make_batch_result()

    rows = ScannerPage.build_valuation_display_rows(
        batch_result
    )

    assert len(rows) == 1

    row = rows[0]

    assert row["symbol"] == "SR609C5600"
    assert row["option_type"] == "CALL"
    assert row["volume"] == "1234"
    assert row["theoretical_price"] == "125.123456"
    assert row["score"] == "86.50"
    assert row["decision"] == "RECOMMEND"
    assert row["risk_level"] == "MEDIUM"
    assert "估值优势" in row["reason"]


def test_build_valuation_display_rows_handles_missing_evaluation():
    """UI must remain safe if an old result has no comprehensive evaluation."""

    batch_result = make_batch_result(
        with_evaluation=False
    )

    rows = ScannerPage.build_valuation_display_rows(
        batch_result
    )

    assert len(rows) == 1

    row = rows[0]

    assert row["score"] == "--"
    assert row["decision"] == "--"
    assert row["risk_level"] == "--"
    assert row["reason"] == "暂无综合评价结果。"


def test_build_valuation_display_rows_rejects_invalid_input():
    """The presentation boundary must reject an invalid result type."""

    with pytest.raises(TypeError):
        ScannerPage.build_valuation_display_rows(
            object()  # type: ignore[arg-type]
        )
