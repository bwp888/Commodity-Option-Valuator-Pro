"""
Commodity Option Valuator Pro
=============================

Excel Market Data Reader

Read option chain data exported
from Wenhua Finance Excel.

Author : Simon
Version : 1.0.1
"""


from __future__ import annotations


from pathlib import Path

from typing import Any


import pandas as pd


from models.option_scanner import (
    OptionContract,
    OptionDirection,
)



# ==========================================================
# Excel Reader
# ==========================================================


class ExcelOptionReader:
    """
    Excel option chain reader.

    Expected columns:

    symbol
    direction
    strike
    price
    volume
    open_interest
    bid
    ask

    """



    REQUIRED_COLUMNS = [

        "symbol",

        "direction",

        "strike",

        "price",

        "volume",

    ]



    def __init__(
        self,
        filepath: str | Path,
    ) -> None:


        self.filepath = Path(
            filepath
        )


        self.dataframe: pd.DataFrame | None = None



    # ------------------------------------------------------
    # Safe Convert
    # ------------------------------------------------------

    @staticmethod
    def _safe_float(
        value: Any,
        default: float = 0.0,
    ) -> float:
        """
        Convert value to float safely.

        Handle:
        - NaN
        - None
        - empty string
        """

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
        """
        Convert value to int safely.
        """

        if value is None:

            return default


        if pd.isna(value):

            return default


        try:

            return int(
                float(value)
            )

        except (
            ValueError,
            TypeError,
        ):

            return default



    # ------------------------------------------------------
    # Load Excel
    # ------------------------------------------------------

    def load(
        self,
    ) -> pd.DataFrame:


        self.dataframe = pd.read_excel(
            self.filepath
        )


        return self.dataframe



    # ------------------------------------------------------
    # Validate
    # ------------------------------------------------------

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



    # ------------------------------------------------------
    # Normalize Direction
    # ------------------------------------------------------

    def parse_direction(
        self,
        value: Any,
    ) -> OptionDirection:


        text = str(
            value
        ).upper().strip()



        if text in (

            "CALL",

            "C",

            "看涨",

            "涨",

        ):

            return OptionDirection.CALL



        if text in (

            "PUT",

            "P",

            "看跌",

            "跌",

        ):

            return OptionDirection.PUT



        raise ValueError(
            f"Unknown option direction: {value}"
        )



    # ------------------------------------------------------
    # Convert Row
    # ------------------------------------------------------

    def row_to_contract(
        self,
        row: pd.Series,
    ) -> OptionContract:


        return OptionContract(

            symbol=str(
                row.get(
                    "symbol",
                    "",
                )
            ),



            direction=self.parse_direction(
                row.get(
                    "direction",
                    "",
                )
            ),



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



    # ------------------------------------------------------
    # Convert DataFrame
    # ------------------------------------------------------

    def dataframe_to_contracts(
        self,
        dataframe: pd.DataFrame | None = None,
    ) -> list[OptionContract]:


        if dataframe is None:

            dataframe = self.dataframe



        if not self.validate(
            dataframe
        ):

            raise ValueError(
                "Invalid option dataframe"
            )



        contracts = []



        for _, row in dataframe.iterrows():

            contracts.append(

                self.row_to_contract(
                    row
                )

            )



        return contracts



    # ------------------------------------------------------
    # Read Contracts
    # ------------------------------------------------------

    def read_contracts(
        self,
    ) -> list[OptionContract]:


        dataframe = self.load()


        return self.dataframe_to_contracts(
            dataframe
        )