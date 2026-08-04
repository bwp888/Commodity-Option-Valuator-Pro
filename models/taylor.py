"""
Commodity Option Valuator Pro

Second Order Taylor Option Valuation Model

Version : 1.0.1
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


from models.greeks import Greeks


@dataclass
class TaylorResult:
    """
    Taylor valuation result.
    """

    base_price: float = 0.0

    delta_adjustment: float = 0.0

    gamma_adjustment: float = 0.0

    estimated_price: float = 0.0



class TaylorValuator:
    """
    Second order Taylor valuation engine.

    Formula:

    V(S+dS)

    =
    V(S)
    +
    Delta*dS
    +
    0.5*Gamma*dS²
    """



    def __init__(
        self,
        greeks: Optional[Greeks] = None,
    ) -> None:

        self.greeks = greeks



    def calculate(
        self,
        current_price: float = 0.0,
        price_change: float = 0.0,
        greeks: Optional[Any] = None,
    ) -> TaylorResult:
        """
        Calculate Taylor estimation.
        """


        if greeks is not None:
            self.greeks = greeks


        delta = 0.0
        gamma = 0.0


        if self.greeks is not None:

            if hasattr(
                self.greeks,
                "delta"
            ):
                delta = float(
                    self.greeks.delta
                )

            elif isinstance(
                self.greeks,
                dict
            ):
                delta = float(
                    self.greeks.get(
                        "delta",
                        0
                    )
                )



            if hasattr(
                self.greeks,
                "gamma"
            ):
                gamma = float(
                    self.greeks.gamma
                )

            elif isinstance(
                self.greeks,
                dict
            ):
                gamma = float(
                    self.greeks.get(
                        "gamma",
                        0
                    )
                )


        delta_adjustment = (
            delta
            *
            price_change
        )


        gamma_adjustment = (
            0.5
            *
            gamma
            *
            price_change ** 2
        )


        estimated_price = (
            current_price
            +
            delta_adjustment
            +
            gamma_adjustment
        )


        return TaylorResult(

            base_price=current_price,

            delta_adjustment=delta_adjustment,

            gamma_adjustment=gamma_adjustment,

            estimated_price=estimated_price,
        )



    @staticmethod
    def estimate(
        greeks: Greeks,
        current_price: float,
        price_change: float,
    ) -> TaylorResult:


        model = TaylorValuator(
            greeks
        )


        return model.calculate(
            current_price=current_price,
            price_change=price_change,
        )



__all__ = [
    "TaylorResult",
    "TaylorValuator",
]