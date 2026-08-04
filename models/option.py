"""
Option models for Commodity Option Valuator Pro
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class OptionType(Enum):
    CALL = "CALL"
    PUT = "PUT"


class OptionDirection(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class Option:
    """
    Commodity option contract model.
    """

    symbol: str = ""

    option_type: OptionType | str = OptionType.CALL

    direction: OptionDirection | str = OptionDirection.LONG

    spot: float = 0.0

    strike: float = 0.0

    maturity: float = 0.0

    rate: float = 0.025

    volatility: float = 0.20


    def __post_init__(self):

        if isinstance(self.option_type, str):

            self.option_type = OptionType(
                self.option_type.upper()
            )

        if isinstance(self.direction, str):

            self.direction = OptionDirection(
                self.direction.upper()
            )


    @property
    def is_call(self) -> bool:
        return self.option_type == OptionType.CALL


    @property
    def is_put(self) -> bool:
        return self.option_type == OptionType.PUT


    @property
    def is_long(self) -> bool:
        return self.direction == OptionDirection.LONG


    @property
    def is_short(self) -> bool:
        return self.direction == OptionDirection.SHORT


    def validate(self) -> bool:

        if self.spot < 0:
            return False

        if self.strike < 0:
            return False

        if self.maturity < 0:
            return False

        if self.volatility < 0:
            return False

        return True


    def to_dict(self) -> dict[str, Any]:

        return {

            "symbol": self.symbol,

            "option_type":
                self.option_type.value,

            "direction":
                self.direction.value,

            "spot":
                self.spot,

            "strike":
                self.strike,

            "maturity":
                self.maturity,

            "rate":
                self.rate,

            "volatility":
                self.volatility,

        }


    def __str__(self) -> str:

        return (
            f"{self.symbol}-"
            f"{self.option_type.value}-"
            f"{self.direction.value}"
        )


# Compatibility name
OptionContract = Option