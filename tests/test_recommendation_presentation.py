"""
Commodity Option Valuator Pro
=============================

Tests for Recommendation Presentation Layer.

Commit 0020
-----------

Author : Simon
Version : 0.6.2
"""

from __future__ import annotations

import pytest

from core.recommendation_engine import (
    Recommendation,
    RecommendationAction,
    RecommendationLevel,
    RecommendationResult,
)

from core.recommendation_presentation import (
    ActionDisplay,
    LevelDisplay,
    PresentationAction,
    PresentationLevel,
    RecommendationPresentation,
    RecommendationPresentationResult,
    RecommendationPresenter,
    RecommendationSummary,
)

from core.recommendation_workflow import (
    RecommendationWorkflowResult,
)

from core.opportunity_analyzer import (
    OpportunityAnalysisResult,
)


# ==========================================================
# Test Helpers
# ==========================================================


def make_recommendation(
    symbol: str = "TEST-C-100",
    action: RecommendationAction = RecommendationAction.BUY,
    level: RecommendationLevel = RecommendationLevel.A,
    score: float = 3.0,
    risk_score: float = 2.0,
    reason: str = "test reason",
) -> Recommendation:
    """Create a deterministic recommendation."""

    return Recommendation(
        symbol=symbol,
        action=action,
        level=level,
        score=score,
        risk_score=risk_score,
        reason=reason,
    )


def make_result(
    recommendations: tuple[Recommendation, ...],
) -> RecommendationResult:
    """Create a recommendation result."""

    return RecommendationResult(
        recommendations=recommendations,
        total_count=len(recommendations),
    )


# ==========================================================
# Import
# ==========================================================


def test_presenter_import() -> None:
    """Presenter should be importable."""

    presenter = RecommendationPresenter()

    assert presenter is not None


# ==========================================================
# Enum Stability
# ==========================================================


def test_presentation_action_values_are_stable() -> None:
    """Presentation action values should remain stable."""

    assert PresentationAction.BUY.value == "BUY"
    assert PresentationAction.SELL.value == "SELL"
    assert PresentationAction.WATCH.value == "WATCH"
    assert PresentationAction.REJECT.value == "REJECT"


def test_presentation_level_values_are_stable() -> None:
    """Presentation level values should remain stable."""

    assert PresentationLevel.A.value == "A"
    assert PresentationLevel.B.value == "B"
    assert PresentationLevel.C.value == "C"
    assert PresentationLevel.D.value == "D"


# ==========================================================
# Action Display
# ==========================================================


@pytest.mark.parametrize(
    "action, expected_title",
    [
        (RecommendationAction.BUY, "BUY"),
        (RecommendationAction.SELL, "SELL"),
        (RecommendationAction.WATCH, "WATCH"),
        (RecommendationAction.REJECT, "REJECT"),
    ],
)
def test_action_display(
    action: RecommendationAction,
    expected_title: str,
) -> None:
    """Each action should have stable display metadata."""

    display = RecommendationPresenter.action_display(
        action
    )

    assert isinstance(
        display,
        ActionDisplay,
    )

    assert display.title == expected_title
    assert display.action.value == expected_title
    assert display.description


def test_action_display_accepts_string() -> None:
    """Action display should accept strings."""

    display = RecommendationPresenter.action_display(
        "buy"
    )

    assert display.action == PresentationAction.BUY
    assert display.title == "BUY"


def test_action_display_rejects_invalid_action() -> None:
    """Invalid action should be rejected."""

    with pytest.raises(
        ValueError,
        match="invalid recommendation action",
    ):
        RecommendationPresenter.action_display(
            "INVALID"
        )


# ==========================================================
# Level Display
# ==========================================================


@pytest.mark.parametrize(
    "level, expected_title",
    [
        (RecommendationLevel.A, "A"),
        (RecommendationLevel.B, "B"),
        (RecommendationLevel.C, "C"),
        (RecommendationLevel.D, "D"),
    ],
)
def test_level_display(
    level: RecommendationLevel,
    expected_title: str,
) -> None:
    """Each level should have stable display metadata."""

    display = RecommendationPresenter.level_display(
        level
    )

    assert isinstance(
        display,
        LevelDisplay,
    )

    assert display.title == expected_title
    assert display.level.value == expected_title
    assert display.description


def test_level_display_accepts_string() -> None:
    """Level display should accept strings."""

    display = RecommendationPresenter.level_display(
        "a"
    )

    assert display.level == PresentationLevel.A
    assert display.title == "A"


def test_level_display_rejects_invalid_level() -> None:
    """Invalid level should be rejected."""

    with pytest.raises(
        ValueError,
        match="invalid recommendation level",
    ):
        RecommendationPresenter.level_display(
            "INVALID"
        )


# ==========================================================
# Single Presentation
# ==========================================================


def test_present_buy_recommendation() -> None:
    """BUY recommendation should be presented correctly."""

    presenter = RecommendationPresenter()

    recommendation = make_recommendation(
        action=RecommendationAction.BUY,
        level=RecommendationLevel.A,
    )

    result = presenter.present(
        recommendation
    )

    assert isinstance(
        result,
        RecommendationPresentation,
    )

    assert result.symbol == "TEST-C-100"
    assert result.action == PresentationAction.BUY
    assert result.action_title == "BUY"
    assert result.level == PresentationLevel.A
    assert result.level_title == "A"
    assert result.score == 3.0
    assert result.risk_score == 2.0
    assert result.reason == "test reason"
    assert result.risk_warning is None


def test_present_sell_recommendation() -> None:
    """SELL recommendation should be presented correctly."""

    presenter = RecommendationPresenter()

    recommendation = make_recommendation(
        action=RecommendationAction.SELL,
        level=RecommendationLevel.A,
    )

    result = presenter.present(
        recommendation
    )

    assert result.action == PresentationAction.SELL
    assert result.action_title == "SELL"


def test_present_watch_recommendation() -> None:
    """WATCH recommendation should be presented correctly."""

    presenter = RecommendationPresenter()

    recommendation = make_recommendation(
        action=RecommendationAction.WATCH,
        level=RecommendationLevel.B,
        score=1.0,
    )

    result = presenter.present(
        recommendation
    )

    assert result.action == PresentationAction.WATCH
    assert result.level == PresentationLevel.B
    assert result.action_description
    assert result.level_description


def test_present_reject_recommendation() -> None:
    """REJECT recommendation should be presented correctly."""

    presenter = RecommendationPresenter()

    recommendation = make_recommendation(
        action=RecommendationAction.REJECT,
        level=RecommendationLevel.C,
        score=-1.0,
    )

    result = presenter.present(
        recommendation
    )

    assert result.action == PresentationAction.REJECT
    assert result.level == PresentationLevel.C
    assert result.risk_warning is not None


def test_present_reject_high_risk_warning() -> None:
    """High-risk rejection should expose a warning."""

    presenter = RecommendationPresenter()

    recommendation = make_recommendation(
        action=RecommendationAction.REJECT,
        level=RecommendationLevel.D,
        score=5.0,
        risk_score=8.0,
    )

    result = presenter.present(
        recommendation
    )

    assert result.risk_warning is not None
    assert "High risk" in result.risk_warning


def test_present_active_high_risk_warning() -> None:
    """Active recommendation with elevated risk should warn."""

    presenter = RecommendationPresenter()

    recommendation = make_recommendation(
        action=RecommendationAction.BUY,
        level=RecommendationLevel.A,
        score=5.0,
        risk_score=6.0,
    )

    result = presenter.present(
        recommendation
    )

    assert result.risk_warning is not None
    assert "Risk alert" in result.risk_warning


def test_present_medium_risk_warning() -> None:
    """Moderate elevated risk should expose a notice."""

    presenter = RecommendationPresenter()

    recommendation = make_recommendation(
        action=RecommendationAction.BUY,
        level=RecommendationLevel.A,
        score=5.0,
        risk_score=4.0,
    )

    result = presenter.present(
        recommendation
    )

    assert result.risk_warning is not None
    assert "Risk notice" in result.risk_warning


def test_present_low_risk_has_no_warning() -> None:
    """Low-risk active recommendation should not warn."""

    presenter = RecommendationPresenter()

    recommendation = make_recommendation(
        action=RecommendationAction.BUY,
        level=RecommendationLevel.A,
        risk_score=2.0,
    )

    result = presenter.present(
        recommendation
    )

    assert result.risk_warning is None


def test_present_reject_generic_reason() -> None:
    """Generic rejection should still have a warning."""

    presenter = RecommendationPresenter()

    recommendation = make_recommendation(
        action=RecommendationAction.REJECT,
        level=RecommendationLevel.C,
        score=1.0,
        risk_score=2.0,
    )

    result = presenter.present(
        recommendation
    )

    assert result.risk_warning is not None
    assert "Recommendation rejected" in result.risk_warning


# ==========================================================
# Input Validation
# ==========================================================


def test_present_rejects_invalid_recommendation() -> None:
    """Invalid recommendation should be rejected."""

    presenter = RecommendationPresenter()

    with pytest.raises(
        TypeError,
        match="recommendation must be a Recommendation",
    ):
        presenter.present(
            "invalid"  # type: ignore[arg-type]
        )


def test_summarize_rejects_invalid_result() -> None:
    """Invalid result should be rejected."""

    with pytest.raises(
        TypeError,
        match="result must be a RecommendationResult",
    ):
        RecommendationPresenter.summarize(
            "invalid"  # type: ignore[arg-type]
        )


def test_present_result_rejects_invalid_result() -> None:
    """Invalid result should be rejected."""

    presenter = RecommendationPresenter()

    with pytest.raises(
        TypeError,
        match="result must be a RecommendationResult",
    ):
        presenter.present_result(
            "invalid"  # type: ignore[arg-type]
        )


def test_present_workflow_rejects_invalid_result() -> None:
    """Invalid workflow result should be rejected."""

    presenter = RecommendationPresenter()

    with pytest.raises(
        TypeError,
        match="result must be a RecommendationWorkflowResult",
    ):
        presenter.present_workflow(
            "invalid"  # type: ignore[arg-type]
        )


# ==========================================================
# Summary
# ==========================================================


def test_summary_empty() -> None:
    """Empty result should produce zero summary."""

    result = make_result(
        ()
    )

    summary = RecommendationPresenter.summarize(
        result
    )

    assert isinstance(
        summary,
        RecommendationSummary,
    )

    assert summary.total_count == 0
    assert summary.buy_count == 0
    assert summary.sell_count == 0
    assert summary.watch_count == 0
    assert summary.reject_count == 0

    assert summary.level_a_count == 0
    assert summary.level_b_count == 0
    assert summary.level_c_count == 0
    assert summary.level_d_count == 0

    assert summary.highest_score is None
    assert summary.lowest_risk_score is None


def test_summary_counts_actions() -> None:
    """Summary should count all actions."""

    result = make_result(
        (
            make_recommendation(
                symbol="BUY",
                action=RecommendationAction.BUY,
                level=RecommendationLevel.A,
            ),
            make_recommendation(
                symbol="SELL",
                action=RecommendationAction.SELL,
                level=RecommendationLevel.A,
            ),
            make_recommendation(
                symbol="WATCH",
                action=RecommendationAction.WATCH,
                level=RecommendationLevel.B,
                score=1.0,
            ),
            make_recommendation(
                symbol="REJECT",
                action=RecommendationAction.REJECT,
                level=RecommendationLevel.D,
                score=-1.0,
            ),
        )
    )

    summary = RecommendationPresenter.summarize(
        result
    )

    assert summary.total_count == 4
    assert summary.buy_count == 1
    assert summary.sell_count == 1
    assert summary.watch_count == 1
    assert summary.reject_count == 1


def test_summary_counts_levels() -> None:
    """Summary should count all levels."""

    result = make_result(
        (
            make_recommendation(
                symbol="A1",
                level=RecommendationLevel.A,
            ),
            make_recommendation(
                symbol="A2",
                level=RecommendationLevel.A,
            ),
            make_recommendation(
                symbol="B1",
                level=RecommendationLevel.B,
                action=RecommendationAction.WATCH,
                score=1.0,
            ),
            make_recommendation(
                symbol="C1",
                level=RecommendationLevel.C,
                action=RecommendationAction.REJECT,
                score=-1.0,
            ),
            make_recommendation(
                symbol="D1",
                level=RecommendationLevel.D,
                action=RecommendationAction.REJECT,
                score=1.0,
                risk_score=8.0,
            ),
        )
    )

    summary = RecommendationPresenter.summarize(
        result
    )

    assert summary.level_a_count == 2
    assert summary.level_b_count == 1
    assert summary.level_c_count == 1
    assert summary.level_d_count == 1


def test_summary_highest_score() -> None:
    """Summary should expose the highest score."""

    result = make_result(
        (
            make_recommendation(
                symbol="LOW",
                score=1.0,
            ),
            make_recommendation(
                symbol="HIGH",
                score=5.0,
            ),
        )
    )

    summary = RecommendationPresenter.summarize(
        result
    )

    assert summary.highest_score == 5.0


def test_summary_lowest_risk() -> None:
    """Summary should expose the lowest risk score."""

    result = make_result(
        (
            make_recommendation(
                symbol="HIGH-RISK",
                risk_score=6.0,
            ),
            make_recommendation(
                symbol="LOW-RISK",
                risk_score=1.0,
            ),
        )
    )

    summary = RecommendationPresenter.summarize(
        result
    )

    assert summary.lowest_risk_score == 1.0


# ==========================================================
# Result Presentation
# ==========================================================


def test_present_result() -> None:
    """Recommendation result should convert to presentation result."""

    presenter = RecommendationPresenter()

    result = make_result(
        (
            make_recommendation(
                symbol="ONE",
                score=5.0,
            ),
            make_recommendation(
                symbol="TWO",
                action=RecommendationAction.WATCH,
                level=RecommendationLevel.B,
                score=1.0,
            ),
        )
    )

    presented = presenter.present_result(
        result
    )

    assert isinstance(
        presented,
        RecommendationPresentationResult,
    )

    assert len(
        presented.items
    ) == 2

    assert presented.symbols == (
        "ONE",
        "TWO",
    )

    assert presented.ranked_count == 2


def test_present_result_preserves_ranked_count() -> None:
    """Explicit ranked count should be preserved."""

    presenter = RecommendationPresenter()

    result = make_result(
        (
            make_recommendation(),
        )
    )

    presented = presenter.present_result(
        result,
        ranked_count=10,
    )

    assert presented.ranked_count == 10


def test_present_result_rejects_negative_ranked_count() -> None:
    """Negative ranked count should be rejected."""

    presenter = RecommendationPresenter()

    result = make_result(
        (
            make_recommendation(),
        )
    )

    with pytest.raises(
        ValueError,
        match="ranked_count must not be negative",
    ):
        presenter.present_result(
            result,
            ranked_count=-1,
        )


def test_present_result_top() -> None:
    """Top property should return first presentation."""

    presenter = RecommendationPresenter()

    first = make_recommendation(
        symbol="FIRST"
    )

    second = make_recommendation(
        symbol="SECOND"
    )

    result = presenter.present_result(
        make_result(
            (
                first,
                second,
            )
        )
    )

    assert result.top is result.items[0]
    assert result.top is not None
    assert result.top.symbol == "FIRST"


def test_present_result_empty_top() -> None:
    """Empty presentation result should have no top item."""

    presenter = RecommendationPresenter()

    result = presenter.present_result(
        make_result(())
    )

    assert result.top is None
    assert result.symbols == ()


def test_present_result_top_n() -> None:
    """Top N should return requested presentations."""

    presenter = RecommendationPresenter()

    result = presenter.present_result(
        make_result(
            (
                make_recommendation(
                    symbol="ONE"
                ),
                make_recommendation(
                    symbol="TWO"
                ),
                make_recommendation(
                    symbol="THREE"
                ),
            )
        )
    )

    top = result.top_n(2)

    assert len(top) == 2
    assert top[0].symbol == "ONE"
    assert top[1].symbol == "TWO"


def test_present_result_top_n_rejects_zero() -> None:
    """Top N should reject zero."""

    presenter = RecommendationPresenter()

    result = presenter.present_result(
        make_result(())
    )

    with pytest.raises(ValueError):
        result.top_n(0)


# ==========================================================
# Workflow Presentation
# ==========================================================


def test_present_workflow_uses_ranked_count() -> None:
    """Workflow presentation should preserve ranked count."""

    presenter = RecommendationPresenter()

    recommendation = make_recommendation(
        symbol="TEST"
    )

    recommendation_result = make_result(
        (
            recommendation,
        )
    )

    analysis = OpportunityAnalysisResult(
        signals=(),
        total_count=0,
    )

    workflow_result = RecommendationWorkflowResult(
        analysis=analysis,
        recommendations=recommendation_result,
        ranked_count=7,
    )

    presented = presenter.present_workflow(
        workflow_result
    )

    assert presented.ranked_count == 7
    assert presented.total_count == 1
    assert presented.symbols == (
        "TEST",
    )


# ==========================================================
# Dataclass Stability
# ==========================================================


def test_action_display_is_frozen() -> None:
    """ActionDisplay should be immutable."""

    display = RecommendationPresenter.action_display(
        RecommendationAction.BUY
    )

    with pytest.raises(
        AttributeError
    ):
        display.title = "changed"  # type: ignore[misc]


def test_level_display_is_frozen() -> None:
    """LevelDisplay should be immutable."""

    display = RecommendationPresenter.level_display(
        RecommendationLevel.A
    )

    with pytest.raises(
        AttributeError
    ):
        display.title = "changed"  # type: ignore[misc]


def test_presentation_is_frozen() -> None:
    """RecommendationPresentation should be immutable."""

    presenter = RecommendationPresenter()

    item = presenter.present(
        make_recommendation()
    )

    with pytest.raises(
        AttributeError
    ):
        item.symbol = "changed"  # type: ignore[misc]


def test_summary_is_frozen() -> None:
    """RecommendationSummary should be immutable."""

    summary = RecommendationPresenter.summarize(
        make_result(
            (
                make_recommendation(),
            )
        )
    )

    with pytest.raises(
        AttributeError
    ):
        summary.total_count = 10  # type: ignore[misc]


# ==========================================================
# Numeric Normalization
# ==========================================================


def test_present_normalizes_score_to_float() -> None:
    """Presentation score should always be float."""

    presenter = RecommendationPresenter()

    recommendation = make_recommendation(
        score=3
    )

    result = presenter.present(
        recommendation
    )

    assert isinstance(
        result.score,
        float,
    )


def test_present_normalizes_risk_to_float() -> None:
    """Presentation risk score should always be float."""

    presenter = RecommendationPresenter()

    recommendation = make_recommendation(
        risk_score=2
    )

    result = presenter.present(
        recommendation
    )

    assert isinstance(
        result.risk_score,
        float,
    )


# ==========================================================
# Public Exports
# ==========================================================


def test_public_exports_are_available() -> None:
    """All public presentation symbols should be exported."""

    import core.recommendation_presentation as module

    expected = {
        "ActionDisplay",
        "LevelDisplay",
        "PresentationAction",
        "PresentationLevel",
        "RecommendationPresentation",
        "RecommendationPresentationResult",
        "RecommendationPresenter",
        "RecommendationSummary",
    }

    assert set(
        module.__all__
    ) == expected