"""
Commodity Option Valuator Pro
=============================

Market Data Adapter.

Commit 0012
------------

Provide a unified interface between external
market-data sources and the application.

Supported source concepts
-------------------------
- Excel
- TDX
- DDE
- Future market-data providers

The adapter does not directly implement a
specific external data source. It normalizes
market data into OptionContract objects so
the UI and scanner remain independent from
the underlying data provider.

Author : Simon
Version : 0.3.1
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)
from datetime import (
    datetime,
)
from typing import (
    Any,
    Iterable,
    Mapping,
)

from models.option_scanner import (
    OptionContract,
    OptionDirection,
)


# ==========================================================
# Market Data Snapshot
# ==========================================================


@dataclass(frozen=True)
class MarketDataSnapshot:
    """
    Immutable market-data snapshot.

    Parameters
    ----------
    contracts:
        Normalized option contracts.

    source:
        Data-source identifier.

    timestamp:
        Snapshot creation time.

    metadata:
        Optional source metadata.
    """

    contracts: tuple[OptionContract, ...]

    source: str = "unknown"

    timestamp: datetime = field(
        default_factory=datetime.now
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def count(self) -> int:
        """Return number of option contracts."""

        return len(
            self.contracts
        )

    def to_list(self) -> list[OptionContract]:
        """Return contracts as a mutable list."""

        return list(
            self.contracts
        )


# ==========================================================
# Market Data Adapter
# ==========================================================


class MarketDataAdapter:
    """
    Unified market-data normalization layer.

    The adapter converts external records into
    OptionContract instances.

    External readers such as Excel, TDX, or DDE
    should eventually provide records to this
    adapter rather than being coupled directly
    to the UI.
    """

    DEFAULT_SOURCE = "unknown"

    REQUIRED_FIELDS = (
        "symbol",
        "direction",
        "strike",
        "price",
        "volume",
    )

    OPTIONAL_FIELDS = (
        "open_interest",
        "bid",
        "ask",
    )

    # ======================================================
    # Construction
    # ======================================================

    def __init__(
        self,
        source: str = DEFAULT_SOURCE,
    ) -> None:
        """
        Initialize market-data adapter.

        Parameters
        ----------
        source:
            Name of the market-data source.
        """

        source_text = str(
            source
        ).strip()

        self.source = (
            source_text
            if source_text
            else self.DEFAULT_SOURCE
        )

    # ======================================================
    # Direction Parsing
    # ======================================================

    @staticmethod
    def parse_direction(
        value: object,
    ) -> OptionDirection:
        """
        Convert an external direction value
        into OptionDirection.

        Accepted values include
        ------------------------
        CALL
        PUT
        call
        put
        """

        if isinstance(
            value,
            OptionDirection,
        ):
            return value

        if value is None:
            raise ValueError(
                "期权方向不能为空。"
            )

        normalized = str(
            value
        ).strip().upper()

        try:
            return OptionDirection(
                normalized
            )
        except ValueError as exc:
            raise ValueError(
                f"无效的期权方向：{value}"
            ) from exc

    # ======================================================
    # Numeric Parsing
    # ======================================================

    @staticmethod
    def parse_float(
        value: object,
        field_name: str,
        *,
        allow_zero: bool = True,
        allow_negative: bool = False,
    ) -> float:
        """
        Convert an external value into float.

        Parameters
        ----------
        value:
            Raw external value.

        field_name:
            Human-readable field name.

        allow_zero:
            Whether zero is accepted.

        allow_negative:
            Whether negative values are accepted.
        """

        try:
            result = float(
                value
            )
        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                f"{field_name}必须是有效数字。"
            ) from exc

        if not allow_negative and result < 0:
            raise ValueError(
                f"{field_name}不能小于 0。"
            )

        if not allow_zero and result == 0:
            raise ValueError(
                f"{field_name}必须大于 0。"
            )

        return result

    @staticmethod
    def parse_int(
        value: object,
        field_name: str,
        *,
        allow_zero: bool = True,
        allow_negative: bool = False,
    ) -> int:
        """
        Convert an external value into int.
        """

        try:
            result = int(
                value
            )
        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                f"{field_name}必须是整数。"
            ) from exc

        if not allow_negative and result < 0:
            raise ValueError(
                f"{field_name}不能小于 0。"
            )

        if not allow_zero and result == 0:
            raise ValueError(
                f"{field_name}必须大于 0。"
            )

        return result

    # ======================================================
    # Record Normalization
    # ======================================================

    def normalize_record(
        self,
        record: Mapping[str, object],
    ) -> OptionContract:
        """
        Normalize one external market-data record.

        Expected fields
        ---------------
        symbol
        direction
        strike
        price
        volume

        Optional fields
        ---------------
        open_interest
        bid
        ask
        """

        if not isinstance(
            record,
            Mapping,
        ):
            raise TypeError(
                "市场数据记录必须是 Mapping。"
            )

        for field_name in self.REQUIRED_FIELDS:

            if field_name not in record:
                raise ValueError(
                    f"缺少必要字段：{field_name}"
                )

        symbol = str(
            record["symbol"]
        ).strip()

        if not symbol:
            raise ValueError(
                "合约代码不能为空。"
            )

        direction = self.parse_direction(
            record["direction"]
        )

        strike = self.parse_float(
            record["strike"],
            "行权价",
            allow_zero=False,
        )

        price = self.parse_float(
            record["price"],
            "市场价格",
        )

        volume = self.parse_int(
            record["volume"],
            "成交量",
        )

        open_interest = self.parse_int(
            record.get(
                "open_interest",
                0,
            ),
            "持仓量",
        )

        bid = self.parse_float(
            record.get(
                "bid",
                0.0,
            ),
            "买价",
        )

        ask = self.parse_float(
            record.get(
                "ask",
                0.0,
            ),
            "卖价",
        )

        return OptionContract(
            symbol=symbol,
            direction=direction,
            strike=strike,
            price=price,
            volume=volume,
            open_interest=open_interest,
            bid=bid,
            ask=ask,
        )

    # ======================================================
    # Batch Normalization
    # ======================================================

    def normalize_records(
        self,
        records: Iterable[
            Mapping[str, object]
        ],
    ) -> list[OptionContract]:
        """
        Normalize multiple external records.

        Invalid records raise ValueError instead
        of being silently discarded.
        """

        contracts: list[
            OptionContract
        ] = []

        for record in records:

            contracts.append(
                self.normalize_record(
                    record
                )
            )

        return contracts

    # ======================================================
    # Snapshot Creation
    # ======================================================

    def create_snapshot(
        self,
        records: Iterable[
            Mapping[str, object]
        ],
        *,
        metadata: Mapping[
            str,
            object,
        ]
        | None = None,
    ) -> MarketDataSnapshot:
        """
        Normalize records and create a snapshot.
        """

        contracts = (
            self.normalize_records(
                records
            )
        )

        snapshot_metadata: dict[
            str,
            Any,
        ] = {}

        if metadata is not None:
            snapshot_metadata.update(
                metadata
            )

        return MarketDataSnapshot(
            contracts=tuple(
                contracts
            ),
            source=self.source,
            metadata=snapshot_metadata,
        )

    # ======================================================
    # Contract Validation
    # ======================================================

    @staticmethod
    def validate_contract(
        contract: OptionContract,
    ) -> bool:
        """
        Validate a normalized OptionContract.
        """

        if not isinstance(
            contract,
            OptionContract,
        ):
            return False

        if not contract.symbol:
            return False

        if contract.direction not in (
            OptionDirection.CALL,
            OptionDirection.PUT,
        ):
            return False

        if contract.strike <= 0:
            return False

        if contract.price < 0:
            return False

        if contract.volume < 0:
            return False

        if contract.open_interest < 0:
            return False

        if contract.bid < 0:
            return False

        if contract.ask < 0:
            return False

        return True

    # ======================================================
    # Contract Filtering
    # ======================================================

    @staticmethod
    def valid_contracts(
        contracts: Iterable[
            OptionContract
        ],
    ) -> list[OptionContract]:
        """
        Return only valid OptionContract objects.
        """

        return [
            contract
            for contract in contracts
            if MarketDataAdapter.validate_contract(
                contract
            )
        ]

    # ======================================================
    # Snapshot From Contracts
    # ======================================================

    def snapshot_from_contracts(
        self,
        contracts: Iterable[
            OptionContract
        ],
        *,
        metadata: Mapping[
            str,
            object,
        ]
        | None = None,
    ) -> MarketDataSnapshot:
        """
        Create a snapshot from already normalized
        OptionContract objects.
        """

        normalized = list(
            contracts
        )

        invalid = [
            contract
            for contract in normalized
            if not self.validate_contract(
                contract
            )
        ]

        if invalid:
            raise ValueError(
                "市场数据中存在无效的 OptionContract。"
            )

        snapshot_metadata: dict[
            str,
            Any,
        ] = {}

        if metadata is not None:
            snapshot_metadata.update(
                metadata
            )

        return MarketDataSnapshot(
            contracts=tuple(
                normalized
            ),
            source=self.source,
            metadata=snapshot_metadata,
        )

    # ======================================================
    # Dictionary Export
    # ======================================================

    @staticmethod
    def contract_to_dict(
        contract: OptionContract,
    ) -> dict[str, object]:
        """
        Convert OptionContract to dictionary.
        """

        if not MarketDataAdapter.validate_contract(
            contract
        ):
            raise ValueError(
                "无效的 OptionContract。"
            )

        return {
            "symbol": contract.symbol,
            "direction": (
                contract.direction.value
            ),
            "strike": contract.strike,
            "price": contract.price,
            "volume": contract.volume,
            "open_interest": (
                contract.open_interest
            ),
            "bid": contract.bid,
            "ask": contract.ask,
        }

    def snapshot_to_dict(
        self,
        snapshot: MarketDataSnapshot,
    ) -> dict[str, object]:
        """
        Convert snapshot into dictionary.
        """

        return {
            "source": snapshot.source,
            "timestamp": (
                snapshot.timestamp.isoformat()
            ),
            "count": snapshot.count,
            "contracts": [
                self.contract_to_dict(
                    contract
                )
                for contract
                in snapshot.contracts
            ],
            "metadata": dict(
                snapshot.metadata
            ),
        }

    # ======================================================
    # Properties
    # ======================================================

    def __str__(
        self,
    ) -> str:
        """Return human-readable adapter name."""

        return (
            f"MarketDataAdapter("
            f"source={self.source!r}"
            f")"
        )

    def __repr__(
        self,
    ) -> str:
        """Return developer representation."""

        return (
            f"MarketDataAdapter("
            f"source={self.source!r}"
            f")"
        )


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "MarketDataAdapter",
    "MarketDataSnapshot",
]