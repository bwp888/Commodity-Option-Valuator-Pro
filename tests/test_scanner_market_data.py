"""
Commodity Option Valuator Pro
=============================

Scanner market-data integration tests.

Commit 0013
------------

Test the connection between ScannerPage
and MarketDataAdapter.

Author : Simon
Version : 0.3.1
"""

from __future__ import annotations

from models.option_scanner import (
    OptionDirection,
)

from ui.scanner import (
    ScannerPage,
)


def make_records() -> list[dict[str, object]]:
    """Create normalized market-data input records."""

    return [
        {
            "symbol": "TEST-C-5000",
            "direction": "CALL",
            "strike": 5000,
            "price": 120,
            "volume": 100,
            "open_interest": 500,
        },
        {
            "symbol": "TEST-C-5100",
            "direction": "CALL",
            "strike": 5100,
            "price": 80,
            "volume": 300,
            "open_interest": 600,
        },
        {
            "symbol": "TEST-P-5000",
            "direction": "PUT",
            "strike": 5000,
            "price": 110,
            "volume": 200,
            "open_interest": 450,
        },
        {
            "symbol": "TEST-P-5100",
            "direction": "PUT",
            "strike": 5100,
            "price": 150,
            "volume": 50,
            "open_interest": 200,
        },
    ]


def test_market_data_adapter_import() -> None:
    """ScannerPage should expose a market-data adapter."""

    page = object.__new__(
        ScannerPage
    )

    page.market_data_adapter = None

    assert hasattr(
        page,
        "market_data_adapter",
    )


def test_load_market_data_normalizes_records() -> None:
    """Raw records should become OptionContract objects."""

    page = object.__new__(
        ScannerPage
    )

    from data.market_data_adapter import (
        MarketDataAdapter,
    )

    page.market_data_adapter = (
        MarketDataAdapter()
    )

    page.contracts = []
    page.selected_contracts = []
    page.scanner = None

    contracts = page.load_market_data(
        make_records()
    )

    assert len(contracts) == 4

    assert contracts[0].symbol == "TEST-C-5000"

    assert (
        contracts[0].direction
        == OptionDirection.CALL
    )

    assert contracts[1].volume == 300


def test_load_market_data_updates_contracts() -> None:
    """Loading data should update the page contract state."""

    page = object.__new__(
        ScannerPage
    )

    from data.market_data_adapter import (
        MarketDataAdapter,
    )

    page.market_data_adapter = (
        MarketDataAdapter()
    )

    page.contracts = []
    page.selected_contracts = []
    page.scanner = None

    contracts = page.load_market_data(
        make_records()
    )

    assert page.contracts == contracts
    assert len(page.contracts) == 4


def test_load_market_data_returns_copy() -> None:
    """The returned list should not expose internal list state."""

    page = object.__new__(
        ScannerPage
    )

    from data.market_data_adapter import (
        MarketDataAdapter,
    )

    page.market_data_adapter = (
        MarketDataAdapter()
    )

    page.contracts = []
    page.selected_contracts = []
    page.scanner = None

    contracts = page.load_market_data(
        make_records()
    )

    contracts.clear()

    assert len(page.contracts) == 4


def test_loaded_contracts_can_be_scanned() -> None:
    """Loaded contracts should flow into OptionScanner."""

    page = object.__new__(
        ScannerPage
    )

    from data.market_data_adapter import (
        MarketDataAdapter,
    )

    page.market_data_adapter = (
        MarketDataAdapter()
    )

    page.contracts = []
    page.selected_contracts = []
    page.scanner = None

    page.load_market_data(
        make_records()
    )

    selected = page.scan_contracts(
        page.contracts,
        top_n=1,
        direction="CALL",
        min_volume=0,
    )

    assert len(selected) == 1
    assert selected[0].symbol == "TEST-C-5100"


def test_loaded_put_contracts_can_be_scanned() -> None:
    """Loaded PUT contracts should be scanned correctly."""

    page = object.__new__(
        ScannerPage
    )

    from data.market_data_adapter import (
        MarketDataAdapter,
    )

    page.market_data_adapter = (
        MarketDataAdapter()
    )

    page.contracts = []
    page.selected_contracts = []
    page.scanner = None

    page.load_market_data(
        make_records()
    )

    selected = page.scan_contracts(
        page.contracts,
        top_n=1,
        direction="PUT",
        min_volume=0,
    )

    assert len(selected) == 1
    assert selected[0].symbol == "TEST-P-5000"


def test_loaded_contracts_support_min_volume() -> None:
    """Minimum volume filtering should work after loading."""

    page = object.__new__(
        ScannerPage
    )

    from data.market_data_adapter import (
        MarketDataAdapter,
    )

    page.market_data_adapter = (
        MarketDataAdapter()
    )

    page.contracts = []
    page.selected_contracts = []
    page.scanner = None

    page.load_market_data(
        make_records()
    )

    selected = page.scan_contracts(
        page.contracts,
        top_n=10,
        direction="全部",
        min_volume=200,
    )

    assert len(selected) == 2

    symbols = {
        contract.symbol
        for contract in selected
    }

    assert symbols == {
        "TEST-C-5100",
        "TEST-P-5000",
    }


def test_market_data_adapter_is_reusable() -> None:
    """The same adapter instance can load multiple datasets."""

    page = object.__new__(
        ScannerPage
    )

    from data.market_data_adapter import (
        MarketDataAdapter,
    )

    page.market_data_adapter = (
        MarketDataAdapter()
    )

    page.contracts = []
    page.selected_contracts = []
    page.scanner = None

    first = page.load_market_data(
        make_records()
    )

    second_records = [
        {
            "symbol": "NEW-C-6000",
            "direction": "CALL",
            "strike": 6000,
            "price": 50,
            "volume": 999,
            "open_interest": 888,
        }
    ]

    second = page.load_market_data(
        second_records
    )

    assert len(first) == 4
    assert len(second) == 1
    assert page.contracts[0].symbol == "NEW-C-6000"