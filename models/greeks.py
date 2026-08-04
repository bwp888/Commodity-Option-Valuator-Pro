"""
Commodity Option Valuator Pro

Greeks calculation module.

Support:
- Delta
- Gamma
- Theta (365 days)
- Vega
- Rho
- Elasticity
"""

from __future__ import annotations

import math

from scipy.stats import norm

from models.option import (
    OptionType,
    OptionDirection,
)

from models.black_scholes import BlackScholes


class Greeks:
    """
    Option Greeks calculator.
    """

    DAYS_PER_YEAR = 365


    def __init__(self, option):

        """
        Accept:

        Option
        or
        BlackScholes instance
        """

        if hasattr(option, "option"):

            # BlackScholes instance
            self.bs = option

            self.option = option.option

        else:

            # Option instance
            self.option = option

            self.bs = BlackScholes(option)


        self.spot = float(
            self.option.spot
        )

        self.strike = float(
            self.option.strike
        )

        self.maturity = float(
            self.option.maturity
        )

        self.rate = float(
            self.option.rate
        )

        self.volatility = float(
            self.option.volatility
        )


    @property
    def _d1(self):

        return (
            math.log(
                self.spot / self.strike
            )
            +
            (
                self.rate
                +
                self.volatility ** 2 / 2
            )
            *
            self.maturity
        ) / (
            self.volatility
            *
            math.sqrt(self.maturity)
        )


    @property
    def _d2(self):

        return (
            self._d1
            -
            self.volatility
            *
            math.sqrt(self.maturity)
        )


    @property
    def delta(self):

        if self.option.option_type == OptionType.CALL:

            value = norm.cdf(
                self._d1
            )

        else:

            value = (
                norm.cdf(self._d1)
                -
                1
            )


        if self.option.direction == OptionDirection.SHORT:

            value = -value


        return float(value)



    @property
    def gamma(self):

        value = (
            norm.pdf(self._d1)
            /
            (
                self.spot
                *
                self.volatility
                *
                math.sqrt(self.maturity)
            )
        )

        return float(value)



    @property
    def vega(self):

        value = (
            self.spot
            *
            norm.pdf(self._d1)
            *
            math.sqrt(self.maturity)
        )


        if self.option.direction == OptionDirection.SHORT:

            value = -value


        return float(value)



    @property
    def theta(self):

        first = (
            -
            self.spot
            *
            norm.pdf(self._d1)
            *
            self.volatility
            /
            (
                2
                *
                math.sqrt(self.maturity)
            )
        )


        if self.option.option_type == OptionType.CALL:

            second = (
                self.rate
                *
                self.strike
                *
                math.exp(
                    -self.rate * self.maturity
                )
                *
                norm.cdf(
                    self._d2
                )
            )

            value = first - second


        else:

            second = (
                self.rate
                *
                self.strike
                *
                math.exp(
                    -self.rate * self.maturity
                )
                *
                norm.cdf(
                    -self._d2
                )
            )

            value = first + second



        value = (
            value
            /
            self.DAYS_PER_YEAR
        )


        if self.option.direction == OptionDirection.SHORT:

            value = -value


        return float(value)



    @property
    def rho(self):

        if self.option.option_type == OptionType.CALL:

            value = (
                self.strike
                *
                self.maturity
                *
                math.exp(
                    -self.rate * self.maturity
                )
                *
                norm.cdf(
                    self._d2
                )
            )

        else:

            value = (
                -
                self.strike
                *
                self.maturity
                *
                math.exp(
                    -self.rate * self.maturity
                )
                *
                norm.cdf(
                    -self._d2
                )
            )


        if self.option.direction == OptionDirection.SHORT:

            value = -value


        return float(value)



    @property
    def elasticity(self):

        """
        Price elasticity.
        """

        if self.bs.price == 0:

            return 0.0


        return float(
            self.delta
            *
            self.spot
            /
            self.bs.price
        )



    def summary(self):

        """
        Complete Greeks summary.
        """

        return {

            "price": float(
                self.bs.price
            ),

            "delta": self.delta,

            "gamma": self.gamma,

            "theta": self.theta,

            "vega": self.vega,

            "rho": self.rho,

            "elasticity": self.elasticity,

        }



    def to_dict(self):

        return self.summary()



    def __str__(self):

        return (
            "Greeks("
            f"price={self.bs.price:.6f}, "
            f"delta={self.delta:.6f}, "
            f"gamma={self.gamma:.6f}, "
            f"theta={self.theta:.6f}, "
            f"vega={self.vega:.6f}, "
            f"rho={self.rho:.6f})"
        )


    def __repr__(self):

        return self.__str__()