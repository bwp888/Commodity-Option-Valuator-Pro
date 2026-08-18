"""
Commodity Option Valuator Pro
=============================

Excel Market Data Reader

Read option chain data exported
from Wenhua Finance Excel.

Supports:
- OptionQuote conversion
- OptionContract conversion
- CALL / PUT parsing
- Chinese direction parsing
- Safe numeric conversion

Author : Simon
Version : 1.2.0
Python : 3.12
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from data.option_chain import OptionQuote
from models.option_scanner import (
    OptionContract,
    OptionDirection,
)


class ExcelOptionReader:
    """
    Excel option chain reader.

    Required columns
    ----------------
    symbol
    strike
    price

    Optional columns
    ----------------
    underlying
    direction
    option_type
    volume
    open_interest
    bid
    ask
    iv
    """

    REQUIRED_COLUMNS = [
        "symbol",
        "strike",
        "price",
    ]

    # ======================================================
    # Initialization
    # ======================================================

    def __init__(
        self,
        filepath: str | Path,
    ) -> None:

        self.filepath = Path(
            filepath
        )

        self.dataframe: pd.DataFrame | None = None

    # ======================================================
    # Safe Conversion
    # ======================================================

    @staticmethod
    def _safe_float(
        value: Any,
        default: float = 0.0,
    ) -> float:
        """
        Safely convert a value to float.
        """

        if value is None:
            return default

        try:
            if pd.isna(value):
                return default

        except (
            TypeError,
            ValueError,
        ):
            pass

        try:
            return float(value)

        except (
            ValueError,
            TypeError,
        ):
            return default

    # ------------------------------------------------------

    @staticmethod
    def _safe_int(
        value: Any,
        default: int = 0,
    ) -> int:
        """
        Safely convert a value to int.
        """

        if value is None:
            return default

        try:
            if pd.isna(value):
                return default

        except (
            TypeError,
            ValueError,
        ):
            pass

        try:
            return int(
                float(value)
            )

        except (
            ValueError,
            TypeError,
        ):
            return default

    # ======================================================
    # Direction Parsing
    # ======================================================

    @staticmethod
    def parse_direction(
        value: Any,
    ) -> OptionDirection:
        """
        Parse option direction.

        Supported values
        ----------------
        CALL
        C
        看涨

        PUT
        P
        看跌

        Returns
        -------
        OptionDirection

        Raises
        ------
        ValueError
            If the direction is unknown.
        """

        if isinstance(
            value,
            OptionDirection,
        ):
            return value

        text = str(
            value
        ).strip().upper()

        if text in (
            "CALL",
            "C",
            "看涨",
        ):
            return OptionDirection.CALL

        if text in (
            "PUT",
            "P",
            "看跌",
        ):
            return OptionDirection.PUT

        raise ValueError(
            f"Unknown option direction: {value!r}"
        )

    # ======================================================
    # Option Type Parsing
    # ======================================================

    @classmethod
    def parse_option_type(
        cls,
        value: Any,
    ) -> str:
        """
        Parse option type.

        Returns
        -------
        str
            CALL or PUT.
        """

        return cls.parse_direction(
            value
        ).value

    # ======================================================
    # Underlying Parsing
    # ======================================================

    @staticmethod
    def _parse_underlying(
        symbol: str,
    ) -> str:
        """
        Extract underlying symbol from option symbol.

        Examples
        --------
        A2609-C-3400
            -> A

        CU2409-C-70000
            -> CU
        """

        text = str(
            symbol
        ).strip()

        if not text:
            return ""

        parts = text.split("-")

        if not parts:
            return text

        underlying = parts[0]

        while (
            underlying
            and underlying[-1].isdigit()
        ):
            underlying = underlying[:-1]

        return underlying

    # ======================================================
    # Excel Loading
    # ======================================================

    def load(
        self,
    ) -> pd.DataFrame:
        """
        Load Excel data.
        """

        self.dataframe = pd.read_excel(
            self.filepath
        )

        return self.dataframe

    # ======================================================
    # Validation
    # ======================================================

    def validate(
        self,
        dataframe: pd.DataFrame | None = None,
    ) -> bool:
        """
        Validate required Excel columns.

        Returns
        -------
        bool
            True if all required columns exist.
        """

        if dataframe is None:
            dataframe = self.dataframe

        if dataframe is None:
            return False

        for column in self.REQUIRED_COLUMNS:

            if column not in dataframe.columns:
                return False

        return True

    # ======================================================
    # Row -> OptionQuote
    # ======================================================

    def row_to_quote(
        self,
        row: pd.Series,
    ) -> OptionQuote:
        """
        Convert one DataFrame row to OptionQuote.
        """

        symbol = str(
            row.get(
                "symbol",
                "",
            )
        )

        direction = row.get(
            "option_type",
            row.get(
                "direction",
                "CALL",
            ),
        )

        underlying_value = row.get(
            "underlying",
            None,
        )

        if (
            underlying_value is None
            or pd.isna(underlying_value)
        ):
            underlying = self._parse_underlying(
                symbol
            )

        else:
            underlying = str(
                underlying_value
            )

        iv_value = row.get(
            "iv",
            None,
        )

        if iv_value is None:
            implied_volatility = None

        else:
            try:
                if pd.isna(iv_value):
                    implied_volatility = None
                else:
                    implied_volatility = float(
                        iv_value
                    )

            except (
                TypeError,
                ValueError,
            ):
                implied_volatility = None

        return OptionQuote(
            symbol=symbol,

            underlying=underlying,

            option_type=self.parse_option_type(
                direction
            ),

            strike=self._safe_float(
                row.get(
                    "strike"
                )
            ),

            last_price=self._safe_float(
                row.get(
                    "price"
                )
            ),

            bid_price=self._safe_float(
                row.get(
                    "bid"
                )
            ),

            ask_price=self._safe_float(
                row.get(
                    "ask"
                )
            ),

            volume=self._safe_int(
                row.get(
                    "volume"
                )
            ),

            open_interest=self._safe_int(
                row.get(
                    "open_interest"
                )
            ),

            implied_volatility=(
                implied_volatility
            ),
        )

    # ======================================================
    # Row -> OptionContract
    # ======================================================

    def row_to_contract(
        self,
        row: pd.Series,
    ) -> OptionContract:
        """
        Convert one DataFrame row to OptionContract.

        This interface is used by the option scanner.
        """

        symbol = str(
            row.get(
                "symbol",
                "",
            )
        )

        direction_value = row.get(
            "direction",
            row.get(
                "option_type",
                "CALL",
            ),
        )

        direction = self.parse_direction(
            direction_value
        )

        return OptionContract(
            symbol=symbol,

            direction=direction,

            strike=self._safe_float(
                row.get(
                    "strike"
                )
            ),

            price=self._safe_float(
                row.get(
                    "price"
                )
            ),

            volume=self._safe_int(
                row.get(
                    "volume"
                )
            ),

            open_interest=self._safe_int(
                row.get(
                    "open_interest"
                )
            ),

            bid=self._safe_float(
                row.get(
                    "bid"
                )
            ),

            ask=self._safe_float(
                row.get(
                    "ask"
                )
            ),
        )

    # ======================================================
    # DataFrame -> OptionQuote
    # ======================================================

    def dataframe_to_quotes(
        self,
        dataframe: pd.DataFrame | None = None,
    ) -> list[OptionQuote]:
        """
        Convert DataFrame to OptionQuote list.
        """

        if dataframe is None:
            dataframe = self.dataframe

        if not self.validate(
            dataframe
        ):
            raise ValueError(
                "Invalid option dataframe"
            )

        quotes: list[OptionQuote] = []

        for _, row in dataframe.iterrows():

            quotes.append(
                self.row_to_quote(
                    row
                )
            )

        return quotes

    # ======================================================
    # DataFrame -> OptionContract
    # ======================================================

    def dataframe_to_contracts(
        self,
        dataframe: pd.DataFrame | None = None,
    ) -> list[OptionContract]:
        """
        Convert DataFrame to OptionContract list.
        """

        if dataframe is None:
            dataframe = self.dataframe

        if not self.validate(
            dataframe
        ):
            raise ValueError(
                "Invalid option dataframe"
            )

        contracts: list[OptionContract] = []

        for _, row in dataframe.iterrows():

            contracts.append(
                self.row_to_contract(
                    row
                )
            )

        return contracts

    # ======================================================
    # Read Quotes
    # ======================================================

    def read_quotes(
        self,
    ) -> list[OptionQuote]:
        """
        Load Excel file and return OptionQuote list.
        """

        dataframe = self.load()

        return self.dataframe_to_quotes(
            dataframe
        )

    # ======================================================
    # Read Contracts
    # ======================================================

    def read_contracts(
        self,
    ) -> list[OptionContract]:
        """
        Load Excel file and return OptionContract list.
        """

        dataframe = self.load()

        return self.dataframe_to_contracts(
            dataframe
        )


__all__ = [
    "ExcelOptionReader",
]