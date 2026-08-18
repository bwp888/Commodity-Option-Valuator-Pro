"""
Commodity Option Valuator Pro
=============================

Option Scanner UI Tests.

Commit 0011
------------

Author : Simon
Version : 0.3.0
"""

from __future__ import annotations

from models.option_scanner import (
    OptionContract,
    OptionDirection,
)

from ui.scanner import (
    ScannerPage,
)


# ==========================================================
# Helpers
# ==========================================================


def make_contracts() -> list[OptionContract]:

    return [
        OptionContract(
            symbol="CALL001",
            direction=OptionDirection.CALL,
            strike=5600,
            price=100,
            volume=500,
            open_interest=1000,
        ),
        OptionContract(
            symbol="CALL002",
            direction=OptionDirection.CALL,
            strike=5700,
            price=80,
            volume=300,
            open_interest=800,
        ),
        OptionContract(
            symbol="CALL003",
            direction=OptionDirection.CALL,
            strike=5800,
            price=60,
            volume=100,
            open_interest=500,
        ),
        OptionContract(
            symbol="PUT001",
            direction=OptionDirection.PUT,
            strike=5600,
            price=90,
            volume=400,
            open_interest=900,
        ),
        OptionContract(
            symbol="PUT002",
            direction=OptionDirection.PUT,
            strike=5500,
            price=70,
            volume=200,
            open_interest=700,
        ),
    ]


# ==========================================================
# Import
# ==========================================================


def test_scanner_page_import():

    assert (
        ScannerPage
        is not None
    )


# ==========================================================
# Metadata
# ==========================================================


def test_scanner_result_columns():

    expected = {
        "symbol",
        "direction",
        "strike",
        "price",
        "volume",
        "open_interest",
    }

    assert expected == set(
        ScannerPage.RESULT_COLUMNS
    )


def test_scanner_result_titles():

    assert (
        ScannerPage.RESULT_TITLES[
            "symbol"
        ]
        ==
        "合约代码"
    )

    assert (
        ScannerPage.RESULT_TITLES[
            "volume"
        ]
        ==
        "成交量"
    )


# ==========================================================
# Parameter Parsing
# ==========================================================


def test_parse_top_n():

    assert (
        ScannerPage.parse_top_n("5")
        ==
        5
    )


def test_parse_top_n_rejects_zero():

    try:

        ScannerPage.parse_top_n("0")

    except ValueError as exc:

        assert "大于 0" in str(exc)

    else:

        raise AssertionError(
            "Expected ValueError"
        )


def test_parse_min_volume():

    assert (
        ScannerPage.parse_min_volume("100")
        ==
        100
    )


def test_parse_min_volume_allows_zero():

    assert (
        ScannerPage.parse_min_volume("0")
        ==
        0
    )


def test_parse_min_volume_rejects_negative():

    try:

        ScannerPage.parse_min_volume("-1")

    except ValueError as exc:

        assert "不能小于 0" in str(exc)

    else:

        raise AssertionError(
            "Expected ValueError"
        )


# ==========================================================
# Contract Filtering
# ==========================================================


def test_filter_all_contracts():

    contracts = make_contracts()

    result = ScannerPage.filter_contracts(
        contracts,
        "全部",
        0,
    )

    assert len(result) == 5


def test_filter_call_contracts():

    contracts = make_contracts()

    result = ScannerPage.filter_contracts(
        contracts,
        "CALL",
        0,
    )

    assert len(result) == 3

    assert all(
        item.direction
        ==
        OptionDirection.CALL
        for item in result
    )


def test_filter_put_contracts():

    contracts = make_contracts()

    result = ScannerPage.filter_contracts(
        contracts,
        "PUT",
        0,
    )

    assert len(result) == 2

    assert all(
        item.direction
        ==
        OptionDirection.PUT
        for item in result
    )


def test_filter_minimum_volume():

    contracts = make_contracts()

    result = ScannerPage.filter_contracts(
        contracts,
        "全部",
        300,
    )

    assert len(result) == 3

    assert all(
        item.volume >= 300
        for item in result
    )


def test_filter_invalid_direction():

    contracts = make_contracts()

    try:

        ScannerPage.filter_contracts(
            contracts,
            "INVALID",
            0,
        )

    except ValueError as exc:

        assert "扫描方向" in str(exc)

    else:

        raise AssertionError(
            "Expected ValueError"
        )


# ==========================================================
# Summary
# ==========================================================


def test_empty_summary():

    summary = {
        "contract_count": 0,
        "selected_count": 0,
        "has_scanner": False,
    }

    assert summary[
        "contract_count"
    ] == 0

    assert summary[
        "selected_count"
    ] == 0

    assert summary[
        "has_scanner"
    ] is False