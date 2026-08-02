"""
Commodity Option Valuator Pro
=============================

Greeks Calculation Engine

This module provides first-order option Greeks based on the
Black-Scholes pricing model.

Implemented Greeks
------------------
- Delta
- Gamma
- Theta (per day, 365-day convention)
- Vega
- Rho
- Elasticity (Lambda)

Author : Simon
Version : 1.0.0
Python  : 3.12
"""

from __future__ import annotations

from typing import Any

from models.black_scholes import BlackScholes


# ==========================================================
# Greeks Engine
# ==========================================================


class Greeks:
    """
    Black-Scholes Greeks calculation engine.

    Parameters
    ----------
    black_scholes
        Initialized BlackScholes pricing engine.

    Notes
    -----
    This class never recalculates d1, d2 or other intermediate
    variables.

    All mathematical values are reused directly from the
    BlackScholes engine.
    """

    DAYS_PER_YEAR: float = 365.0

    # ------------------------------------------------------

    def __init__(
        self,
        black_scholes: BlackScholes,
    ) -> None:
        """
        Initialize Greeks engine.

        Parameters
        ----------
        black_scholes
            Initialized pricing engine.
        """

        self.bs = black_scholes

    # ------------------------------------------------------
    # Public Shortcuts
    # ------------------------------------------------------

    @property
    def option(self):
        """
        Return underlying Option object.
        """

        return self.bs.option

    # ------------------------------------------------------

    @property
    def spot(self) -> float:
        """
        Underlying spot price.
        """

        return self.option.spot

    # ------------------------------------------------------

    @property
    def strike(self) -> float:
        """
        Strike price.
        """

        return self.option.strike

    # ------------------------------------------------------

    @property
    def maturity(self) -> float:
        """
        Time to maturity (years).
        """

        return self.option.maturity

    # ------------------------------------------------------

    @property
    def rate(self) -> float:
        """
        Risk-free interest rate.
        """

        return self.option.rate

    # ------------------------------------------------------

    @property
    def volatility(self) -> float:
        """
        Annualized volatility.
        """

        return self.option.volatility

    # ------------------------------------------------------

    @property
    def d1(self) -> float:
        """
        Cached Black-Scholes d1.
        """

        return self.bs.d1

    # ------------------------------------------------------

    @property
    def d2(self) -> float:
        """
        Cached Black-Scholes d2.
        """

        return self.bs.d2

    # ------------------------------------------------------

    @property
    def pdf_d1(self) -> float:
        """
        Standard normal PDF evaluated at d1.
        """

        return self.bs.pdf(self.d1)

    # ------------------------------------------------------

    @property
    def discount_factor(self) -> float:
        """
        Discount factor.

        exp(-rT)
        """

        return self.bs.discount_factor

    # ------------------------------------------------------

    @property
    def is_call(self) -> bool:
        """
        True if option is Call.
        """

        return self.option.is_call

    # ------------------------------------------------------

    @property
    def is_put(self) -> bool:
        """
        True if option is Put.
        """

        return self.option.is_put
            # ------------------------------------------------------
    # Delta
    # ------------------------------------------------------

    @property
    def delta(self) -> float:
        """
        First-order sensitivity to the underlying price.

        Returns
        -------
        float
            Delta of the option.
        """

        if self.is_call:
            return self.bs.cdf(self.d1)

        return self.bs.cdf(self.d1) - 1.0

    # ------------------------------------------------------
    # Gamma
    # ------------------------------------------------------

    @property
    def gamma(self) -> float:
        """
        Second-order sensitivity to the underlying price.

        Returns
        -------
        float
            Gamma of the option.
        """

        denominator = (
            self.spot
            * self.volatility
            * (self.maturity ** 0.5)
        )

        return self.pdf_d1 / denominator

    # ------------------------------------------------------
    # Common Factors
    # ------------------------------------------------------

    @property
    def sqrt_maturity(self) -> float:
        """
        Square root of maturity.
        """

        return self.maturity ** 0.5

    # ------------------------------------------------------

    @property
    def vega_factor(self) -> float:
        """
        Common factor shared by Vega and Theta.

        S · φ(d1) · √T
        """

        return (
            self.spot
            * self.pdf_d1
            * self.sqrt_maturity
        )

    # ------------------------------------------------------

    @property
    def theta_decay(self) -> float:
        """
        Common decay term.

        S · φ(d1) · σ / (2√T)
        """

        return (
            self.spot
            * self.pdf_d1
            * self.volatility
            / (
                2.0
                * self.sqrt_maturity
            )
        )
    # ------------------------------------------------------
    # Theta
    # ------------------------------------------------------

    @property
    def theta(self) -> float:
        """
        Daily Theta using the 365-day convention.

        Returns
        -------
        float
            Daily time decay.
        """

        if self.is_call:

            annual_theta = (
                -self.theta_decay
                - self.rate
                * self.strike
                * self.discount_factor
                * self.bs.cdf(self.d2)
            )

        else:

            annual_theta = (
                -self.theta_decay
                + self.rate
                * self.strike
                * self.discount_factor
                * self.bs.cdf(-self.d2)
            )

        return annual_theta / self.DAYS_PER_YEAR

    # ------------------------------------------------------
    # Vega
    # ------------------------------------------------------

    @property
    def vega(self) -> float:
        """
        Vega.

        Returns
        -------
        float
            Sensitivity to volatility.

        Notes
        -----
        Returned for a volatility change of 1.00
        (100%), not 1%.
        """

        return self.vega_factor

    # ------------------------------------------------------
    # Rho
    # ------------------------------------------------------

    @property
    def rho(self) -> float:
        """
        Rho.

        Returns
        -------
        float
            Sensitivity to interest rate.
        """

        factor = (
            self.strike
            * self.maturity
            * self.discount_factor
        )

        if self.is_call:

            return (
                factor
                * self.bs.cdf(self.d2)
            )

        return (
            -factor
            * self.bs.cdf(-self.d2)
        )

    # ------------------------------------------------------
    # Elasticity (Lambda)
    # ------------------------------------------------------

    @property
    def elasticity(self) -> float:
        """
        Elasticity (Lambda).

        Returns
        -------
        float
            Percentage leverage.

        Notes
        -----
        Lambda = Delta × Spot / Option Price
        """

        price = self.bs.price

        if abs(price) < 1.0e-12:
            return 0.0

        return (
            self.delta
            * self.spot
            / price
        )
    # ------------------------------------------------------
    # Summary
    # ------------------------------------------------------

    def summary(self) -> dict[str, Any]:
        """
        Return Greeks summary.

        Returns
        -------
        dict
            Greeks information.
        """

        return {
            "option_type": (
                self.option.option_type.value
            ),
            "spot": self.spot,
            "strike": self.strike,
            "maturity": self.maturity,
            "rate": self.rate,
            "volatility": self.volatility,

            "price": self.bs.price,

            "delta": self.delta,
            "gamma": self.gamma,
            "theta": self.theta,
            "vega": self.vega,
            "rho": self.rho,

            "elasticity": self.elasticity,
        }

    # ------------------------------------------------------
    # Dictionary Export
    # ------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Convert Greeks result to dictionary.

        Returns
        -------
        dict
        """

        return self.summary()

    # ------------------------------------------------------
    # String Representation
    # ------------------------------------------------------

    def __str__(self) -> str:
        """
        Human-readable representation.
        """

        return (
            "Greeks("
            f"type={self.option.option_type.value}, "
            f"delta={self.delta:.6f}, "
            f"gamma={self.gamma:.6f}, "
            f"theta={self.theta:.6f}"
            ")"
        )

    # ------------------------------------------------------

    def __repr__(self) -> str:
        """
        Developer representation.
        """

        return (
            "Greeks("
            f"option={self.option!r}"
            ")"
        )


# ==========================================================
# Public Exports
# ==========================================================

__all__ = [
    "Greeks",
]