"""
Commodity Option Valuator Pro
=============================

Second Order Taylor Valuation Model

This module provides fast option price estimation
using Delta and Gamma approximation.

Formula
-------

V_new = V0
        + Delta * dS
        + 0.5 * Gamma * dS^2


Author : Simon
Version : 1.0.0
Python : 3.12
"""

from __future__ import annotations

from typing import Any


from models.greeks import Greeks



# ==========================================================
# Taylor Valuation Engine
# ==========================================================


class TaylorValuator:
    """
    Second order Taylor option valuation engine.

    Parameters
    ----------
    greeks:
        Greeks calculation engine.

    Notes
    -----
    Uses existing Delta and Gamma values.
    Does not recalculate Black-Scholes.
    """


    def __init__(
        self,
        greeks: Greeks,
    ) -> None:
        """
        Initialize Taylor model.

        Parameters
        ----------
        greeks:
            Initialized Greeks object.
        """

        self.greeks = greeks



    # ------------------------------------------------------
    # Basic Properties
    # ------------------------------------------------------


    @property
    def option(self):
        """
        Underlying option.
        """

        return self.greeks.option



    # ------------------------------------------------------


    @property
    def base_price(self) -> float:
        """
        Current option theoretical price.
        """

        return self.greeks.bs.price



    # ------------------------------------------------------


    @property
    def spot(self) -> float:
        """
        Current underlying price.
        """

        return self.greeks.spot



    # ------------------------------------------------------


    @property
    def delta(self) -> float:
        """
        Delta.
        """

        return self.greeks.delta



    # ------------------------------------------------------


    @property
    def gamma(self) -> float:
        """
        Gamma.
        """

        return self.greeks.gamma
    # ------------------------------------------------------
    # Spot Change
    # ------------------------------------------------------

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
            dS
        """

        return new_spot - self.spot


    # ------------------------------------------------------
    # Delta Contribution
    # ------------------------------------------------------

    def delta_effect(
        self,
        new_spot: float,
    ) -> float:
        """
        First-order Taylor contribution.

        Formula
        -------
        Delta * dS
        """

        dS = self.spot_change(
            new_spot
        )

        return (
            self.delta
            *
            dS
        )


    # ------------------------------------------------------
    # Gamma Contribution
    # ------------------------------------------------------

    def gamma_effect(
        self,
        new_spot: float,
    ) -> float:
        """
        Second-order Gamma contribution.

        Formula
        -------
        0.5 * Gamma * dS^2
        """

        dS = self.spot_change(
            new_spot
        )

        return (
            0.5
            *
            self.gamma
            *
            dS ** 2
        )


    # ------------------------------------------------------
    # First Order Taylor
    # ------------------------------------------------------

    def first_order(
        self,
        new_spot: float,
    ) -> float:
        """
        First-order Taylor estimation.

        Formula
        -------
        V0 + Delta*dS
        """

        return (
            self.base_price
            +
            self.delta_effect(
                new_spot
            )
        )


    # ------------------------------------------------------
    # Second Order Taylor
    # ------------------------------------------------------

    def second_order(
        self,
        new_spot: float,
    ) -> float:
        """
        Second-order Taylor estimation.

        Formula
        -------
        V0
        + Delta*dS
        + 0.5*Gamma*dS²
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


    # ------------------------------------------------------
    # Main Estimator
    # ------------------------------------------------------

    def estimate(
        self,
        new_spot: float,
    ) -> dict[str, float]:
        """
        Estimate option price after spot movement.

        Parameters
        ----------
        new_spot:
            New underlying price.

        Returns
        -------
        dict
            Taylor estimation result.
        """

        dS = self.spot_change(
            new_spot
        )


        delta_value = self.delta_effect(
            new_spot
        )


        gamma_value = self.gamma_effect(
            new_spot
        )


        return {
            "base_price": self.base_price,

            "old_spot": self.spot,

            "new_spot": new_spot,

            "spot_change": dS,

            "delta_effect": delta_value,

            "gamma_effect": gamma_value,

            "first_order_price": (
                self.first_order(
                    new_spot
                )
            ),

            "second_order_price": (
                self.second_order(
                    new_spot
                )
            ),
        }
    # ------------------------------------------------------
    # Validation
    # ------------------------------------------------------

    def validate_spot(
        self,
        new_spot: float,
    ) -> None:
        """
        Validate new underlying price.

        Parameters
        ----------
        new_spot:
            Target spot price.

        Raises
        ------
        ValueError
            If spot price is invalid.
        """

        if new_spot <= 0:

            raise ValueError(
                "Spot price must be positive."
            )


    # ------------------------------------------------------
    # Summary
    # ------------------------------------------------------

    def summary(
        self,
        new_spot: float,
    ) -> dict[str, Any]:
        """
        Return complete Taylor valuation result.

        Parameters
        ----------
        new_spot:
            Target underlying price.

        Returns
        -------
        dict
            Taylor estimation summary.
        """

        self.validate_spot(
            new_spot
        )

        return self.estimate(
            new_spot
        )


    # ------------------------------------------------------
    # Dictionary Export
    # ------------------------------------------------------

    def to_dict(
        self,
        new_spot: float,
    ) -> dict[str, Any]:
        """
        Export Taylor result.

        Parameters
        ----------
        new_spot:
            Target price.

        Returns
        -------
        dict
        """

        return self.summary(
            new_spot
        )


    # ------------------------------------------------------
    # String Representation
    # ------------------------------------------------------

    def __str__(self) -> str:
        """
        Human-readable representation.
        """

        return (
            "TaylorValuator("
            f"spot={self.spot:.4f}, "
            f"price={self.base_price:.6f}"
            ")"
        )


    # ------------------------------------------------------

    def __repr__(self) -> str:
        """
        Developer representation.
        """

        return (
            "TaylorValuator("
            f"option={self.option!r}"
            ")"
        )


# ==========================================================
# Public Exports
# ==========================================================

__all__ = [
    "TaylorValuator",
]