"""
Commodity Option Valuator Pro
=============================

Comprehensive Valuation Evaluation.

Phase 2-A
---------

Provides the unified comprehensive evaluation layer
for single-option valuation and scanner batch valuation.

Workflow
--------
SingleOptionValuationResult
        ↓
ComprehensiveEvaluator
        ↓
Valuation / IV / Theta / Gamma / Taylor
        ↓
Risk Gate
        ↓
Recommendation / Watch / Caution
        ↓
Reason List

Scoring
-------
Valuation Advantage       : 0 - 35
IV Quality                : 0 - 20
Theta Risk                : 0 - 20
Gamma Risk                : 0 - 15
Taylor Consistency        : 0 - 10

Total                     : 0 - 100

Decision
--------
80 - 100 : RECOMMEND
60 - 79  : WATCH
0  - 59  : CAUTION

Risk Gate
---------
HIGH / EXTREME risk cannot receive RECOMMEND.

This module does not modify:
- RecommendationEngine
- RecommendationWorkflow
- RecommendationSummary
- RecommendationPresentation
- SingleOptionValuator
- RiskAnalyzer
- BlackScholes
- Greeks
- TaylorValuator

It consumes the existing SingleOptionValuationResult
and reuses the existing RiskAnalyzer scoring model
through a lightweight adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import SimpleNamespace
from typing import Any

from models.risk import (
    RiskAnalyzer,
    RiskLevel,
)


# ==========================================================
# Evaluation Decision
# ==========================================================


class ComprehensiveDecision(str, Enum):
    """
    Final comprehensive evaluation decision.
    """

    RECOMMEND = "RECOMMEND"
    WATCH = "WATCH"
    CAUTION = "CAUTION"


# ==========================================================
# Evaluation Reason
# ==========================================================


@dataclass(frozen=True)
class EvaluationReason:
    """
    One deterministic evaluation reason.

    Attributes
    ----------
    category:
        Reason category.

    positive:
        Whether the reason is favorable.

    message:
        Human-readable explanation.
    """

    category: str
    positive: bool
    message: str


# ==========================================================
# Evaluation Components
# ==========================================================


@dataclass(frozen=True)
class EvaluationComponents:
    """
    Component scores of comprehensive evaluation.

    All scores are positive contributions.

    Risk deductions are represented through the
    component scores themselves.
    """

    valuation_score: float
    iv_score: float
    theta_score: float
    gamma_score: float
    taylor_score: float

    @property
    def total_score(self) -> float:
        """Return total score."""

        return min(
            100.0,
            max(
                0.0,
                self.valuation_score
                + self.iv_score
                + self.theta_score
                + self.gamma_score
                + self.taylor_score,
            ),
        )

    def to_dict(self) -> dict[str, float]:
        """Return component scores as a dictionary."""

        return {
            "valuation_score": self.valuation_score,
            "iv_score": self.iv_score,
            "theta_score": self.theta_score,
            "gamma_score": self.gamma_score,
            "taylor_score": self.taylor_score,
            "total_score": self.total_score,
        }


# ==========================================================
# Comprehensive Evaluation Result
# ==========================================================


@dataclass(frozen=True)
class ComprehensiveEvaluationResult:
    """
    Complete comprehensive evaluation result.
    """

    symbol: str

    decision: ComprehensiveDecision

    score: float

    risk_score: float

    risk_level: RiskLevel

    components: EvaluationComponents

    reasons: tuple[EvaluationReason, ...]

    @property
    def reason_text(self) -> str:
        """
        Return reasons as a readable multi-line string.
        """

        return "\n".join(
            (
                (
                    "✓ "
                    if reason.positive
                    else "⚠ "
                )
                + reason.message
            )
            for reason in self.reasons
        )

    @property
    def reason_messages(self) -> tuple[str, ...]:
        """
        Return plain reason messages.
        """

        return tuple(
            reason.message
            for reason in self.reasons
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Export evaluation result as dictionary.
        """

        return {
            "symbol": self.symbol,
            "decision": self.decision.value,
            "score": self.score,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "components": self.components.to_dict(),
            "reasons": [
                {
                    "category": reason.category,
                    "positive": reason.positive,
                    "message": reason.message,
                }
                for reason in self.reasons
            ],
        }


# ==========================================================
# Comprehensive Evaluator
# ==========================================================


class ComprehensiveEvaluator:
    """
    Unified comprehensive evaluation engine.

    This class is shared by:

    - single-option valuation
    - scanner batch valuation

    It does not perform option pricing.

    It evaluates an already-computed
    SingleOptionValuationResult.
    """

    RECOMMEND_THRESHOLD = 80.0
    WATCH_THRESHOLD = 60.0

    MAX_RECOMMEND_RISK_LEVELS = {
        RiskLevel.LOW,
        RiskLevel.MEDIUM,
    }

    # ------------------------------------------------------
    # Valuation
    # ------------------------------------------------------

    VALUATION_MAX_SCORE = 35.0

    # ------------------------------------------------------
    # IV
    # ------------------------------------------------------

    IV_MAX_SCORE = 20.0
    IV_LOW = 0.20
    IV_HIGH = 0.50

    # ------------------------------------------------------
    # Theta
    # ------------------------------------------------------

    THETA_MAX_SCORE = 20.0
    THETA_LOW = 0.01
    THETA_HIGH = 0.10

    # ------------------------------------------------------
    # Gamma
    # ------------------------------------------------------

    GAMMA_MAX_SCORE = 15.0
    GAMMA_LOW = 0.01
    GAMMA_HIGH = 0.10

    # ------------------------------------------------------
    # Taylor
    # ------------------------------------------------------

    TAYLOR_MAX_SCORE = 10.0

    def evaluate(
        self,
        valuation_result: Any,
    ) -> ComprehensiveEvaluationResult:
        """
        Evaluate an existing valuation result.

        The object is intentionally duck-typed so that
        the evaluator does not create a hard dependency
        on the orchestration layer.

        Required attributes
        -------------------
        symbol
        current_option_price
        current_theoretical_price
        current_option_iv
        current_gamma
        current_theta
        target_theoretical_price
        taylor_first_order_price
        taylor_second_order_price
        """

        self._validate_result(
            valuation_result
        )

        risk = self._build_risk_analysis(
            valuation_result
        )

        components = EvaluationComponents(
            valuation_score=self._valuation_score(
                valuation_result
            ),
            iv_score=self._iv_score(
                valuation_result
            ),
            theta_score=self._theta_score(
                valuation_result
            ),
            gamma_score=self._gamma_score(
                valuation_result
            ),
            taylor_score=self._taylor_score(
                valuation_result
            ),
        )

        score = components.total_score

        risk_score = float(
            risk["score"]
        )

        risk_level = RiskLevel(
            risk["level"]
        )

        decision = self._decision(
            score=score,
            risk_level=risk_level,
        )

        reasons = self._build_reasons(
            valuation_result=valuation_result,
            components=components,
            risk_score=risk_score,
            risk_level=risk_level,
            decision=decision,
        )

        return ComprehensiveEvaluationResult(
            symbol=str(
                valuation_result.symbol
            ),
            decision=decision,
            score=score,
            risk_score=risk_score,
            risk_level=risk_level,
            components=components,
            reasons=tuple(reasons),
        )

    # ======================================================
    # Validation
    # ======================================================

    @staticmethod
    def _validate_result(
        result: Any,
    ) -> None:
        """Validate required valuation-result attributes."""

        required = (
            "symbol",
            "current_option_price",
            "current_theoretical_price",
            "current_option_iv",
            "current_gamma",
            "current_theta",
            "target_theoretical_price",
            "taylor_first_order_price",
            "taylor_second_order_price",
        )

        for name in required:

            if not hasattr(
                result,
                name,
            ):
                raise TypeError(
                    "valuation_result is missing "
                    f"required attribute: {name}"
                )

        if not str(
            result.symbol
        ).strip():

            raise ValueError(
                "valuation_result.symbol must not be empty"
            )

    # ======================================================
    # Risk Adapter
    # ======================================================

    @staticmethod
    def _build_risk_analysis(
        result: Any,
    ) -> dict[str, Any]:
        """
        Reuse the existing RiskAnalyzer.

        RiskAnalyzer was designed around the lower-level
        Greeks / BS / IV objects. SingleOptionValuationResult
        already contains the calculated values.

        A lightweight adapter exposes those values to
        RiskAnalyzer without modifying the existing risk
        model or introducing circular imports.
        """

        greeks = SimpleNamespace(
            gamma=float(
                result.current_gamma
            ),
            theta=float(
                result.current_theta
            ),
            bs=SimpleNamespace(
                price=float(
                    result.current_theoretical_price
                )
            ),
            option=SimpleNamespace(
                spot=float(
                    result.current_futures_price
                )
            ),
        )

        implied_volatility = SimpleNamespace(
            solve_cached=lambda: float(
                result.current_option_iv
            )
        )

        taylor = SimpleNamespace()

        analyzer = RiskAnalyzer(
            greeks=greeks,
            implied_volatility=implied_volatility,
            taylor=taylor,
        )

        return analyzer.analyze(
            market_price=float(
                result.current_option_price
            )
        )

    # ======================================================
    # Component Scores
    # ======================================================

    def _valuation_score(
        self,
        result: Any,
    ) -> float:
        """
        Score valuation advantage.

        A market price below theoretical value is favorable
        for the valuation model.

        A market price above theoretical value is unfavorable.

        The score is normalized to 0 - 35.
        """

        market_price = float(
            result.current_option_price
        )

        theoretical_price = float(
            result.current_theoretical_price
        )

        if market_price <= 0:
            return self.VALUATION_MAX_SCORE

        if theoretical_price <= 0:
            return 0.0

        advantage = (
            theoretical_price
            - market_price
        ) / market_price

        if advantage <= 0:
            return 0.0

        # 10% theoretical advantage reaches full score.
        normalized = advantage / 0.10

        return self._clamp(
            normalized
            * self.VALUATION_MAX_SCORE,
            0.0,
            self.VALUATION_MAX_SCORE,
        )

    def _iv_score(
        self,
        result: Any,
    ) -> float:
        """
        Score IV quality.

        Lower/moderate IV receives a higher score.
        IV at or above 50% receives zero score.
        """

        iv = float(
            result.current_option_iv
        )

        if iv <= self.IV_LOW:
            return self.IV_MAX_SCORE

        if iv >= self.IV_HIGH:
            return 0.0

        normalized = (
            self.IV_HIGH - iv
        ) / (
            self.IV_HIGH - self.IV_LOW
        )

        return self._clamp(
            normalized
            * self.IV_MAX_SCORE,
            0.0,
            self.IV_MAX_SCORE,
        )

    def _theta_score(
        self,
        result: Any,
    ) -> float:
        """
        Score time-value decay.

        Lower absolute daily theta receives a higher score.
        """

        theta = abs(
            float(
                result.current_theta
            )
        )

        if theta <= self.THETA_LOW:
            return self.THETA_MAX_SCORE

        if theta >= self.THETA_HIGH:
            return 0.0

        normalized = (
            self.THETA_HIGH - theta
        ) / (
            self.THETA_HIGH - self.THETA_LOW
        )

        return self._clamp(
            normalized
            * self.THETA_MAX_SCORE,
            0.0,
            self.THETA_MAX_SCORE,
        )

    def _gamma_score(
        self,
        result: Any,
    ) -> float:
        """
        Score gamma risk.

        Lower absolute gamma receives a higher score.
        """

        gamma = abs(
            float(
                result.current_gamma
            )
        )

        if gamma <= self.GAMMA_LOW:
            return self.GAMMA_MAX_SCORE

        if gamma >= self.GAMMA_HIGH:
            return 0.0

        normalized = (
            self.GAMMA_HIGH - gamma
        ) / (
            self.GAMMA_HIGH - self.GAMMA_LOW
        )

        return self._clamp(
            normalized
            * self.GAMMA_MAX_SCORE,
            0.0,
            self.GAMMA_MAX_SCORE,
        )

    def _taylor_score(
        self,
        result: Any,
    ) -> float:
        """
        Score Taylor consistency.

        The first- and second-order Taylor estimates are
        compared with the target theoretical price.

        Smaller relative deviation receives a higher score.
        """

        target = float(
            result.target_theoretical_price
        )

        first = float(
            result.taylor_first_order_price
        )

        second = float(
            result.taylor_second_order_price
        )

        if target <= 0:
            return 0.0

        first_error = abs(
            first - target
        ) / target

        second_error = abs(
            second - target
        ) / target

        average_error = (
            first_error
            + second_error
        ) / 2.0

        # <= 2% error = full score
        # >= 10% error = zero score
        if average_error <= 0.02:
            return self.TAYLOR_MAX_SCORE

        if average_error >= 0.10:
            return 0.0

        normalized = (
            0.10 - average_error
        ) / 0.08

        return self._clamp(
            normalized
            * self.TAYLOR_MAX_SCORE,
            0.0,
            self.TAYLOR_MAX_SCORE,
        )

    # ======================================================
    # Decision
    # ======================================================

    def _decision(
        self,
        *,
        score: float,
        risk_level: RiskLevel,
    ) -> ComprehensiveDecision:
        """
        Convert score and risk gate into final decision.
        """

        if (
            score >= self.RECOMMEND_THRESHOLD
            and risk_level
            in self.MAX_RECOMMEND_RISK_LEVELS
        ):
            return ComprehensiveDecision.RECOMMEND

        if score >= self.WATCH_THRESHOLD:
            return ComprehensiveDecision.WATCH

        return ComprehensiveDecision.CAUTION

    # ======================================================
    # Reasons
    # ======================================================

    def _build_reasons(
        self,
        *,
        valuation_result: Any,
        components: EvaluationComponents,
        risk_score: float,
        risk_level: RiskLevel,
        decision: ComprehensiveDecision,
    ) -> list[EvaluationReason]:
        """
        Build deterministic human-readable reasons.
        """

        reasons: list[
            EvaluationReason
        ] = []

        market_price = float(
            valuation_result.current_option_price
        )

        theoretical_price = float(
            valuation_result.current_theoretical_price
        )

        if market_price > 0:

            valuation_gap = (
                theoretical_price
                - market_price
            ) / market_price

            if valuation_gap >= 0.10:

                reasons.append(
                    EvaluationReason(
                        category="valuation",
                        positive=True,
                        message=(
                            "市场价格明显低于理论价格，"
                            "存在较明显的估值优势。"
                        ),
                    )
                )

            elif valuation_gap > 0:

                reasons.append(
                    EvaluationReason(
                        category="valuation",
                        positive=True,
                        message=(
                            "市场价格低于理论价格，"
                            "存在一定估值优势。"
                        ),
                    )
                )

            elif valuation_gap <= -0.10:

                reasons.append(
                    EvaluationReason(
                        category="valuation",
                        positive=False,
                        message=(
                            "市场价格明显高于理论价格，"
                            "当前估值优势不足。"
                        ),
                    )
                )

            else:

                reasons.append(
                    EvaluationReason(
                        category="valuation",
                        positive=False,
                        message=(
                            "市场价格与理论价格较为接近，"
                            "估值优势有限。"
                        ),
                    )
                )

        iv = float(
            valuation_result.current_option_iv
        )

        if iv <= self.IV_LOW:

            reasons.append(
                EvaluationReason(
                    category="iv",
                    positive=True,
                    message="IV处于较低或合理区间。",
                )
            )

        elif iv < self.IV_HIGH:

            reasons.append(
                EvaluationReason(
                    category="iv",
                    positive=False,
                    message="IV处于中等偏高区间，需要关注波动率风险。",
                )
            )

        else:

            reasons.append(
                EvaluationReason(
                    category="iv",
                    positive=False,
                    message="IV偏高，期权价格可能已经包含较高波动预期。",
                )
            )

        theta = abs(
            float(
                valuation_result.current_theta
            )
        )

        if theta <= self.THETA_LOW:

            reasons.append(
                EvaluationReason(
                    category="theta",
                    positive=True,
                    message="时间价值损耗较低，Theta压力可接受。",
                )
            )

        elif theta < self.THETA_HIGH:

            reasons.append(
                EvaluationReason(
                    category="theta",
                    positive=False,
                    message="时间价值存在一定损耗，需要关注持有时间。",
                )
            )

        else:

            reasons.append(
                EvaluationReason(
                    category="theta",
                    positive=False,
                    message="时间价值损耗较大，Theta压力明显。",
                )
            )

        gamma = abs(
            float(
                valuation_result.current_gamma
            )
        )

        if gamma <= self.GAMMA_LOW:

            reasons.append(
                EvaluationReason(
                    category="gamma",
                    positive=True,
                    message="Gamma风险较低，价格敏感度相对可控。",
                )
            )

        elif gamma < self.GAMMA_HIGH:

            reasons.append(
                EvaluationReason(
                    category="gamma",
                    positive=False,
                    message="Gamma处于中等水平，需要关注标的价格快速变化。",
                )
            )

        else:

            reasons.append(
                EvaluationReason(
                    category="gamma",
                    positive=False,
                    message="Gamma风险较高，标的价格变化可能快速放大期权价值波动。",
                )
            )

        target = float(
            valuation_result.target_theoretical_price
        )

        first = float(
            valuation_result.taylor_first_order_price
        )

        second = float(
            valuation_result.taylor_second_order_price
        )

        if target > 0:

            error = (
                (
                    abs(
                        first - target
                    )
                    +
                    abs(
                        second - target
                    )
                )
                / 2.0
                / target
            )

            if error <= 0.02:

                reasons.append(
                    EvaluationReason(
                        category="taylor",
                        positive=True,
                        message="Taylor估值与目标理论价格较为一致。",
                    )
                )

            elif error < 0.10:

                reasons.append(
                    EvaluationReason(
                        category="taylor",
                        positive=False,
                        message="Taylor估值与目标理论价格存在一定偏差。",
                    )
                )

            else:

                reasons.append(
                    EvaluationReason(
                        category="taylor",
                        positive=False,
                        message="Taylor估值与目标理论价格偏差较大，目标情景敏感性较高。",
                    )
                )

        if risk_level == RiskLevel.HIGH:

            reasons.append(
                EvaluationReason(
                    category="risk",
                    positive=False,
                    message=(
                        "综合风险等级较高，"
                        "因此即使估值评分较高也不直接列为推荐。"
                    ),
                )
            )

        elif risk_level == RiskLevel.EXTREME:

            reasons.append(
                EvaluationReason(
                    category="risk",
                    positive=False,
                    message=(
                        "综合风险等级为极高，"
                        "当前不适合列为推荐。"
                    ),
                )
            )

        elif risk_level == RiskLevel.LOW:

            reasons.append(
                EvaluationReason(
                    category="risk",
                    positive=True,
                    message="综合风险等级较低。",
                )
            )

        else:

            reasons.append(
                EvaluationReason(
                    category="risk",
                    positive=True,
                    message="综合风险处于可接受范围。",
                )
            )

        return reasons

    # ======================================================
    # Convenience
    # ======================================================

    def evaluate_to_dict(
        self,
        valuation_result: Any,
    ) -> dict[str, Any]:
        """
        Evaluate and export as dictionary.
        """

        return self.evaluate(
            valuation_result
        ).to_dict()

    # ======================================================
    # Utility
    # ======================================================

    @staticmethod
    def _clamp(
        value: float,
        minimum: float,
        maximum: float,
    ) -> float:
        """Clamp a value into a fixed range."""

        return max(
            minimum,
            min(
                maximum,
                value,
            ),
        )


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "ComprehensiveDecision",
    "EvaluationReason",
    "EvaluationComponents",
    "ComprehensiveEvaluationResult",
    "ComprehensiveEvaluator",
]