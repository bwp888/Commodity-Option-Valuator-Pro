"""
Commodity Option Valuator Pro
=============================

Excel Market Data Reader

Read option chain data exported
from Wenhua Finance Excel.

Convert Excel rows into unified
OptionQuote data objects.

Author : Simon
Version : 1.1.0
"""


from __future__ import annotations


from pathlib import Path

from typing import Any


import pandas as pd


from data.option_chain import (
    OptionQuote,
)


class ExcelOptionReader:
    """
    Excel option chain reader.

    Excel columns:

    symbol
    underlying
    option_type
    strike
    price
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


    def __init__(
        self,
        filepath: str | Path,
    ) -> None:

        self.filepath = Path(
            filepath
        )

        self.dataframe: pd.DataFrame | None = None


    # ======================================================
    # Safe Convert
    # ======================================================

    @staticmethod
    def _safe_float(
        value: Any,
        default: float = 0.0,
    ) -> float:

        if value is None:
            return default


        if pd.isna(value):
            return default


        try:
            return float(value)

        except (
            ValueError,
            TypeError,
        ):
            return default



    @staticmethod
    def _safe_int(
        value: Any,
        default: int = 0,
    ) -> int:

        if value is None:
            return default


        if pd.isna(value):
            return default


        try:
            return int(float(value))

        except (
            ValueError,
            TypeError,
        ):
            return default



    # ======================================================
    # Load Excel
    # ======================================================

    def load(
        self,
    ) -> pd.DataFrame:

        self.dataframe = pd.read_excel(
            self.filepath
        )

        return self.dataframe



    # ======================================================
    # Validate
    # ======================================================

    def validate(
        self,
        dataframe: pd.DataFrame | None = None,
    ) -> bool:


        if dataframe is None:
            dataframe = self.dataframe


        if dataframe is None:
            return False


        for column in self.REQUIRED_COLUMNS:

            if column not in dataframe.columns:
                return False


        return True



    # ======================================================
    # Option Type Parse
    # ======================================================

    @staticmethod
    def parse_option_type(
        value: Any,
    ) -> str:


        text = str(
            value
        ).upper().strip()



        if text in (
            "CALL",
            "C",
            "看涨",
            "涨",
        ):
            return "CALL"



        if text in (
            "PUT",
            "P",
            "看跌",
            "跌",
        ):
            return "PUT"



        return "CALL"



    # ======================================================
    # Convert Row
    # ======================================================

    def row_to_quote(
        self,
        row: pd.Series,
    ) -> OptionQuote:


        return OptionQuote(

            symbol=str(
                row.get(
                    "symbol",
                    "",
                )
            ),


            underlying=str(
                row.get(
                    "underlying",
                    "",
                )
            ),


            option_type=self.parse_option_type(
                row.get(
                    "option_type",
                    row.get(
                        "direction",
                        "CALL",
                    )
                )
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


            implied_volatility=self._safe_float(
                row.get(
                    "iv"
                )
            ),

        )



    # ======================================================
    # Convert DataFrame
    # ======================================================

    def dataframe_to_quotes(
        self,
        dataframe: pd.DataFrame | None = None,
    ) -> list[OptionQuote]:


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
    # Read Quotes
    # ======================================================

    def read_quotes(
        self,
    ) -> list[OptionQuote]:


        dataframe = self.load()


        return self.dataframe_to_quotes(
            dataframe
        )