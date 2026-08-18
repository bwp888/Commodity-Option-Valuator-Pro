"""
Commodity Option Valuator Pro
=============================

Option Risk Evaluation Model

This module provides the unified risk-analysis layer
for option valuation.

Public interfaces
-----------------
RiskLevel
    Risk classification enum.

RiskAnalyzer
    Complete option risk analyzer.

RiskEngine
    Legacy-compatible risk scoring engine.

RiskResult
    Legacy-compatible risk result container.

Risk scoring
------------
IV Score          : 0 - 25
Gamma Score       : 0 - 25
Theta Score       : 0 - 20
Valuation Score   : 0 - 30
Total Score       : 0 - 100

Author : Simon
Version : 1.1.0
Python : 3.12
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


# ==========================================================
# Risk Level
# ==========================================================


class RiskLevel(Enum):
    """
    Risk classification level.

    The levels are ordered by increasing risk.
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"

    def __str__(self) -> str:
        return self.value


# ==========================================================
# Risk Result
# ==========================================================


@dataclass
class RiskResult:
    """
    Legacy-compatible risk evaluation result.
    """

    score: float

    level: str

    description: str


# ==========================================================
# Risk Analyzer
# ==========================================================


class RiskAnalyzer:
    """
    Complete option risk analyzer.

    Parameters
    ----------
    greeks:
        Existing Greeks calculation object.

    implied_volatility:
        Existing ImpliedVolatility solver.

    taylor:
        Existing TaylorValuator.

    Notes
    -----
    The analyzer does not modify the underlying valuation
    objects. It only reads their calculated values and
    converts them into normalized risk scores.
    """

    IV_MAX_SCORE = 25.0
    GAMMA_MAX_SCORE = 25.0
    THETA_MAX_SCORE = 20.0
    VALUATION_MAX_SCORE = 30.0

    TOTAL_MAX_SCORE = 100.0

    # IV reference points.
    IV_LOW = 0.20
    IV_HIGH = 0.50

    # Gamma reference points.
    GAMMA_LOW = 0.01
    GAMMA_HIGH = 0.10

    # Theta reference points.
    THETA_LOW = 0.01
    THETA_HIGH = 0.10

    # Valuation deviation reference points.
    VALUATION_LOW = 0.02
    VALUATION_HIGH = 0.10

    def __init__(
        self,
        greeks: Any,
        implied_volatility: Any,
        taylor: Any,
    ) -> None:
        """
        Initialize risk analyzer.
        """

        self.greeks = greeks
        self.implied_volatility = implied_volatility
        self.taylor = taylor

        self.option = getattr(
            greeks,
            "option",
            getattr(
                implied_volatility,
                "option",
                None,
            ),
        )

        self.spot = float(
            getattr(
                greeks,
                "spot",
                getattr(
                    self.option,
                    "spot",
                    0.0,
                ),
            )
        )

        self.price = float(
            getattr(
                getattr(greeks, "bs", None),
                "price",
                0.0,
            )
        )

        if self.price == 0.0:
            self.price = self._get_price()

    # ======================================================
    # Internal Helpers
    # ======================================================

    @staticmethod
    def _clamp(
        value: float,
        minimum: float,
        maximum: float,
    ) -> float:
        """
        Clamp value into [minimum, maximum].
        """

        return max(
            minimum,
            min(
                maximum,
                value,
            ),
        )

    def _get_price(self) -> float:
        """
        Obtain current option valuation price.
        """

        bs = getattr(
            self.greeks,
            "bs",
            None,
        )

        if bs is not None and hasattr(
            bs,
            "price",
        ):
            return float(bs.price)

        option = self.option

        if option is not None:
            try:
                from models.black_scholes import BlackScholes

                return float(
                    BlackScholes(option).price
                )

            except Exception:
                pass

        return 0.0

    def _get_iv(self) -> float:
        """
        Obtain implied volatility.

        Returns
        -------
        float
            Annualized implied volatility.

        Notes
        -----
        If the IV solver cannot produce a valid result,
        zero is returned instead of propagating the
        numerical exception into the risk scanner.
        """

        try:
            if hasattr(
                self.implied_volatility,
                "solve_cached",
            ):
                return float(
                    self.implied_volatility.solve_cached()
                )

            if hasattr(
                self.implied_volatility,
                "implied_volatility",
            ):
                return float(
                    self.implied_volatility.implied_volatility
                )

            if hasattr(
                self.implied_volatility,
                "solve",
            ):
                return float(
                    self.implied_volatility.solve()
                )

        except (
            ValueError,
            TypeError,
            ArithmeticError,
        ):
            return 0.0

        return 0.0

    def _get_gamma(self) -> float:
        """
        Obtain absolute gamma.
        """

        try:
            return abs(
                float(
                    self.greeks.gamma
                )
            )

        except (
            AttributeError,
            TypeError,
            ValueError,
        ):
            return 0.0

    def _get_theta(self) -> float:
        """
        Obtain absolute daily theta.

        Greeks.theta in this project is already normalized
        to 365 calendar days.
        """

        try:
            return abs(
                float(
                    self.greeks.theta
                )
            )

        except (
            AttributeError,
            TypeError,
            ValueError,
        ):
            return 0.0

    # ======================================================
    # Component Scores
    # ======================================================

    def iv_score(self) -> float:
        """
        Calculate implied-volatility risk score.

        Returns
        -------
        float
            Score between 0 and 25.
        """

        iv = self._get_iv()

        if iv <= self.IV_LOW:
            return 0.0

        if iv >= self.IV_HIGH:
            return self.IV_MAX_SCORE

        score = (
            (
                iv - self.IV_LOW
            )
            /
            (
                self.IV_HIGH - self.IV_LOW
            )
        ) * self.IV_MAX_SCORE

        return self._clamp(
            score,
            0.0,
            self.IV_MAX_SCORE,
        )

    def gamma_score(self) -> float:
        """
        Calculate gamma risk score.

        Returns
        -------
        float
            Score between 0 and 25.
        """

        gamma = self._get_gamma()

        if gamma <= self.GAMMA_LOW:
            return 0.0

        if gamma >= self.GAMMA_HIGH:
            return self.GAMMA_MAX_SCORE

        score = (
            (
                gamma - self.GAMMA_LOW
            )
            /
            (
                self.GAMMA_HIGH - self.GAMMA_LOW
            )
        ) * self.GAMMA_MAX_SCORE

        return self._clamp(
            score,
            0.0,
            self.GAMMA_MAX_SCORE,
        )

    def theta_score(self) -> float:
        """
        Calculate theta risk score.

        Theta is measured using the project's
        365-day convention.

        Returns
        -------
        float
            Score between 0 and 20.
        """

        theta = self._get_theta()

        if theta <= self.THETA_LOW:
            return 0.0

        if theta >= self.THETA_HIGH:
            return self.THETA_MAX_SCORE

        score = (
            (
                theta - self.THETA_LOW
            )
            /
            (
                self.THETA_HIGH - self.THETA_LOW
            )
        ) * self.THETA_MAX_SCORE

        return self._clamp(
            score,
            0.0,
            self.THETA_MAX_SCORE,
        )

    def valuation_score(
        self,
        market_price: float,
    ) -> float:
        """
        Calculate valuation-deviation risk score.

        Parameters
        ----------
        market_price:
            Market option price.

        Returns
        -------
        float
            Score between 0 and 30.
        """

        theoretical_price = self.price

        market_price = float(
            market_price
        )

        if market_price <= 0:
            return self.VALUATION_MAX_SCORE

        if theoretical_price <= 0:
            return self.VALUATION_MAX_SCORE

        deviation = abs(
            market_price
            -
            theoretical_price
        ) / theoretical_price

        if deviation <= self.VALUATION_LOW:
            return 0.0

        if deviation >= self.VALUATION_HIGH:
            return self.VALUATION_MAX_SCORE

        score = (
            (
                deviation - self.VALUATION_LOW
            )
            /
            (
                self.VALUATION_HIGH
                -
                self.VALUATION_LOW
            )
        ) * self.VALUATION_MAX_SCORE

        return self._clamp(
            score,
            0.0,
            self.VALUATION_MAX_SCORE,
        )

    # ======================================================
    # Total Score
    # ======================================================

    def total_score(
        self,
        market_price: float | None = None,
    ) -> float:
        """
        Calculate total risk score.

        If market_price is omitted, the option's current
        valuation price is used.
        """

        if market_price is None:
            market_price = self.price

        score = (
            self.iv_score()
            +
            self.gamma_score()
            +
            self.theta_score()
            +
            self.valuation_score(
                market_price
            )
        )

        return self._clamp(
            score,
            0.0,
            self.TOTAL_MAX_SCORE,
        )

    # ======================================================
    # Risk Level
    # ======================================================

    @staticmethod
    def risk_level(
        score: float,
    ) -> RiskLevel:
        """
        Convert numerical score into risk level.

        Thresholds
        ----------
        0 - 29:
            LOW

        30 - 69:
            MEDIUM

        70 - 89:
            HIGH

        90 - 100:
            EXTREME
        """

        score = float(score)

        if score < 30.0:
            return RiskLevel.LOW

        if score < 70.0:
            return RiskLevel.MEDIUM

        if score < 90.0:
            return RiskLevel.HIGH

        return RiskLevel.EXTREME

    # ======================================================
    # Analyze
    # ======================================================

    def analyze(
        self,
        market_price: float | None = None,
    ) -> dict[str, Any]:
        """
        Perform complete risk analysis.

        Returns
        -------
        dict
            Structured risk analysis result.
        """

        if market_price is None:
            market_price = self.price

        iv_score = self.iv_score()

        gamma_score = self.gamma_score()

        theta_score = self.theta_score()

        valuation_score = self.valuation_score(
            market_price
        )

        score = self._clamp(
            iv_score
            +
            gamma_score
            +
            theta_score
            +
            valuation_score,
            0.0,
            self.TOTAL_MAX_SCORE,
        )

        level = self.risk_level(
            score
        )

        return {
            "score": score,

            "level": level.value,

            "components": {
                "iv_score": iv_score,
                "gamma_score": gamma_score,
                "theta_score": theta_score,
                "valuation_score": valuation_score,
            },

            "market": {
                "spot": self.spot,
                "price": self.price,
                "market_price": float(
                    market_price
                ),
                "implied_volatility": self._get_iv(),
                "gamma": self._get_gamma(),
                "theta": self._get_theta(),
            },
        }

    # ======================================================
    # Summary
    # ======================================================

    def summary(
        self,
        market_price: float | None = None,
    ) -> dict[str, Any]:
        """
        Return complete risk summary.
        """

        return self.analyze(
            market_price
        )

    # ======================================================
    # Dictionary Export
    # ======================================================

    def to_dict(
        self,
        market_price: float | None = None,
    ) -> dict[str, Any]:
        """
        Export risk analysis as dictionary.
        """

        return self.analyze(
            market_price
        )

    # ======================================================
    # Representation
    # ======================================================

    def __str__(self) -> str:
        """
        Human-readable representation.
        """

        return (
            "RiskAnalyzer("
            f"score={self.total_score():.4f}, "
            f"level={self.risk_level(self.total_score()).value}"
            ")"
        )

    def __repr__(self) -> str:
        """
        Developer representation.
        """

        return self.__str__()


# ==========================================================
# Legacy Risk Engine
# ==========================================================


class RiskEngine:
    """
    Legacy-compatible risk scoring engine.

    This class is retained so existing modules that use
    RiskEngine do not break while RiskAnalyzer becomes the
    main public risk-analysis interface.
    """

    def calculate(
        self,
        delta: float,
        gamma: float,
        theta: float,
        vega: float,
    ) -> RiskResult:
        """
        Calculate legacy risk score.
        """

        score = (
            abs(delta) * 20.0
            +
            abs(gamma) * 200.0
            +
            abs(theta) * 10.0
            +
            abs(vega) * 5.0
        )

        score = min(
            max(
                score,
                0.0,
            ),
            100.0,
        )

        if score < 30.0:
            level = RiskLevel.LOW.value

        elif score < 70.0:
            level = RiskLevel.MEDIUM.value

        elif score < 90.0:
            level = RiskLevel.HIGH.value

        else:
            level = RiskLevel.EXTREME.value

        return RiskResult(
            score=score,
            level=level,
            description=f"{level} risk",
        )


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "RiskLevel",
    "RiskResult",
    "RiskAnalyzer",
    "RiskEngine",
]