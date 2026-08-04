from __future__ import annotations


from dataclasses import dataclass
from typing import Any


from models.option_scanner import (
    OptionContract,
    OptionDirection,
)


from models.black_scholes import (
    BlackScholes,
)


from models.greeks import (
    Greeks,
)



# ==========================================================
# Valuation Result
# ==========================================================


@dataclass
class ValuationResult:
    """
    Option valuation result.
    """

    symbol: str

    direction: OptionDirection

    premium: float

    theoretical_price: float

    delta: float

    gamma: float

    theta: float

    vega: float

    difference: float | None

    risk_score: float


    def premium_difference(
        self,
    ) -> float:
        """
        Difference between market premium
        and theoretical value.
        """

        if self.difference is not None:
            return float(
                self.difference
            )

        return float(
            self.theoretical_price
            -
            self.premium
        )


    def valuation_ratio(
        self,
    ) -> float:
        """
        Theoretical / market price ratio.
        """

        if self.premium <= 0:
            return 0.0


        return float(
            self.theoretical_price
            /
            self.premium
        )



# ==========================================================
# Valuation Engine
# ==========================================================


class ValuationEngine:
    """
    Commodity option valuation engine.
    """


    def __init__(
        self,
        risk_free_rate: float = 0.025,
    ) -> None:

        self.risk_free_rate = (
            risk_free_rate
        )


    def __str__(
        self,
    ) -> str:

        return (
            "ValuationEngine"
        )


    def __repr__(
        self,
    ) -> str:

        return (
            "ValuationEngine()"
        )


    @property
    def days_per_year(
        self,
    ) -> int:

        return 365


    def days_to_year(
        self,
        days: int,
    ) -> float:

        return (
            days
            /
            self.days_per_year
        )
    def validate_contract(
        self,
        option: OptionContract | None,
    ) -> bool:
        """
        Validate option contract.
        """


        if option is None:
            return False


        if not option.symbol:
            return False


        if option.direction not in (
            OptionDirection.CALL,
            OptionDirection.PUT,
        ):
            return False


        if option.strike <= 0:
            return False


        if option.price < 0:
            return False


        return True



    def build_parameters(
        self,
        option: OptionContract,
        underlying_price: float,
        volatility: float,
        days: int,
    ) -> dict[str, float]:
        """
        Build Black-Scholes parameters.
        """


        return {

            "spot": float(
                underlying_price
            ),

            "strike": float(
                option.strike
            ),

            "volatility": float(
                volatility
            ),

            "time": self.days_to_year(
                days
            ),

            "rate": float(
                self.risk_free_rate
            ),

        }



    def evaluate(
        self,
        option: OptionContract,
        underlying_price: float,
        volatility: float,
        days: int,
    ) -> ValuationResult:
        """
        Evaluate single option.
        """


        if not self.validate_contract(
            option
        ):
            raise ValueError(
                "Invalid option contract"
            )


        params = self.build_parameters(
            option,
            underlying_price,
            volatility,
            days,
        )


        option_type = (
            "call"
            if option.direction
            ==
            OptionDirection.CALL
            else
            "put"
        )


        try:

            price = BlackScholes.price(
                S=params["spot"],
                K=params["strike"],
                T=params["time"],
                r=params["rate"],
                sigma=params["volatility"],
                option_type=option_type,
            )


        except Exception:

            price = 0.0



        try:

            greeks = Greeks.calculate(
                S=params["spot"],
                K=params["strike"],
                T=params["time"],
                r=params["rate"],
                sigma=params["volatility"],
                option_type=option_type,
            )


        except Exception:

            greeks = {

                "delta": 0.0,

                "gamma": 0.0,

                "theta": 0.0,

                "vega": 0.0,

            }



        difference = (
            price
            -
            option.price
        )


        risk_score = abs(
            difference
        )



        return ValuationResult(

            symbol=option.symbol,

            direction=option.direction,

            premium=float(
                option.price
            ),

            theoretical_price=float(
                price
            ),

            delta=float(
                greeks.get(
                    "delta",
                    0.0
                )
            ),

            gamma=float(
                greeks.get(
                    "gamma",
                    0.0
                )
            ),

            theta=float(
                greeks.get(
                    "theta",
                    0.0
                )
            ),

            vega=float(
                greeks.get(
                    "vega",
                    0.0
                )
            ),

            difference=float(
                difference
            ),

            risk_score=float(
                risk_score
            ),

        )
    def evaluate_batch(
        self,
        options: list[OptionContract],
        underlying_price: float,
        volatility: float,
        days: int,
    ) -> list[ValuationResult]:
        """
        Batch valuation.
        """


        results: list[ValuationResult] = []


        for option in options:

            result = self.evaluate(
                option,
                underlying_price,
                volatility,
                days,
            )

            results.append(
                result
            )


        return results



    def sort_by_risk(
        self,
        results: list[ValuationResult],
    ) -> list[ValuationResult]:
        """
        Sort by risk score descending.
        """


        return sorted(

            results,

            key=lambda x:
                x.risk_score,

            reverse=True,

        )



    def sort_by_difference(
        self,
        results: list[ValuationResult],
    ) -> list[ValuationResult]:
        """
        Sort by valuation difference.
        """


        return sorted(

            results,

            key=lambda x:
                abs(
                    x.premium_difference()
                ),

            reverse=True,

        )



    def result_to_dict(
        self,
        result: ValuationResult,
    ) -> dict[str, Any]:
        """
        Convert valuation result
        into dictionary.
        """


        return {

            "symbol":
                result.symbol,


            "direction":
                result.direction.value,


            "premium":
                result.premium,


            "theoretical_price":
                result.theoretical_price,


            "delta":
                result.delta,


            "gamma":
                result.gamma,


            "theta":
                result.theta,


            "vega":
                result.vega,


            "difference":
                result.difference,


            "risk_score":
                result.risk_score,

        }