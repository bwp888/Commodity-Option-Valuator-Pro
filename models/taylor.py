"""
Commodity Option Valuator Pro
=============================

Second Order Taylor Option Valuation Model

Features
--------
- Base option price
- Spot price change
- Delta effect
- Gamma effect
- First-order Taylor estimation
- Second-order Taylor estimation
- Structured estimation result
- Dictionary export
- Backward-compatible calculate() interface

Taylor Formula
--------------
V(S + dS)
=
V(S)
+
Delta * dS
+
0.5 * Gamma * dS^2

Author : Simon
Version : 1.1.0
Python : 3.12
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


from models.greeks import Greeks


# ==========================================================
# Taylor Result
# ==========================================================


@dataclass
class TaylorResult:
    """
    Taylor valuation result.
    """

    base_price: float = 0.0

    delta_adjustment: float = 0.0

    gamma_adjustment: float = 0.0

    estimated_price: float = 0.0

    # ------------------------------------------------------
    # Dictionary Export
    # ------------------------------------------------------

    def to_dict(self) -> dict[str, float]:
        """
        Convert result to dictionary.
        """

        return {
            "base_price": self.base_price,
            "delta_adjustment": self.delta_adjustment,
            "gamma_adjustment": self.gamma_adjustment,
            "estimated_price": self.estimated_price,
        }


# ==========================================================
# Taylor Valuator
# ==========================================================


class TaylorValuator:
    """
    Second-order Taylor valuation engine.

    Parameters
    ----------
    greeks:
        Greeks instance used for Delta and Gamma.

    Notes
    -----
    The class provides both the original calculation interface
    and the higher-level convenience interfaces used by the
    project test suite.
    """

    # ------------------------------------------------------
    # Initialization
    # ------------------------------------------------------

    def __init__(
        self,
        greeks: Optional[Greeks] = None,
    ) -> None:

        self.greeks = greeks

    # ======================================================
    # Basic Properties
    # ======================================================

    @property
    def base_price(self) -> float:
        """
        Current option theoretical price.
        """

        if self.greeks is None:
            return 0.0

        if hasattr(self.greeks, "bs"):
            return float(
                self.greeks.bs.price
            )

        if hasattr(self.greeks, "price"):
            return float(
                self.greeks.price
            )

        return 0.0

    # ------------------------------------------------------

    @property
    def spot(self) -> float:
        """
        Current underlying spot price.
        """

        if self.greeks is None:
            return 0.0

        if hasattr(self.greeks, "spot"):
            return float(
                self.greeks.spot
            )

        if hasattr(self.greeks, "option"):

            return float(
                self.greeks.option.spot
            )

        return 0.0

    # ------------------------------------------------------

    @property
    def delta(self) -> float:
        """
        Option Delta.
        """

        if self.greeks is None:
            return 0.0

        value = getattr(
            self.greeks,
            "delta",
            0.0,
        )

        if callable(value):
            value = value()

        return float(value)

    # ------------------------------------------------------

    @property
    def gamma(self) -> float:
        """
        Option Gamma.
        """

        if self.greeks is None:
            return 0.0

        value = getattr(
            self.greeks,
            "gamma",
            0.0,
        )

        if callable(value):
            value = value()

        return float(value)

    # ======================================================
    # Spot Change
    # ======================================================

    def spot_change(
        self,
        new_spot: float,
    ) -> float:
        """
        Calculate underlying price change.

        Parameters
        ----------
        new_spot:
            New underlying price.

        Returns
        -------
        float
            New spot minus old spot.

        Raises
        ------
        ValueError
            If new_spot is not positive.
        """

        new_spot = float(new_spot)

        if new_spot <= 0:
            raise ValueError(
                "Spot price must be positive."
            )

        return new_spot - self.spot

    # ======================================================
    # Delta Effect
    # ======================================================

    def delta_effect(
        self,
        new_spot: float,
    ) -> float:
        """
        Calculate first-order Delta effect.

        Formula
        -------
        Delta * dS
        """

        change = self.spot_change(
            new_spot
        )

        return (
            self.delta
            *
            change
        )

    # ======================================================
    # Gamma Effect
    # ======================================================

    def gamma_effect(
        self,
        new_spot: float,
    ) -> float:
        """
        Calculate second-order Gamma effect.

        Formula
        -------
        0.5 * Gamma * dS^2
        """

        change = self.spot_change(
            new_spot
        )

        return (
            0.5
            *
            self.gamma
            *
            change ** 2
        )

    # ======================================================
    # First Order
    # ======================================================

    def first_order(
        self,
        new_spot: float,
    ) -> float:
        """
        First-order Taylor estimation.

        Formula
        -------
        V1 = V0 + Delta * dS
        """

        return (
            self.base_price
            +
            self.delta_effect(
                new_spot
            )
        )

    # ======================================================
    # Second Order
    # ======================================================

    def second_order(
        self,
        new_spot: float,
    ) -> float:
        """
        Second-order Taylor estimation.

        Formula
        -------
        V2 =
            V0
            +
            Delta * dS
            +
            0.5 * Gamma * dS^2
        """

        return (
            self.base_price
            +
            self.delta_effect(
                new_spot
            )
            +
            self.gamma_effect(
                new_spot
            )
        )

    # ======================================================
    # Estimate
    # ======================================================

    def estimate(
        self,
        new_spot: float,
        current_price: Optional[float] = None,
        price_change: Optional[float] = None,
    ) -> dict[str, float]:
        """
        Calculate complete Taylor estimation.

        Parameters
        ----------
        new_spot:
            New underlying price.

        current_price:
            Optional compatibility parameter.

        price_change:
            Optional compatibility parameter.

        Returns
        -------
        dict
            Complete Taylor estimation result.
        """

        new_spot = float(new_spot)

        if new_spot <= 0:
            raise ValueError(
                "Spot price must be positive."
            )

        old_spot = self.spot

        change = (
            new_spot
            -
            old_spot
        )

        delta_effect = (
            self.delta
            *
            change
        )

        gamma_effect = (
            0.5
            *
            self.gamma
            *
            change ** 2
        )

        base_price = (
            self.base_price
            if current_price is None
            else float(current_price)
        )

        first_order_price = (
            base_price
            +
            delta_effect
        )

        second_order_price = (
            base_price
            +
            delta_effect
            +
            gamma_effect
        )

        return {
            "base_price": base_price,
            "old_spot": old_spot,
            "new_spot": new_spot,
            "spot_change": change,
            "delta_effect": delta_effect,
            "gamma_effect": gamma_effect,
            "first_order_price": first_order_price,
            "second_order_price": second_order_price,
        }

    # ======================================================
    # Calculate
    # ======================================================

    def calculate(
        self,
        current_price: float = 0.0,
        price_change: float = 0.0,
        greeks: Optional[Any] = None,
    ) -> TaylorResult:
        """
        Calculate Taylor estimation.

        This method preserves the original project interface.

        Parameters
        ----------
        current_price:
            Current option price.

        price_change:
            Underlying price change.

        greeks:
            Optional Greeks object or compatible dictionary.
        """

        if greeks is not None:
            self.greeks = greeks

        delta = self.delta
        gamma = self.gamma

        delta_adjustment = (
            delta
            *
            float(price_change)
        )

        gamma_adjustment = (
            0.5
            *
            gamma
            *
            float(price_change) ** 2
        )

        estimated_price = (
            float(current_price)
            +
            delta_adjustment
            +
            gamma_adjustment
        )

        return TaylorResult(
            base_price=float(
                current_price
            ),
            delta_adjustment=delta_adjustment,
            gamma_adjustment=gamma_adjustment,
            estimated_price=estimated_price,
        )

    # ======================================================
    # Summary
    # ======================================================

    def summary(
        self,
        new_spot: Optional[float] = None,
    ) -> dict[str, float]:
        """
        Return Taylor valuation summary.

        Parameters
        ----------
        new_spot:
            Optional new underlying price.

        If omitted, the current spot is used.

        Raises
        ------
        ValueError
            If supplied spot is not positive.
        """

        if new_spot is None:
            new_spot = self.spot

        new_spot = float(new_spot)

        if new_spot <= 0:
            raise ValueError(
                "Spot price must be positive."
            )

        result = self.estimate(
            new_spot
        )

        return result

    # ======================================================
    # Dictionary Export
    # ======================================================

    def to_dict(
        self,
        new_spot: Optional[float] = None,
    ) -> dict[str, float]:
        """
        Export Taylor estimation as dictionary.
        """

        return self.summary(
            new_spot
        )

    # ======================================================
    # String Representation
    # ======================================================

    def __str__(self) -> str:
        """
        Human-readable representation.
        """

        return (
            "TaylorValuator("
            f"base_price={self.base_price:.6f}, "
            f"spot={self.spot:.6f}, "
            f"delta={self.delta:.6f}, "
            f"gamma={self.gamma:.6f}"
            ")"
        )

    # ------------------------------------------------------

    def __repr__(self) -> str:
        """
        Developer representation.
        """

        return self.__str__()


# ==========================================================
# Public Exports
# ==========================================================

__all__ = [
    "TaylorResult",
    "TaylorValuator",
]