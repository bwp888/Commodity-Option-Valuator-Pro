"""
Commodity Option Valuator Pro
=============================

Implied Volatility Solver

This module calculates implied volatility from market option prices.

Algorithm
---------
Brent root finding algorithm.

Features
--------
- European Call IV
- European Put IV
- Market price validation
- Stable numerical solving

Author : Simon
Version : 1.0.0
Python : 3.12
"""

from __future__ import annotations

from typing import Any


from scipy.optimize import brentq


from models.black_scholes import BlackScholes
from models.option import Option


# ==========================================================
# Implied Volatility Engine
# ==========================================================


class ImpliedVolatility:
    """
    Calculate implied volatility from option market price.

    Parameters
    ----------
    option:
        Option contract.

    market_price:
        Observed market option price.

    Notes
    -----
    The solver finds volatility σ satisfying:

        BlackScholes(option, σ).price = market_price
    """

    # Numerical boundaries

    MIN_VOLATILITY: float = 1.0e-6

    MAX_VOLATILITY: float = 5.0

    PRICE_TOLERANCE: float = 1.0e-10


    # ------------------------------------------------------

    def __init__(
        self,
        option: Option,
        market_price: float,
    ) -> None:
        """
        Initialize IV solver.

        Parameters
        ----------
        option:
            Option contract.

        market_price:
            Market observed price.
        """

        self.option = option

        self.market_price = market_price


    # ------------------------------------------------------
    # Basic Properties
    # ------------------------------------------------------


    @property
    def spot(self) -> float:
        """
        Underlying price.
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
        Time to maturity.
        """

        return self.option.maturity


    # ------------------------------------------------------


    @property
    def rate(self) -> float:
        """
        Risk-free rate.
        """

        return self.option.rate


    # ------------------------------------------------------


    @property
    def is_call(self) -> bool:
        """
        Whether option is Call.
        """

        return self.option.is_call


    # ------------------------------------------------------


    @property
    def is_put(self) -> bool:
        """
        Whether option is Put.
        """

        return self.option.is_put


    # ------------------------------------------------------


    @property
    def intrinsic_value(self) -> float:
        """
        Option intrinsic value.
        """

        if self.is_call:

            return max(
                self.spot - self.strike,
                0.0,
            )

        return max(
            self.strike - self.spot,
            0.0,
        )


    # ------------------------------------------------------


    @property
    def initial_volatility(self) -> float:
        """
        Initial volatility guess.

        Used for displaying or debugging.
        """

        return 0.20
    # ------------------------------------------------------
    # Market Price Validation
    # ------------------------------------------------------

    def validate_market_price(self) -> None:
        """
        Validate market option price.

        Raises
        ------
        ValueError
            If market price is outside valid range.
        """

        if self.market_price <= 0:

            raise ValueError(
                "Market price must be positive."
            )


        if self.market_price < self.intrinsic_value:

            raise ValueError(
                "Market price cannot be below intrinsic value."
            )


    # ------------------------------------------------------
    # Black-Scholes Price With Volatility
    # ------------------------------------------------------

    def price_with_volatility(
        self,
        volatility: float,
    ) -> float:
        """
        Calculate option price under given volatility.

        Parameters
        ----------
        volatility:
            Trial volatility.

        Returns
        -------
        float
            Black-Scholes price.
        """
        temp_option = Option(
        option_type=self.option.option_type,
        spot=self.option.spot,
        strike=self.option.strike,
        maturity=self.option.maturity,
        rate=self.option.rate,
        volatility=volatility,
        )
        bs = BlackScholes(
            temp_option
        )


        return bs.price


    # ------------------------------------------------------
    # Root Function
    # ------------------------------------------------------

    def objective(
        self,
        volatility: float,
    ) -> float:
        """
        Root function.

        Solve:

            BS_price(volatility)
            -
            market_price
            = 0
        """

        return (
            self.price_with_volatility(
                volatility
            )
            -
            self.market_price
        )


    # ------------------------------------------------------
    # Solve IV
    # ------------------------------------------------------

    def solve(self) -> float:
        """
        Calculate implied volatility.

        Returns
        -------
        float
            Annualized implied volatility.

        Raises
        ------
        ValueError
            If no solution exists.
        """

        self.validate_market_price()


        low_price = self.price_with_volatility(
            self.MIN_VOLATILITY
        )

        high_price = self.price_with_volatility(
            self.MAX_VOLATILITY
        )


        if (
            self.market_price < low_price
            or
            self.market_price > high_price
        ):

            raise ValueError(
                "Market price outside solver range."
            )


        volatility = brentq(
            self.objective,
            self.MIN_VOLATILITY,
            self.MAX_VOLATILITY,
            xtol=self.PRICE_TOLERANCE,
        )


        return volatility


    # ------------------------------------------------------
    # Cached Result
    # ------------------------------------------------------

    @property
    def implied_volatility(self) -> float:
        """
        Return solved implied volatility.

        Returns
        -------
        float
            Annualized volatility.
        """

        return self.solve()
    # ------------------------------------------------------
    # Cached Solver Result
    # ------------------------------------------------------

    def solve_cached(self) -> float:
        """
        Solve IV with cache.

        Returns
        -------
        float
            Implied volatility.
        """

        if hasattr(
            self,
            "_iv_cache",
        ):

            return self._iv_cache


        self._iv_cache = self.solve()


        return self._iv_cache


    # ------------------------------------------------------
    # Summary
    # ------------------------------------------------------

    def summary(self) -> dict[str, Any]:
        """
        Return complete IV information.

        Returns
        -------
        dict
            Solver result summary.
        """

        return {
            "option_type": (
                self.option.option_type.value
            ),

            "spot": self.spot,

            "strike": self.strike,

            "maturity": self.maturity,

            "rate": self.rate,

            "market_price": self.market_price,

            "intrinsic_value": (
                self.intrinsic_value
            ),

            "implied_volatility": (
                self.solve_cached()
            ),
        }


    # ------------------------------------------------------
    # Dictionary Export
    # ------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Export result as dictionary.
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
            "ImpliedVolatility("
            f"type={self.option.option_type.value}, "
            f"market_price={self.market_price:.6f}, "
            f"iv={self.solve_cached():.6f}"
            ")"
        )


    # ------------------------------------------------------

    def __repr__(self) -> str:
        """
        Developer representation.
        """

        return (
            "ImpliedVolatility("
            f"option={self.option!r}, "
            f"market_price={self.market_price}"
            ")"
        )


# ==========================================================
# Public Exports
# ==========================================================

__all__ = [
    "ImpliedVolatility",
]