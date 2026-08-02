"""
Commodity Option Valuator Pro
=============================

Black-Scholes Pricing Engine

This module provides the pricing engine for European
commodity options based on the Black-Scholes model.

Author : Simon
Version : 1.0.0
Python : 3.12
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from models.option import Option


# ==========================================================
# Internal Calculation Cache
# ==========================================================


@dataclass(slots=True, frozen=True)
class _BSCache:
    """
    Internal calculation cache.

    This object stores intermediate values that are reused
    by pricing, Greeks, implied volatility and Taylor
    expansion calculations.
    """

    d1: float
    d2: float

    sigma: float
    sigma_sqrt_t: float

    discount_factor: float

    forward_price: float


# ==========================================================
# Black-Scholes Engine
# ==========================================================


class BlackScholes:
    """
    Black-Scholes pricing engine.

    One engine instance corresponds to one Option object.

    All intermediate variables are calculated only once and
    cached for later reuse.
    """

    SQRT_2 = math.sqrt(2.0)

    SQRT_2PI = math.sqrt(
        2.0 * math.pi
    )

    # ------------------------------------------------------

    def __init__(
        self,
        option: Option,
    ) -> None:
        """
        Parameters
        ----------
        option
            European option contract.
        """

        self.option = option

        self._validate()

        self._cache = self._compute()

    # ------------------------------------------------------
    # Normal Distribution
    # ------------------------------------------------------

    @staticmethod
    def pdf(
        x: float,
    ) -> float:
        """
        Standard normal probability density function.
        """

        return (
            math.exp(
                -0.5 * x * x
            )
            / BlackScholes.SQRT_2PI
        )

    # ------------------------------------------------------

    @staticmethod
    def cdf(
        x: float,
    ) -> float:
        """
        Standard normal cumulative distribution function.
        """

        return (
            0.5
            * (
                1.0
                + math.erf(
                    x
                    / BlackScholes.SQRT_2
                )
            )
        )

    # ------------------------------------------------------
    # Validation
    # ------------------------------------------------------

    def _validate(
        self,
    ) -> None:
        """
        Validate option parameters.
        """

        values = (
            self.option.spot,
            self.option.strike,
            self.option.maturity,
            self.option.rate,
            self.option.volatility,
        )

        if not all(
            math.isfinite(v)
            for v in values
        ):
            raise ValueError(
                "All option parameters must be finite."
            )

        if self.option.spot <= 0.0:
            raise ValueError(
                "Spot price must be greater than zero."
            )

        if self.option.strike <= 0.0:
            raise ValueError(
                "Strike price must be greater than zero."
            )

        if self.option.maturity <= 0.0:
            raise ValueError(
                "Maturity must be greater than zero."
            )

        if self.option.volatility <= 0.0:
            raise ValueError(
                "Volatility must be greater than zero."
            )
    # ------------------------------------------------------
    # Internal Calculation
    # ------------------------------------------------------

    def _compute(self) -> _BSCache:
        """
        Compute and cache all intermediate variables.

        Returns
        -------
        _BSCache
            Cached Black-Scholes variables.
        """

        spot = self.option.spot
        strike = self.option.strike
        maturity = self.option.maturity
        rate = self.option.rate
        sigma = self.option.volatility

        sigma_sqrt_t = sigma * math.sqrt(maturity)

        ln_sk = math.log(
            spot / strike
        )

        variance = sigma * sigma

        d1 = (
            ln_sk
            + (
                rate
                + 0.5 * variance
            )
            * maturity
        ) / sigma_sqrt_t

        d2 = (
            d1
            - sigma_sqrt_t
        )

        discount_factor = math.exp(
            -rate * maturity
        )

        forward_price = (
            spot
            * math.exp(
                rate * maturity
            )
        )

        return _BSCache(
            d1=d1,
            d2=d2,
            sigma=sigma,
            sigma_sqrt_t=sigma_sqrt_t,
            discount_factor=discount_factor,
            forward_price=forward_price,
        )

    # ------------------------------------------------------
    # Cached Properties
    # ------------------------------------------------------

    @property
    def d1(self) -> float:
        """
        Black-Scholes d1.
        """

        return self._cache.d1

    # ------------------------------------------------------

    @property
    def d2(self) -> float:
        """
        Black-Scholes d2.
        """

        return self._cache.d2

    # ------------------------------------------------------

    @property
    def sigma(self) -> float:
        """
        Annual volatility.
        """

        return self._cache.sigma

    # ------------------------------------------------------

    @property
    def sigma_sqrt_t(self) -> float:
        """
        σ√T
        """

        return self._cache.sigma_sqrt_t

    # ------------------------------------------------------

    @property
    def discount_factor(self) -> float:
        """
        e^(-rT)
        """

        return self._cache.discount_factor

    # ------------------------------------------------------

    @property
    def discount_strike(self) -> float:
        """
        Present value of strike price.
        """

        return (
            self.option.strike
            * self.discount_factor
        )

    # ------------------------------------------------------

    @property
    def forward_price(self) -> float:
        """
        Risk-neutral forward price.
        """

        return self._cache.forward_price

    # ------------------------------------------------------

    @property
    def moneyness(self) -> float:
        """
        Spot / Strike ratio.
        """

        return (
            self.option.spot
            / self.option.strike
        )
    # ------------------------------------------------------
    # Pricing
    # ------------------------------------------------------

    @property
    def call_price(self) -> float:
        """
        Black-Scholes Call option price.

        Returns
        -------
        float
        """

        s = self.option.spot

        pv_k = self.discount_strike

        return (
            s
            * self.cdf(self.d1)
            - pv_k
            * self.cdf(self.d2)
        )

    # ------------------------------------------------------

    @property
    def put_price(self) -> float:
        """
        Black-Scholes Put option price.

        Returns
        -------
        float
        """

        s = self.option.spot

        pv_k = self.discount_strike

        return (
            pv_k
            * self.cdf(-self.d2)
            - s
            * self.cdf(-self.d1)
        )

    # ------------------------------------------------------

    @property
    def price(self) -> float:
        """
        Return option price according to option type.

        Returns
        -------
        float
        """

        if self.option.is_call:
            return self.call_price

        return self.put_price

    # ------------------------------------------------------

    @property
    def intrinsic_value(self) -> float:
        """
        Intrinsic value.

        Returns
        -------
        float
        """

        if self.option.is_call:
            return max(
                self.option.spot
                - self.option.strike,
                0.0,
            )

        return max(
            self.option.strike
            - self.option.spot,
            0.0,
        )

    # ------------------------------------------------------

    @property
    def time_value(self) -> float:
        """
        Time value.

        Returns
        -------
        float
        """

        return max(
            self.price
            - self.intrinsic_value,
            0.0,
        )
    # ------------------------------------------------------
    # Option State
    # ------------------------------------------------------

    @property
    def is_in_the_money(self) -> bool:
        """
        Return True if the option is in-the-money.
        """

        if self.option.is_call:
            return (
                self.option.spot
                > self.option.strike
            )

        return (
            self.option.spot
            < self.option.strike
        )

    # ------------------------------------------------------

    @property
    def is_out_of_the_money(self) -> bool:
        """
        Return True if the option is out-of-the-money.
        """

        return not (
            self.is_in_the_money
            or self.is_at_the_money
        )

    # ------------------------------------------------------

    @property
    def is_at_the_money(self) -> bool:
        """
        Return True if the option is approximately
        at-the-money.
        """

        return math.isclose(
            self.option.spot,
            self.option.strike,
            rel_tol=1.0e-8,
            abs_tol=1.0e-8,
        )

    # ------------------------------------------------------
    # Financial Analysis
    # ------------------------------------------------------

    @property
    def put_call_parity(self) -> float:
        """
        Verify put-call parity.

        Returns
        -------
        float

        Notes
        -----
        Call - Put = S - K * exp(-rT)

        A result close to zero indicates the pricing
        satisfies put-call parity.
        """

        parity = (
            self.call_price
            - self.put_price
            - (
                self.option.spot
                - self.discount_strike
            )
        )

        return parity

    # ------------------------------------------------------

    def summary(self) -> dict[str, float | bool | str]:
        """
        Return pricing summary.

        Returns
        -------
        dict
        """

        return {
            "option_type": self.option.option_type.value,
            "spot": self.option.spot,
            "strike": self.option.strike,
            "maturity": self.option.maturity,
            "rate": self.option.rate,
            "volatility": self.option.volatility,
            "d1": self.d1,
            "d2": self.d2,
            "forward_price": self.forward_price,
            "discount_factor": self.discount_factor,
            "call_price": self.call_price,
            "put_price": self.put_price,
            "price": self.price,
            "intrinsic_value": self.intrinsic_value,
            "time_value": self.time_value,
            "is_itm": self.is_in_the_money,
            "is_atm": self.is_at_the_money,
            "is_otm": self.is_out_of_the_money,
            "put_call_parity": self.put_call_parity,
        }
    # ------------------------------------------------------

    def __str__(self) -> str:
        """
        Human-readable representation.
        """

        return (
            f"BlackScholes("
            f"type={self.option.option_type.value}, "
            f"price={self.price:.6f})"
        )

    # ------------------------------------------------------

    def __repr__(self) -> str:
        """
        Developer representation.
        """

        return (
            "BlackScholes("
            f"option={self.option!r}"
            ")"
        )


# ==========================================================
# Public Exports
# ==========================================================

__all__ = [
    "BlackScholes",
]