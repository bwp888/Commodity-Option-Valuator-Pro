"""
Commodity Option Valuator Pro
=============================

Risk Scoring Engine

This module calculates comprehensive
option risk score.

Score Range
------------
0 - 100

Higher score means higher risk.


Author : Simon
Version : 1.0.0
Python : 3.12
"""

from __future__ import annotations


from enum import Enum

from typing import Any


from models.greeks import Greeks
from models.implied_volatility import ImpliedVolatility
from models.taylor import TaylorValuator



# ==========================================================
# Risk Level
# ==========================================================


class RiskLevel(Enum):
    """
    Risk classification.
    """

    LOW = "LOW"

    MEDIUM = "MEDIUM"

    HIGH = "HIGH"

    EXTREME = "EXTREME"



# ==========================================================
# Risk Analyzer
# ==========================================================


class RiskAnalyzer:
    """
    Comprehensive option risk scoring engine.

    Parameters
    ----------
    greeks:
        Greeks calculation object.

    iv:
        Implied volatility solver.

    taylor:
        Taylor valuation model.

    Notes
    -----
    Generates a 0-100 risk score.
    """


    MAX_SCORE: float = 100.0



    def __init__(
        self,
        greeks: Greeks,
        iv: ImpliedVolatility,
        taylor: TaylorValuator,
    ) -> None:
        """
        Initialize risk analyzer.

        Parameters
        ----------
        greeks:
            Greeks engine.

        iv:
            Implied volatility engine.

        taylor:
            Taylor valuation engine.
        """

        self.greeks = greeks

        self.iv = iv

        self.taylor = taylor



    # ------------------------------------------------------
    # Basic Properties
    # ------------------------------------------------------


    @property
    def option(self):
        """
        Option contract.
        """

        return self.greeks.option



    # ------------------------------------------------------


    @property
    def spot(self) -> float:
        """
        Current underlying price.
        """

        return self.greeks.spot



    # ------------------------------------------------------


    @property
    def price(self) -> float:
        """
        Current theoretical price.
        """

        return self.greeks.bs.price
    # ------------------------------------------------------
    # IV Risk Score
    # ------------------------------------------------------

    def iv_score(self) -> float:
        """
        Calculate implied volatility risk score.

        Logic
        -----
        Higher IV means higher risk.

        Score:
        0 - 25
        """

        iv = (
            self.iv.implied_volatility
        )


        if iv < 0.10:

            return 5.0


        if iv < 0.20:

            return 10.0


        if iv < 0.35:

            return 15.0


        if iv < 0.50:

            return 20.0


        return 25.0



    # ------------------------------------------------------
    # Gamma Risk Score
    # ------------------------------------------------------

    def gamma_score(self) -> float:
        """
        Calculate Gamma risk score.

        Higher Gamma means higher
        price sensitivity risk.

        Score:
        0 - 25
        """

        gamma = abs(
            self.greeks.gamma
        )


        if gamma < 0.01:

            return 5.0


        if gamma < 0.02:

            return 10.0


        if gamma < 0.04:

            return 15.0


        if gamma < 0.08:

            return 20.0


        return 25.0



    # ------------------------------------------------------
    # Theta Risk Score
    # ------------------------------------------------------

    def theta_score(self) -> float:
        """
        Calculate Theta decay risk.

        Larger negative Theta means
        faster time decay.

        Score:
        0 - 20
        """

        theta = abs(
            self.greeks.theta
        )


        if theta < 0.005:

            return 5.0


        if theta < 0.02:

            return 10.0


        if theta < 0.05:

            return 15.0


        return 20.0



    # ------------------------------------------------------
    # Valuation Deviation Score
    # ------------------------------------------------------

    def valuation_score(
        self,
        new_spot: float | None = None,
    ) -> float:
        """
        Calculate Taylor valuation deviation.

        Score:
        0 - 30
        """

        if new_spot is None:

            new_spot = self.spot


        result = self.taylor.estimate(
            new_spot
        )


        estimated_price = (
            result[
                "second_order_price"
            ]
        )


        base_price = (
            result[
                "base_price"
            ]
        )


        if base_price == 0:

            return 30.0


        deviation = abs(
            estimated_price
            -
            base_price
        ) / base_price



        if deviation < 0.05:

            return 5.0


        if deviation < 0.10:

            return 15.0


        if deviation < 0.20:

            return 25.0


        return 30.0



    # ------------------------------------------------------
    # Total Score
    # ------------------------------------------------------

    def total_score(
        self,
        new_spot: float | None = None,
    ) -> float:
        """
        Calculate total risk score.

        Returns
        -------
        float
            Risk score 0-100.
        """

        score = (
            self.iv_score()
            +
            self.gamma_score()
            +
            self.theta_score()
            +
            self.valuation_score(
                new_spot
            )
        )


        return min(
            score,
            self.MAX_SCORE,
        )
    # ------------------------------------------------------
    # Risk Level
    # ------------------------------------------------------

    def risk_level(
        self,
        score: float | None = None,
    ) -> RiskLevel:
        """
        Convert score into risk level.

        Parameters
        ----------
        score:
            Risk score.

        Returns
        -------
        RiskLevel
        """

        if score is None:

            score = self.total_score()


        if score < 40:

            return RiskLevel.LOW


        if score < 70:

            return RiskLevel.MEDIUM


        if score < 90:

            return RiskLevel.HIGH


        return RiskLevel.EXTREME



    # ------------------------------------------------------
    # Full Analysis
    # ------------------------------------------------------

    def analyze(
        self,
        new_spot: float | None = None,
    ) -> dict[str, Any]:
        """
        Generate complete risk analysis.

        Parameters
        ----------
        new_spot:
            Target underlying price.

        Returns
        -------
        dict
            Complete risk report.
        """

        score = self.total_score(
            new_spot
        )


        return {

            "score": score,


            "level": (
                self.risk_level(
                    score
                ).value
            ),


            "components": {

                "iv_score": (
                    self.iv_score()
                ),


                "gamma_score": (
                    self.gamma_score()
                ),


                "theta_score": (
                    self.theta_score()
                ),


                "valuation_score": (
                    self.valuation_score(
                        new_spot
                    )
                ),
            },


            "market": {

                "spot": self.spot,


                "option_price": (
                    self.price
                ),


                "implied_volatility": (
                    self.iv.implied_volatility
                ),
            },
        }



    # ------------------------------------------------------
    # Summary
    # ------------------------------------------------------

    def summary(
        self,
        new_spot: float | None = None,
    ) -> dict[str, Any]:
        """
        Return risk summary.

        This method is used by GUI layer.
        """

        return self.analyze(
            new_spot
        )



    # ------------------------------------------------------
    # Dictionary Export
    # ------------------------------------------------------

    def to_dict(
        self,
        new_spot: float | None = None,
    ) -> dict[str, Any]:
        """
        Export risk result.

        Parameters
        ----------
        new_spot:
            Target spot.

        Returns
        -------
        dict
        """

        return self.analyze(
            new_spot
        )
    # ------------------------------------------------------
    # String Representation
    # ------------------------------------------------------

    def __str__(self) -> str:
        """
        Human-readable representation.
        """

        score = self.total_score()


        level = self.risk_level(
            score
        ).value


        return (
            "RiskAnalyzer("
            f"score={score:.2f}, "
            f"level={level}"
            ")"
        )



    # ------------------------------------------------------

    def __repr__(self) -> str:
        """
        Developer representation.
        """

        return (
            "RiskAnalyzer("
            f"option={self.option!r}"
            ")"
        )



# ==========================================================
# Public Exports
# ==========================================================

__all__ = [
    "RiskAnalyzer",
    "RiskLevel",
]