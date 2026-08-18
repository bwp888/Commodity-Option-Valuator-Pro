"""
Commodity Option Valuator Pro
=============================

Tests for MarketFileReader.

Commit 0014
------------

Author : Simon
Version : 0.4.0
"""

from __future__ import annotations

from pathlib import Path

import pytest

from data.market_file_reader import (
    MarketFileReader,
)


# ==========================================================
# Test Data
# ==========================================================


def make_tsv_content() -> str:
    """Return a valid tab-separated market-data file."""

    return (
        "合约代码\t方向\t行权价\t市场价格\t成交量\t持仓量\n"
        "SR609C5600\tCALL\t5600\t120.5\t1000\t5000\n"
        "SR609P5400\tPUT\t5400\t85.2\t800\t4200\n"
    )


def make_csv_content() -> str:
    """Return a valid CSV market-data file."""

    return (
        "symbol,direction,strike,price,volume,open_interest\n"
        "SR609C5600,CALL,5600,120.5,1000,5000\n"
        "SR609P5400,PUT,5400,85.2,800,4200\n"
    )


# ==========================================================
# Import
# ==========================================================


def test_reader_import() -> None:
    """MarketFileReader should be importable."""

    reader = MarketFileReader()

    assert reader is not None


# ==========================================================
# Initialization
# ==========================================================


def test_reader_default_encodings() -> None:
    """Reader should provide default encoding candidates."""

    reader = MarketFileReader()

    assert "utf-8" in reader.encodings
    assert "gbk" in reader.encodings
    assert "gb18030" in reader.encodings


def test_reader_custom_encodings() -> None:
    """Custom encoding candidates should be accepted."""

    reader = MarketFileReader(
        encodings=(
            "utf-8",
        )
    )

    assert reader.encodings == (
        "utf-8",
    )


# ==========================================================
# File Validation
# ==========================================================


def test_read_missing_file(
    tmp_path: Path,
) -> None:
    """Missing files should raise FileNotFoundError."""

    reader = MarketFileReader()

    path = (
        tmp_path
        / "missing.txt"
    )

    with pytest.raises(
        FileNotFoundError
    ):
        reader.read(path)


def test_read_directory_rejected(
    tmp_path: Path,
) -> None:
    """Directories should not be accepted as files."""

    reader = MarketFileReader()

    with pytest.raises(
        ValueError,
        match="不是文件",
    ):
        reader.read(tmp_path)


def test_read_empty_file(
    tmp_path: Path,
) -> None:
    """Empty files should be rejected."""

    path = (
        tmp_path
        / "empty.txt"
    )

    path.write_text(
        "",
        encoding="utf-8",
    )

    reader = MarketFileReader()

    with pytest.raises(
        ValueError,
        match="为空",
    ):
        reader.read(path)


# ==========================================================
# Delimiter Detection
# ==========================================================


def test_detect_tab_delimiter() -> None:
    """Tab-separated headers should be detected."""

    reader = MarketFileReader()

    delimiter = reader._detect_delimiter(
        "symbol\tdirection\tstrike"
    )

    assert delimiter == "\t"


def test_detect_csv_delimiter() -> None:
    """Comma-separated headers should be detected."""

    reader = MarketFileReader()

    delimiter = reader._detect_delimiter(
        "symbol,direction,strike"
    )

    assert delimiter == ","


def test_detect_semicolon_delimiter() -> None:
    """Semicolon-separated headers should be detected."""

    reader = MarketFileReader()

    delimiter = reader._detect_delimiter(
        "symbol;direction;strike"
    )

    assert delimiter == ";"


def test_detect_pipe_delimiter() -> None:
    """Pipe-separated headers should be detected."""

    reader = MarketFileReader()

    delimiter = reader._detect_delimiter(
        "symbol|direction|strike"
    )

    assert delimiter == "|"


# ==========================================================
# Header Normalization
# ==========================================================


def test_normalize_chinese_headers() -> None:
    """Chinese market-data headers should be mapped."""

    reader = MarketFileReader()

    headers = reader._normalize_headers(
        [
            "合约代码",
            "方向",
            "行权价",
            "市场价格",
            "成交量",
            "持仓量",
        ]
    )

    assert headers == [
        "symbol",
        "direction",
        "strike",
        "price",
        "volume",
        "open_interest",
    ]


def test_normalize_english_headers() -> None:
    """English headers should remain canonical."""

    reader = MarketFileReader()

    headers = reader._normalize_headers(
        [
            "symbol",
            "direction",
            "strike",
            "price",
            "volume",
            "open_interest",
        ]
    )

    assert headers == [
        "symbol",
        "direction",
        "strike",
        "price",
        "volume",
        "open_interest",
    ]


def test_normalize_header_ignores_spaces() -> None:
    """Header matching should ignore spaces."""

    reader = MarketFileReader()

    headers = reader._normalize_headers(
        [
            "合约代码",
            " 市场价格 ",
            "成交量",
        ]
    )

    assert headers == [
        "symbol",
        "price",
        "volume",
    ]


# ==========================================================
# Header Validation
# ==========================================================


def test_validate_headers_accepts_required_fields() -> None:
    """Required fields should pass validation."""

    reader = MarketFileReader()

    reader._validate_headers(
        [
            "symbol",
            "direction",
            "strike",
            "price",
            "volume",
        ]
    )


def test_validate_headers_rejects_missing_symbol() -> None:
    """Missing symbol should be rejected."""

    reader = MarketFileReader()

    with pytest.raises(
        ValueError,
        match="symbol",
    ):
        reader._validate_headers(
            [
                "direction",
                "strike",
                "price",
                "volume",
            ]
        )


def test_validate_headers_rejects_missing_direction() -> None:
    """Missing direction should be rejected."""

    reader = MarketFileReader()

    with pytest.raises(
        ValueError,
        match="direction",
    ):
        reader._validate_headers(
            [
                "symbol",
                "strike",
                "price",
                "volume",
            ]
        )


def test_validate_headers_rejects_missing_strike() -> None:
    """Missing strike should be rejected."""

    reader = MarketFileReader()

    with pytest.raises(
        ValueError,
        match="strike",
    ):
        reader._validate_headers(
            [
                "symbol",
                "direction",
                "price",
                "volume",
            ]
        )


def test_validate_headers_rejects_missing_price() -> None:
    """Missing price should be rejected."""

    reader = MarketFileReader()

    with pytest.raises(
        ValueError,
        match="price",
    ):
        reader._validate_headers(
            [
                "symbol",
                "direction",
                "strike",
                "volume",
            ]
        )


def test_validate_headers_rejects_missing_volume() -> None:
    """Missing volume should be rejected."""

    reader = MarketFileReader()

    with pytest.raises(
        ValueError,
        match="volume",
    ):
        reader._validate_headers(
            [
                "symbol",
                "direction",
                "strike",
                "price",
            ]
        )


# ==========================================================
# Text File Reading
# ==========================================================


def test_read_tsv_file(
    tmp_path: Path,
) -> None:
    """TSV market-data files should be parsed."""

    path = (
        tmp_path
        / "market.tsv"
    )

    path.write_text(
        make_tsv_content(),
        encoding="utf-8",
    )

    reader = MarketFileReader()

    records = reader.read(path)

    assert len(records) == 2

    assert records[0]["symbol"] == (
        "SR609C5600"
    )

    assert records[0]["direction"] == (
        "CALL"
    )

    assert records[0]["strike"] == (
        "5600"
    )

    assert records[0]["price"] == (
        "120.5"
    )

    assert records[0]["volume"] == (
        "1000"
    )

    assert records[0]["open_interest"] == (
        "5000"
    )


def test_read_csv_file(
    tmp_path: Path,
) -> None:
    """CSV market-data files should be parsed."""

    path = (
        tmp_path
        / "market.csv"
    )

    path.write_text(
        make_csv_content(),
        encoding="utf-8",
    )

    reader = MarketFileReader()

    records = reader.read(path)

    assert len(records) == 2

    assert records[1]["symbol"] == (
        "SR609P5400"
    )

    assert records[1]["direction"] == (
        "PUT"
    )


def test_read_records_alias(
    tmp_path: Path,
) -> None:
    """read_records should behave like read."""

    path = (
        tmp_path
        / "market.tsv"
    )

    path.write_text(
        make_tsv_content(),
        encoding="utf-8",
    )

    reader = MarketFileReader()

    records = reader.read_records(
        path
    )

    assert len(records) == 2


# ==========================================================
# Encoding
# ==========================================================


def test_read_gbk_file(
    tmp_path: Path,
) -> None:
    """GBK encoded Chinese files should be supported."""

    path = (
        tmp_path
        / "market_gbk.txt"
    )

    path.write_bytes(
        make_tsv_content().encode(
            "gbk"
        )
    )

    reader = MarketFileReader()

    records = reader.read(path)

    assert len(records) == 2

    assert records[0]["symbol"] == (
        "SR609C5600"
    )


# ==========================================================
# Optional Fields
# ==========================================================


def test_optional_fields_are_supported(
    tmp_path: Path,
) -> None:
    """Bid and ask should be retained when available."""

    content = (
        "symbol,direction,strike,price,volume,"
        "open_interest,bid,ask\n"
        "SR609C5600,CALL,5600,120.5,1000,"
        "5000,120,121\n"
    )

    path = (
        tmp_path
        / "market.csv"
    )

    path.write_text(
        content,
        encoding="utf-8",
    )

    reader = MarketFileReader()

    records = reader.read(path)

    assert records[0]["bid"] == "120"
    assert records[0]["ask"] == "121"


# ==========================================================
# Empty Rows
# ==========================================================


def test_empty_rows_are_ignored(
    tmp_path: Path,
) -> None:
    """Blank rows should not become records."""

    content = (
        "symbol,direction,strike,price,volume\n"
        "\n"
        "SR609C5600,CALL,5600,120.5,1000\n"
        "\n"
    )

    path = (
        tmp_path
        / "market.csv"
    )

    path.write_text(
        content,
        encoding="utf-8",
    )

    reader = MarketFileReader()

    records = reader.read(path)

    assert len(records) == 1


# ==========================================================
# Missing Fields
# ==========================================================


def test_missing_required_field(
    tmp_path: Path,
) -> None:
    """Files missing required columns should fail."""

    content = (
        "symbol,direction,strike,price\n"
        "SR609C5600,CALL,5600,120.5\n"
    )

    path = (
        tmp_path
        / "invalid.csv"
    )

    path.write_text(
        content,
        encoding="utf-8",
    )

    reader = MarketFileReader()

    with pytest.raises(
        ValueError,
        match="volume",
    ):
        reader.read(path)


# ==========================================================
# Record Normalization
# ==========================================================


def test_normalize_record_keeps_market_values() -> None:
    """Record normalization should preserve market values."""

    reader = MarketFileReader()

    record = reader._normalize_record(
        {
            "symbol": " SR609C5600 ",
            "direction": " CALL ",
            "strike": "5600",
            "price": "120.5",
            "volume": "1000",
        }
    )

    assert record["symbol"] == (
        "SR609C5600"
    )

    assert record["direction"] == (
        "CALL"
    )

    assert record["strike"] == "5600"
    assert record["price"] == "120.5"
    assert record["volume"] == "1000"


# ==========================================================
# String Helper
# ==========================================================


def test_stringify_none() -> None:
    """None should become an empty string."""

    reader = MarketFileReader()

    assert reader._stringify(None) == ""


def test_stringify_number() -> None:
    """Numbers should convert to strings."""

    reader = MarketFileReader()

    assert reader._stringify(5600) == "5600"


# ==========================================================
# Path Support
# ==========================================================


def test_read_accepts_string_path(
    tmp_path: Path,
) -> None:
    """String paths should be accepted."""

    path = (
        tmp_path
        / "market.csv"
    )

    path.write_text(
        make_csv_content(),
        encoding="utf-8",
    )

    reader = MarketFileReader()

    records = reader.read(
        str(path)
    )

    assert len(records) == 2