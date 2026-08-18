"""
Tests for market-data adapter.

Commit 0012
"""

from datetime import datetime

import pytest

from data.market_data_adapter import (
    MarketDataAdapter,
    MarketDataSnapshot,
)

from models.option_scanner import (
    OptionContract,
    OptionDirection,
)


def make_record(
    symbol: str = "SR609C5600",
    direction: str = "CALL",
    strike: float = 5600.0,
    price: float = 120.0,
    volume: int = 100,
    open_interest: int = 200,
    bid: float = 118.0,
    ask: float = 122.0,
) -> dict[str, object]:

    return {
        "symbol": symbol,
        "direction": direction,
        "strike": strike,
        "price": price,
        "volume": volume,
        "open_interest": open_interest,
        "bid": bid,
        "ask": ask,
    }


# ==========================================================
# Adapter Construction
# ==========================================================


def test_adapter_import() -> None:

    adapter = MarketDataAdapter()

    assert adapter.source == "unknown"


def test_adapter_source() -> None:

    adapter = MarketDataAdapter(
        source="TDX"
    )

    assert adapter.source == "TDX"


def test_adapter_empty_source_uses_default() -> None:

    adapter = MarketDataAdapter(
        source=" "
    )

    assert adapter.source == "unknown"


# ==========================================================
# Direction
# ==========================================================


def test_parse_call_direction() -> None:

    adapter = MarketDataAdapter()

    result = adapter.parse_direction(
        "CALL"
    )

    assert result == OptionDirection.CALL


def test_parse_put_direction() -> None:

    adapter = MarketDataAdapter()

    result = adapter.parse_direction(
        "put"
    )

    assert result == OptionDirection.PUT


def test_parse_existing_direction() -> None:

    adapter = MarketDataAdapter()

    result = adapter.parse_direction(
        OptionDirection.CALL
    )

    assert result == OptionDirection.CALL


def test_parse_invalid_direction() -> None:

    adapter = MarketDataAdapter()

    with pytest.raises(
        ValueError,
        match="无效的期权方向",
    ):
        adapter.parse_direction(
            "INVALID"
        )


# ==========================================================
# Record Normalization
# ==========================================================


def test_normalize_record() -> None:

    adapter = MarketDataAdapter(
        source="TEST"
    )

    contract = adapter.normalize_record(
        make_record()
    )

    assert isinstance(
        contract,
        OptionContract,
    )

    assert contract.symbol == "SR609C5600"

    assert contract.direction == (
        OptionDirection.CALL
    )

    assert contract.strike == 5600.0

    assert contract.price == 120.0

    assert contract.volume == 100

    assert contract.open_interest == 200

    assert contract.bid == 118.0

    assert contract.ask == 122.0


def test_normalize_record_with_defaults() -> None:

    adapter = MarketDataAdapter()

    record = {
        "symbol": "SR609P5600",
        "direction": "PUT",
        "strike": 5600,
        "price": 100,
        "volume": 50,
    }

    contract = adapter.normalize_record(
        record
    )

    assert contract.direction == (
        OptionDirection.PUT
    )

    assert contract.open_interest == 0

    assert contract.bid == 0.0

    assert contract.ask == 0.0


def test_normalize_record_rejects_missing_field() -> None:

    adapter = MarketDataAdapter()

    record = make_record()

    del record["symbol"]

    with pytest.raises(
        ValueError,
        match="缺少必要字段",
    ):
        adapter.normalize_record(
            record
        )


def test_normalize_record_rejects_empty_symbol() -> None:

    adapter = MarketDataAdapter()

    record = make_record(
        symbol=" "
    )

    with pytest.raises(
        ValueError,
        match="合约代码不能为空",
    ):
        adapter.normalize_record(
            record
        )


def test_normalize_record_rejects_invalid_strike() -> None:

    adapter = MarketDataAdapter()

    record = make_record(
        strike=0
    )

    with pytest.raises(
        ValueError,
        match="行权价必须大于 0",
    ):
        adapter.normalize_record(
            record
        )


def test_normalize_record_rejects_negative_volume() -> None:

    adapter = MarketDataAdapter()

    record = make_record(
        volume=-1
    )

    with pytest.raises(
        ValueError,
        match="成交量不能小于 0",
    ):
        adapter.normalize_record(
            record
        )


# ==========================================================
# Batch Normalization
# ==========================================================


def test_normalize_records() -> None:

    adapter = MarketDataAdapter()

    records = [
        make_record(
            symbol="SR609C5600",
            direction="CALL",
        ),
        make_record(
            symbol="SR609P5600",
            direction="PUT",
        ),
    ]

    contracts = adapter.normalize_records(
        records
    )

    assert len(contracts) == 2

    assert contracts[0].direction == (
        OptionDirection.CALL
    )

    assert contracts[1].direction == (
        OptionDirection.PUT
    )


def test_normalize_records_empty() -> None:

    adapter = MarketDataAdapter()

    contracts = adapter.normalize_records(
        []
    )

    assert contracts == []


# ==========================================================
# Snapshot
# ==========================================================


def test_create_snapshot() -> None:

    adapter = MarketDataAdapter(
        source="TEST"
    )

    snapshot = adapter.create_snapshot(
        [
            make_record()
        ],
        metadata={
            "exchange": "CZCE"
        },
    )

    assert isinstance(
        snapshot,
        MarketDataSnapshot,
    )

    assert snapshot.source == "TEST"

    assert snapshot.count == 1

    assert isinstance(
        snapshot.timestamp,
        datetime,
    )

    assert snapshot.metadata[
        "exchange"
    ] == "CZCE"


def test_snapshot_to_list() -> None:

    adapter = MarketDataAdapter()

    snapshot = adapter.create_snapshot(
        [
            make_record()
        ]
    )

    contracts = snapshot.to_list()

    assert isinstance(
        contracts,
        list,
    )

    assert len(contracts) == 1


# ==========================================================
# Contract Validation
# ==========================================================


def test_validate_contract() -> None:

    contract = OptionContract(
        symbol="SR609C5600",
        direction=OptionDirection.CALL,
        strike=5600.0,
        price=120.0,
        volume=100,
    )

    assert MarketDataAdapter.validate_contract(
        contract
    )


def test_validate_invalid_contract_type() -> None:

    assert not MarketDataAdapter.validate_contract(
        "invalid"
    )


def test_valid_contracts() -> None:

    valid = OptionContract(
        symbol="SR609C5600",
        direction=OptionDirection.CALL,
        strike=5600.0,
        price=120.0,
        volume=100,
    )

    invalid = OptionContract(
        symbol="",
        direction=OptionDirection.CALL,
        strike=5600.0,
        price=120.0,
        volume=100,
    )

    result = MarketDataAdapter.valid_contracts(
        [
            valid,
            invalid,
        ]
    )

    assert result == [valid]


# ==========================================================
# Snapshot From Contracts
# ==========================================================


def test_snapshot_from_contracts() -> None:

    adapter = MarketDataAdapter(
        source="TDX"
    )

    contract = OptionContract(
        symbol="SR609C5600",
        direction=OptionDirection.CALL,
        strike=5600.0,
        price=120.0,
        volume=100,
    )

    snapshot = adapter.snapshot_from_contracts(
        [
            contract
        ]
    )

    assert snapshot.source == "TDX"

    assert snapshot.contracts == (
        contract,
    )


def test_snapshot_from_contracts_rejects_invalid() -> None:

    adapter = MarketDataAdapter()

    invalid = OptionContract(
        symbol="",
        direction=OptionDirection.CALL,
        strike=5600.0,
        price=120.0,
        volume=100,
    )

    with pytest.raises(
        ValueError,
        match="存在无效的 OptionContract",
    ):
        adapter.snapshot_from_contracts(
            [
                invalid
            ]
        )


# ==========================================================
# Dictionary Export
# ==========================================================


def test_contract_to_dict() -> None:

    adapter = MarketDataAdapter()

    contract = adapter.normalize_record(
        make_record()
    )

    result = adapter.contract_to_dict(
        contract
    )

    assert result == {
        "symbol": "SR609C5600",
        "direction": "CALL",
        "strike": 5600.0,
        "price": 120.0,
        "volume": 100,
        "open_interest": 200,
        "bid": 118.0,
        "ask": 122.0,
    }


def test_snapshot_to_dict() -> None:

    adapter = MarketDataAdapter(
        source="TEST"
    )

    snapshot = adapter.create_snapshot(
        [
            make_record()
        ]
    )

    result = adapter.snapshot_to_dict(
        snapshot
    )

    assert result["source"] == "TEST"

    assert result["count"] == 1

    assert len(
        result["contracts"]
    ) == 1