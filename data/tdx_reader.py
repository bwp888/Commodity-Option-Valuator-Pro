"""
TongDaXin option market data reader.

TongDaXin option exports use a GBK-encoded, tab-separated text format.
Although the exported file usually has an ``.xls`` extension, it is not
a native Microsoft Excel BIFF workbook.

This module converts TongDaXin raw option market data into the project's
unified OptionQuote model.

The reader intentionally does not use TongDaXin-calculated Greeks or
theoretical valuation results.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

from data.option_chain import OptionQuote


class TDXOptionReader:
    """
    Read option-chain files exported by TongDaXin.

    The exported file is treated as GBK-encoded tab-separated text,
    regardless of its filename extension.
    """

    COLUMN_MAP = {
        "代码": "symbol",
        "名称": "name",
        "现价": "price",
        "买价": "bid",
        "卖价": "ask",
        "总量": "volume",
        "持仓量": "open_interest",
        "类型": "option_type",
        "行权价": "strike",
    }

    CALL_VALUES = {
        "看涨",
        "认购",
        "CALL",
        "C",
    }

    PUT_VALUES = {
        "看跌",
        "认沽",
        "PUT",
        "P",
    }

    def __init__(
        self,
        file_path: str | Path,
        encoding: str = "gbk",
    ) -> None:
        self.file_path = Path(file_path)
        self.encoding = encoding
        self.dataframe: pd.DataFrame | None = None

    # ==========================================================
    # File validation
    # ==========================================================

    def validate_file(self) -> None:
        """Validate that the input file exists and is a regular file."""
        if not self.file_path.exists():
            raise FileNotFoundError(
                f"TDX option file not found: {self.file_path}"
            )

        if not self.file_path.is_file():
            raise ValueError(
                f"TDX option path is not a file: {self.file_path}"
            )

    # ==========================================================
    # Raw file loading
    # ==========================================================

    def load(self) -> pd.DataFrame:
        """
        Load the TongDaXin export as a tab-separated text file.

        The file extension is intentionally ignored. TongDaXin's
        exported .xls file is not a native Excel workbook.
        """
        self.validate_file()

        dataframe = pd.read_csv(
            self.file_path,
            sep="\t",
            encoding=self.encoding,
            dtype=str,
            keep_default_na=False,
            na_filter=False,
        )

        dataframe.columns = [
            str(column).strip()
            for column in dataframe.columns
        ]

        dataframe = dataframe.dropna(
            axis=0,
            how="all",
        )

        self.dataframe = dataframe

        return dataframe

    # ==========================================================
    # Value conversion
    # ==========================================================

    @staticmethod
    def _clean_value(value: Any) -> str:
        """Convert a raw cell value into a stripped string."""
        if value is None:
            return ""

        return str(value).strip()

    @classmethod
    def _safe_float(
        cls,
        value: Any,
    ) -> float:
        """Convert a raw value to float, returning 0.0 on failure."""
        text = cls._clean_value(value)

        if not text:
            return 0.0

        if text in {
            "--",
            "-",
            "—",
            "N/A",
            "NA",
            "None",
        }:
            return 0.0

        text = text.replace(",", "")

        try:
            return float(text)
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def _safe_optional_float(
        cls,
        value: Any,
    ) -> float | None:
        """
        Convert a raw value to float.

        Missing or invalid market quotes are represented by None
        instead of 0.0.
        """
        text = cls._clean_value(value)

        if not text:
            return None

        if text in {
            "--",
            "-",
            "—",
            "N/A",
            "NA",
            "None",
        }:
            return None

        text = text.replace(",", "")

        try:
            return float(text)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _safe_int(
        cls,
        value: Any,
    ) -> int:
        """Convert a raw value to int, returning 0 on failure."""
        text = cls._clean_value(value)

        if not text:
            return 0

        if text in {
            "--",
            "-",
            "—",
            "N/A",
            "NA",
            "None",
        }:
            return 0

        text = text.replace(",", "")

        try:
            return int(float(text))
        except (TypeError, ValueError):
            return 0

    # ==========================================================
    # Option type
    # ==========================================================

    @classmethod
    def parse_option_type(
        cls,
        value: Any,
        symbol: str = "",
    ) -> str:
        """
        Convert TongDaXin option direction into CALL / PUT.

        The explicit ``类型`` field has priority. The contract symbol
        is used as a fallback.
        """
        text = cls._clean_value(value).upper()

        if text in cls.CALL_VALUES:
            return "CALL"

        if text in cls.PUT_VALUES:
            return "PUT"

        normalized_symbol = cls._clean_value(symbol).upper()

        if re.search(r"-C-", normalized_symbol):
            return "CALL"

        if re.search(r"-P-", normalized_symbol):
            return "PUT"

        raise ValueError(
            f"Unable to determine option type: "
            f"type={value!r}, symbol={symbol!r}"
        )

    # ==========================================================
    # Underlying
    # ==========================================================

    @staticmethod
    def parse_underlying(
        symbol: str,
    ) -> str:
        """
        Extract the underlying commodity code from a TDX option symbol.

        Example:
            A2609-C-3400 -> A
        """
        text = str(symbol).strip().upper()

        if not text:
            return ""

        parts = text.split("-")

        if parts:
            match = re.match(
                r"([A-Z]+)",
                parts[0],
            )

            if match:
                return match.group(1)

        return ""

    # ==========================================================
    # Row conversion
    # ==========================================================

    def row_to_quote(
        self,
        row: pd.Series,
    ) -> OptionQuote:
        """Convert one TongDaXin row into OptionQuote."""
        symbol = self._clean_value(
            row.get("代码", "")
        )

        if symbol.startswith("="):
            symbol = symbol[1:].strip()

        if (
            len(symbol) >= 2
            and symbol.startswith('"')
            and symbol.endswith('"')
        ):
            symbol = symbol[1:-1]

        underlying = self.parse_underlying(
            symbol
        )

        option_type = self.parse_option_type(
            row.get("类型", ""),
            symbol=symbol,
        )

        return OptionQuote(
            symbol=symbol,
            underlying=underlying,
            option_type=option_type,
            strike=self._safe_float(
                row.get("行权价", "")
            ),
            last_price=self._safe_float(
                row.get("现价", "")
            ),
            bid_price=self._safe_optional_float(
                row.get("买价", "")
            ),
            ask_price=self._safe_optional_float(
                row.get("卖价", "")
            ),
            volume=self._safe_int(
                row.get("总量", "")
            ),
            open_interest=self._safe_int(
                row.get("持仓量", "")
            ),
            implied_volatility=None,
        )

    # ==========================================================
    # DataFrame conversion
    # ==========================================================

    def dataframe_to_quotes(
        self,
        dataframe: pd.DataFrame | None = None,
    ) -> list[OptionQuote]:
        """Convert a DataFrame into a list of OptionQuote objects."""
        if dataframe is None:
            dataframe = self.dataframe

        if dataframe is None:
            raise ValueError(
                "No TDX option dataframe loaded"
            )

        required_columns = {
            "代码",
            "现价",
            "买价",
            "卖价",
            "总量",
            "持仓量",
            "类型",
            "行权价",
        }

        missing_columns = sorted(
            required_columns
            - set(dataframe.columns)
        )

        if missing_columns:
            raise ValueError(
                "Missing required TDX option columns: "
                + ", ".join(missing_columns)
            )

        quotes: list[OptionQuote] = []

        for _, row in dataframe.iterrows():
            symbol = self._clean_value(
                row.get("代码", "")
            )

            if not symbol:
                continue

            try:
                quotes.append(
                    self.row_to_quote(row)
                )
            except ValueError:
                continue

        return quotes

    # ==========================================================
    # Public API
    # ==========================================================

    def read_quotes(self) -> list[OptionQuote]:
        """Load the TDX file and return normalized option quotes."""
        dataframe = self.load()

        return self.dataframe_to_quotes(
            dataframe
        )