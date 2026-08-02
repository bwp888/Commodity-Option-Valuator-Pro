"""
Commodity Option Valuator Pro
=============================

Option Data Model

This module defines the immutable option contract used
throughout the entire application.

Author : Simon
Version: 1.0.0
Python : 3.12
"""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from enum import Enum
from typing import Any


# ==========================================================
# Option Type
# ==========================================================


class OptionType(str, Enum):
    """
    Supported option types.
    """

    CALL = "CALL"
    PUT = "PUT"

    @classmethod
    def from_value(
        cls,
        value: str | "OptionType",
    ) -> "OptionType":
        """
        Convert string or OptionType into OptionType.

        Examples
        --------
        CALL
        Call
        call
        PUT
        Put
        put
        """

        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "option_type must be str or OptionType."
            )

        value = value.strip().upper()

        try:
            return cls(value)

        except ValueError as exc:
            raise ValueError(
                f"Unsupported option type: {value}"
            ) from exc


# ==========================================================
# Option Model
# ==========================================================


@dataclass(
    frozen=True,
    slots=True,
)
class Option:
    """
    European option contract.

    Parameters
    ----------
    option_type
        CALL or PUT

    spot
        Underlying price.

    strike
        Strike price.

    maturity
        Time to expiration (years).

    rate
        Risk-free interest rate.

    volatility
        Annual volatility.
    """

    option_type: OptionType | str

    spot: float

    strike: float

    maturity: float

    rate: float

    volatility: float

    # ------------------------------------------------------

    def __post_init__(self) -> None:
        """
        Normalize and validate data.
        """

        object.__setattr__(
            self,
            "option_type",
            OptionType.from_value(
                self.option_type
            ),
        )

        self._validate_positive(
            "spot",
            self.spot,
        )

        self._validate_positive(
            "strike",
            self.strike,
        )

        self._validate_positive(
            "maturity",
            self.maturity,
        )

        self._validate_positive(
            "volatility",
            self.volatility,
        )

    # ------------------------------------------------------

    @staticmethod
    def _validate_positive(
        name: str,
        value: float,
    ) -> None:
        """
        Validate positive numeric values.
        """

        if value <= 0.0:
            raise ValueError(
                f"{name} must be greater than zero."
            )

    # ------------------------------------------------------

    @property
    def is_call(self) -> bool:
        """
        Return True if Call option.
        """

        return self.option_type is OptionType.CALL

    # ------------------------------------------------------

    @property
    def is_put(self) -> bool:
        """
        Return True if Put option.
        """

        return self.option_type is OptionType.PUT
    # ------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the option contract to a dictionary.

        Returns
        -------
        dict[str, Any]
            Dictionary representation of the option.
        """

        data = asdict(self)

        data["option_type"] = self.option_type.value

        return data

    # ------------------------------------------------------

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "Option":
        """
        Create an Option instance from a dictionary.

        Parameters
        ----------
        data
            Dictionary containing option fields.

        Returns
        -------
        Option
        """

        return cls(
            option_type=OptionType.from_value(
                data["option_type"]
            ),
            spot=float(data["spot"]),
            strike=float(data["strike"]),
            maturity=float(data["maturity"]),
            rate=float(data["rate"]),
            volatility=float(data["volatility"]),
        )

    # ------------------------------------------------------

    def copy(
        self,
        **changes: Any,
    ) -> "Option":
        """
        Return a new Option with selected fields updated.

        Examples
        --------
        >>> option2 = option.copy(spot=105.0)

        >>> option3 = option.copy(
        ...     volatility=0.25,
        ...     maturity=0.5,
        ... )
        """

        data = self.to_dict()

        data.update(changes)

        return Option.from_dict(data)

    # ------------------------------------------------------

    def __str__(self) -> str:
        """
        Human-readable representation.
        """

        return (
            f"{self.option_type.value}("
            f"S={self.spot:.4f}, "
            f"K={self.strike:.4f}, "
            f"T={self.maturity:.6f}, "
            f"r={self.rate:.6f}, "
            f"σ={self.volatility:.6f})"
        )

    # ------------------------------------------------------

    def __repr__(self) -> str:
        """
        Developer representation.
        """

        return (
            "Option("
            f"option_type={self.option_type.value!r}, "
            f"spot={self.spot!r}, "
            f"strike={self.strike!r}, "
            f"maturity={self.maturity!r}, "
            f"rate={self.rate!r}, "
            f"volatility={self.volatility!r}"
            ")"
        )
    # ------------------------------------------------------

    def keys(self) -> tuple[str, ...]:
        """
        Return all field names.

        Returns
        -------
        tuple[str, ...]
        """

        return tuple(self.to_dict().keys())

    # ------------------------------------------------------

    def values(self) -> tuple[Any, ...]:
        """
        Return all field values.

        Returns
        -------
        tuple[Any, ...]
        """

        return tuple(self.to_dict().values())

    # ------------------------------------------------------

    def items(self) -> tuple[tuple[str, Any], ...]:
        """
        Return all key/value pairs.

        Returns
        -------
        tuple[tuple[str, Any], ...]
        """

        return tuple(self.to_dict().items())

    # ------------------------------------------------------

    def __iter__(self):
        """
        Iterate over key/value pairs.

        Examples
        --------
        >>> dict(option)
        """

        yield from self.to_dict().items()


# ==========================================================
# Public Exports
# ==========================================================

__all__ = [
    "Option",
    "OptionType",
]