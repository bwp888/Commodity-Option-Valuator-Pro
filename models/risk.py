"""
Commodity Option Valuator Pro
=============================

Option Risk Evaluation Model

Author : Simon
Version : 1.0.1
"""

from __future__ import annotations


from dataclasses import dataclass



# ==========================================================
# Risk Result
# ==========================================================


@dataclass
class RiskResult:
    """
    Risk evaluation result.
    """

    score: float

    level: str

    description: str



# ==========================================================
# Risk Engine
# ==========================================================


class RiskEngine:
    """
    Main risk scoring engine.
    """

    def calculate(
        self,
        delta: float,
        gamma: float,
        theta: float,
        vega: float,
    ) -> RiskResult:

        score = (

            abs(delta) * 20

            +

            abs(gamma) * 200

            +

            abs(theta) * 10

            +

            abs(vega) * 5

        )


        score = min(
            score,
            100.0
        )


        if score < 30:

            level = "LOW"

        elif score < 70:

            level = "MEDIUM"

        else:

            level = "HIGH"



        return RiskResult(

            score=score,

            level=level,

            description=f"{level} risk"

        )



# ==========================================================
# Risk Analyzer
# ==========================================================


class RiskAnalyzer:
    """
    Compatibility wrapper.

    Used by option scanner.

    """



    def __init__(
        self,
    ) -> None:

        self.engine = RiskEngine()



    def analyze(
        self,
        delta: float = 0.0,
        gamma: float = 0.0,
        theta: float = 0.0,
        vega: float = 0.0,
    ) -> RiskResult:
        """
        Analyze option risk.
        """

        return self.engine.calculate(

            delta=delta,

            gamma=gamma,

            theta=theta,

            vega=vega,

        )



    # alias

    calculate = analyze



__all__ = [

    "RiskResult",

    "RiskEngine",

    "RiskAnalyzer",

]