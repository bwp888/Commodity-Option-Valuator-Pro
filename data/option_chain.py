"""
Option chain data structures.

This module defines the unified market quote model
used by external data adapters.

Supported future sources:
- Wenhua DDE
- Excel
- CSV
- API
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional


OptionType = Literal["CALL", "PUT"]


@dataclass(slots=True)
class OptionQuote:
    """
    Unified option market quote.

    This class is only a data container.
    It does not perform valuation.
    """

    symbol: str

    underlying: str

    option_type: OptionType

    strike: float

    last_price: float

    bid_price: Optional[float] = None

    ask_price: Optional[float] = None

    volume: int = 0

    open_interest: int = 0

    implied_volatility: Optional[float] = None

    timestamp: Optional[datetime] = None


    def is_call(self) -> bool:
        return self.option_type == "CALL"


    def is_put(self) -> bool:
        return self.option_type == "PUT"


    def mid_price(self) -> Optional[float]:

        if (
            self.bid_price is None
            or self.ask_price is None
        ):
            return None

        return (
            self.bid_price
            +
            self.ask_price
        ) / 2