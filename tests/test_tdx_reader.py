from __future__ import annotations

from pathlib import Path

import pandas as pd

from data.option_chain import OptionQuote
from data.tdx_reader import TDXOptionReader


def create_tdx_dataframe() -> pd.DataFrame:
    """Create representative TongDaXin option data."""
    return pd.DataFrame(
        [
            {
                "代码": '="A2609-C-3400"',
                "名称": "豆一2609-购-3400",
                "现价": "1446.0",
                "买价": "1223.5",
                "卖价": "--",
                "总量": "0",
                "持仓量": "0",
                "类型": "看涨",
                "行权价": "3400.0",
            },
            {
                "代码": '="A2609-P-3400"',
                "名称": "豆一2609-沽-3400",
                "现价": "88.0",
                "买价": "80.0",
                "卖价": "90.0",
                "总量": "125",
                "持仓量": "350",
                "类型": "看跌",
                "行权价": "3400.0",
            },
        ]
    )


def test_parse_underlying() -> None:
    assert (
        TDXOptionReader.parse_underlying(
            "A2609-C-3400"
        )
        == "A"
    )


def test_parse_call_option() -> None:
    assert (
        TDXOptionReader.parse_option_type(
            "看涨",
            "A2609-C-3400",
        )
        == "CALL"
    )


def test_parse_put_option() -> None:
    assert (
        TDXOptionReader.parse_option_type(
            "看跌",
            "A2609-P-3400",
        )
        == "PUT"
    )


def test_dataframe_to_quotes() -> None:
    reader = TDXOptionReader(
        "unused.xls"
    )

    dataframe = create_tdx_dataframe()

    quotes = reader.dataframe_to_quotes(
        dataframe
    )

    assert len(quotes) == 2

    assert isinstance(
        quotes[0],
        OptionQuote,
    )

    assert quotes[0].symbol == "A2609-C-3400"
    assert quotes[0].underlying == "A"
    assert quotes[0].option_type == "CALL"
    assert quotes[0].strike == 3400.0
    assert quotes[0].last_price == 1446.0
    assert quotes[0].bid_price == 1223.5
    assert quotes[0].ask_price is None
    assert quotes[0].volume == 0
    assert quotes[0].open_interest == 0
    assert quotes[0].implied_volatility is None

    assert quotes[1].symbol == "A2609-P-3400"
    assert quotes[1].option_type == "PUT"
    assert quotes[1].strike == 3400.0
    assert quotes[1].volume == 125
    assert quotes[1].open_interest == 350


def test_read_real_tdx_file() -> None:
    """
    Optional integration test.

    If the real TongDaXin export is copied into the project root,
    this test validates the complete file-reading path.
    """
    file_path = Path(
        "大连商品期权20260813.xls"
    )

    if not file_path.exists():
        return

    reader = TDXOptionReader(
        file_path
    )

    quotes = reader.read_quotes()

    assert quotes
    assert all(
        isinstance(
            quote,
            OptionQuote,
        )
        for quote in quotes
    )

    assert all(
        quote.symbol
        for quote in quotes
    )

    assert all(
        quote.option_type in {
            "CALL",
            "PUT",
        }
        for quote in quotes
    )