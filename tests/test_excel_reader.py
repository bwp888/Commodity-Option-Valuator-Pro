"""
Commodity Option Valuator Pro
=============================

Excel Reader Tests

Author : Simon
Version : 1.0.0
"""


from __future__ import annotations


import pandas as pd


import pytest


from data.excel_reader import (
    ExcelOptionReader,
)

from models.option_scanner import (
    OptionDirection,
)



# ==========================================================
# Fixtures
# ==========================================================


@pytest.fixture
def option_dataframe():

    return pd.DataFrame(

        [

            {
                "symbol":
                    "CU2409-C-70000",

                "direction":
                    "CALL",

                "strike":
                    70000,

                "price":
                    850,

                "volume":
                    12000,

                "open_interest":
                    50000,

                "bid":
                    840,

                "ask":
                    860,
            },


            {
                "symbol":
                    "CU2409-P-70000",

                "direction":
                    "PUT",

                "strike":
                    70000,

                "price":
                    620,

                "volume":
                    9000,

            },

        ]
    )



@pytest.fixture
def reader(tmp_path):

    file = (
        tmp_path
        /
        "option.xlsx"
    )


    return (
        ExcelOptionReader(
            file
        )
    )



# ==========================================================
# Validation
# ==========================================================


def test_required_columns():

    reader = ExcelOptionReader(
        "test.xlsx"
    )


    df = pd.DataFrame(

        [

            {
                "symbol":"A",

                "direction":"CALL",

                "strike":100,

                "price":10,

                "volume":100,

            }

        ]

    )


    assert (
        reader.validate(df)
        is True
    )



def test_invalid_columns():

    reader = ExcelOptionReader(
        "test.xlsx"
    )


    df = pd.DataFrame(
        [
            {
                "symbol":"A"
            }
        ]
    )


    assert (
        reader.validate(df)
        is False
    )



# ==========================================================
# Direction
# ==========================================================


@pytest.mark.parametrize(

    "value,expected",

    [

        (
            "CALL",
            OptionDirection.CALL
        ),

        (
            "C",
            OptionDirection.CALL
        ),

        (
            "看涨",
            OptionDirection.CALL
        ),

        (
            "PUT",
            OptionDirection.PUT
        ),

        (
            "P",
            OptionDirection.PUT
        ),

        (
            "看跌",
            OptionDirection.PUT
        ),

    ]

)

def test_parse_direction(
    reader,
    value,
    expected,
):

    assert (
        reader.parse_direction(value)
        ==
        expected
    )



def test_unknown_direction(reader):

    with pytest.raises(
        ValueError
    ):

        reader.parse_direction(
            "UNKNOWN"
        )



# ==========================================================
# Convert
# ==========================================================


def test_row_to_contract(
    reader,
    option_dataframe,
):

    contract = (
        reader.row_to_contract(
            option_dataframe.iloc[0]
        )
    )


    assert (
        contract.symbol
        ==
        "CU2409-C-70000"
    )


    assert (
        contract.direction
        ==
        OptionDirection.CALL
    )


    assert (
        contract.volume
        ==
        12000
    )



def test_dataframe_to_contracts(
    reader,
    option_dataframe,
):

    result = (
        reader.dataframe_to_contracts(
            option_dataframe
        )
    )


    assert (
        len(result)
        ==
        2
    )


    assert (
        result[1].direction
        ==
        OptionDirection.PUT
    )