"""
Commodity Option Valuator Pro
=============================

Option Scanner Workspace.

Commit 0029-B
--------------

Connect the option scanner workspace with
the market data adapter.

Author : Simon
Version : 0.3.3
"""

from __future__ import annotations

import customtkinter as ctk

from data.market_data_adapter import (
    MarketDataAdapter,
)

from core.scanner_batch_valuation import (
    BatchValuationParameters,
    BatchValuationResult,
    ScannerBatchValuator,
)
from data.option_chain import (
    OptionQuote,
)

from models.option_scanner import (
    OptionContract,
    OptionDirection,
    OptionScanner,
)

from ui.components import (
    PrimaryButton,
    SectionCard,
)

from ui.styles import (
    COLOR_DANGER,
    COLOR_SUCCESS,
    COLOR_TEXT,
    COLOR_TEXT_SECONDARY,
    CONTENT_PADDING,
    FONT_BODY_SIZE,
    FONT_FAMILY,
    FONT_SMALL_SIZE,
    FONT_SUBTITLE_SIZE,
)


# ==========================================================
# Scanner Page
# ==========================================================


class ScannerPage(ctk.CTkFrame):
    """
    Option chain scanner workspace.

    Commit 0013 connects the UI with the existing
    MarketDataAdapter and OptionScanner.

    Responsibilities
    ----------------
    - Collect scanner parameters.
    - Load and normalize market data.
    - Build scanner contracts.
    - Execute option chain scanning.
    - Display selected CALL / PUT contracts.
    - Provide a stable UI boundary for future
      market-data source integration.
    """

    RESULT_COLUMNS = (
        "symbol",
        "direction",
        "strike",
        "price",
        "volume",
        "open_interest",
    )

    RESULT_TITLES = {
        "symbol": "合约代码",
        "direction": "方向",
        "strike": "行权价",
        "price": "市场价格",
        "volume": "成交量",
        "open_interest": "持仓量",
    }

    def __init__(
        self,
        master,
        **kwargs,
    ) -> None:

        super().__init__(
            master,
            fg_color="transparent",
            corner_radius=0,
            **kwargs,
        )

        self.grid_columnconfigure(
            0,
            weight=1,
        )

        self.grid_rowconfigure(
            1,
            weight=1,
        )

        self.contracts: list[
            OptionContract
        ] = []

        self.selected_contracts: list[
            OptionContract
        ] = []

        self.valuation_result: (
            BatchValuationResult | None
        ) = None

        self.scanner: OptionScanner | None = None

        self.market_data_adapter = (
            MarketDataAdapter()
        )

        self.create_header()

        self.create_workspace()

    # ======================================================
    # Header
    # ======================================================

    def create_header(self) -> None:
        """Create scanner workspace heading."""

        self.header = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )

        self.header.grid(
            row=0,
            column=0,
            padx=CONTENT_PADDING,
            pady=CONTENT_PADDING,
            sticky="ew",
        )

        self.header.grid_columnconfigure(
            0,
            weight=1,
        )

        self.title = ctk.CTkLabel(
            self.header,
            text="期权扫描工作台",
            text_color=COLOR_TEXT,
            font=(
                FONT_FAMILY,
                24,
                "bold",
            ),
            anchor="w",
        )

        self.title.grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.subtitle = ctk.CTkLabel(
            self.header,
            text=(
                "载入期权链并按照成交量筛选活跃合约"
            ),
            text_color=COLOR_TEXT_SECONDARY,
            font=(
                FONT_FAMILY,
                FONT_BODY_SIZE,
            ),
            anchor="w",
        )

        self.subtitle.grid(
            row=1,
            column=0,
            pady=(4, 0),
            sticky="w",
        )

    # ======================================================
    # Workspace
    # ======================================================

    def create_workspace(self) -> None:
        """Create scanner workspace."""

        self.workspace = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )

        self.workspace.grid(
            row=1,
            column=0,
            padx=CONTENT_PADDING,
            pady=(0, CONTENT_PADDING),
            sticky="nsew",
        )

        self.workspace.grid_columnconfigure(
            0,
            weight=0,
        )

        self.workspace.grid_columnconfigure(
            1,
            weight=1,
        )

        self.workspace.grid_rowconfigure(
            0,
            weight=1,
        )

        self.create_parameter_section()

        self.create_result_section()

    # ======================================================
    # Parameter Section
    # ======================================================

    def create_parameter_section(self) -> None:
        """Create scanner parameter section."""

        self.parameter_section = SectionCard(
            self.workspace,
            title="扫描参数",
        )

        self.parameter_section.grid(
            row=0,
            column=0,
            padx=(0, 8),
            sticky="nsw",
        )

        self.parameter_section.content.grid_columnconfigure(
            1,
            weight=1,
        )

        self.create_parameter_label(
            row=0,
            text="TOP N",
        )

        self.top_n_entry = ctk.CTkEntry(
            self.parameter_section.content,
            placeholder_text="例如 5",
        )

        self.top_n_entry.grid(
            row=0,
            column=1,
            padx=(8, 8),
            pady=6,
            sticky="ew",
        )

        self.top_n_entry.insert(
            0,
            "5",
        )

        self.create_parameter_label(
            row=1,
            text="最低成交量",
        )

        self.min_volume_entry = ctk.CTkEntry(
            self.parameter_section.content,
            placeholder_text="例如 0",
        )

        self.min_volume_entry.grid(
            row=1,
            column=1,
            padx=(8, 8),
            pady=6,
            sticky="ew",
        )

        self.min_volume_entry.insert(
            0,
            "0",
        )

        self.create_parameter_label(
            row=2,
            text="扫描方向",
        )

        self.direction_selector = ctk.CTkSegmentedButton(
            self.parameter_section.content,
            values=[
                "全部",
                "CALL",
                "PUT",
            ],
        )

        self.direction_selector.set(
            "全部"
        )

        self.direction_selector.grid(
            row=2,
            column=1,
            padx=(8, 8),
            pady=6,
            sticky="ew",
        )

        self.scan_button = PrimaryButton(
            self.parameter_section.content,
            text="开始扫描",
            command=self.on_scan,
        )

        self.scan_button.grid(
            row=3,
            column=0,
            columnspan=2,
            padx=8,
            pady=(18, 8),
            sticky="ew",
        )

        self.clear_button = ctk.CTkButton(
            self.parameter_section.content,
            text="清空结果",
            command=self.reset_results,
        )

        self.clear_button.grid(
            row=4,
            column=0,
            columnspan=2,
            padx=8,
            pady=6,
            sticky="ew",
        )

        self.status_label = ctk.CTkLabel(
            self.parameter_section.content,
            text="等待扫描",
            text_color=COLOR_TEXT_SECONDARY,
            font=(
                FONT_FAMILY,
                FONT_SMALL_SIZE,
            ),
            justify="left",
            anchor="w",
        )

        self.status_label.grid(
            row=5,
            column=0,
            columnspan=2,
            padx=8,
            pady=(14, 8),
            sticky="ew",
        )

    # ======================================================
    # Parameter Helpers
    # ======================================================

    def create_parameter_label(
        self,
        row: int,
        text: str,
    ) -> None:
        """Create a scanner parameter label."""

        label = ctk.CTkLabel(
            self.parameter_section.content,
            text=text,
            text_color=COLOR_TEXT_SECONDARY,
            font=(
                FONT_FAMILY,
                FONT_BODY_SIZE,
            ),
            anchor="w",
        )

        label.grid(
            row=row,
            column=0,
            padx=8,
            pady=6,
            sticky="w",
        )

    # ======================================================
    # Result Section
    # ======================================================

    def create_result_section(self) -> None:
        """Create scanner result section."""

        self.result_section = SectionCard(
            self.workspace,
            title="扫描结果",
        )

        self.result_section.grid(
            row=0,
            column=1,
            padx=(8, 0),
            sticky="nsew",
        )

        self.result_section.content.grid_columnconfigure(
            0,
            weight=1,
        )

        self.result_section.content.grid_rowconfigure(
            1,
            weight=1,
        )

        self.summary_label = ctk.CTkLabel(
            self.result_section.content,
            text="暂无扫描结果",
            text_color=COLOR_TEXT_SECONDARY,
            font=(
                FONT_FAMILY,
                FONT_SMALL_SIZE,
            ),
            anchor="w",
        )

        self.summary_label.grid(
            row=0,
            column=0,
            padx=8,
            pady=(0, 8),
            sticky="ew",
        )

        self.table_frame = ctk.CTkScrollableFrame(
            self.result_section.content,
            fg_color="transparent",
        )

        self.table_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
        )

        self.table_frame.grid_columnconfigure(
            0,
            weight=1,
        )

        self.result_labels: list[
            ctk.CTkLabel
        ] = []

    # ======================================================
    # Input Parsing
    # ======================================================

    @staticmethod
    def parse_top_n(
        value: str,
    ) -> int:
        """
        Parse TOP N.

        Raises
        ------
        ValueError
            If value is invalid.
        """

        try:
            top_n = int(
                value.strip()
            )
        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "TOP N 必须是整数。"
            ) from exc

        if top_n <= 0:
            raise ValueError(
                "TOP N 必须大于 0。"
            )

        return top_n

    @staticmethod
    def parse_min_volume(
        value: str,
    ) -> int:
        """
        Parse minimum volume.

        Raises
        ------
        ValueError
            If value is invalid.
        """

        try:
            min_volume = int(
                value.strip()
            )
        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "最低成交量必须是整数。"
            ) from exc

        if min_volume < 0:
            raise ValueError(
                "最低成交量不能小于 0。"
            )

        return min_volume

    # ======================================================
    # Contract Filtering
    # ======================================================

    @staticmethod
    def filter_contracts(
        contracts: list[OptionContract],
        direction: str,
        min_volume: int,
    ) -> list[OptionContract]:
        """
        Filter option contracts.

        Parameters
        ----------
        contracts:
            Source option contracts.

        direction:
            全部 / CALL / PUT.

        min_volume:
            Minimum trading volume.
        """

        if direction not in {
            "全部",
            "CALL",
            "PUT",
        }:
            raise ValueError(
                "无效的扫描方向。"
            )

        filtered = [
            contract
            for contract in contracts
            if contract.volume >= min_volume
        ]

        if direction == "CALL":

            filtered = [
                contract
                for contract in filtered
                if contract.direction
                == OptionDirection.CALL
            ]

        elif direction == "PUT":

            filtered = [
                contract
                for contract in filtered
                if contract.direction
                == OptionDirection.PUT
            ]

        return filtered

    # ======================================================
    # Scanner Execution
    # ======================================================

    def scan_contracts(
        self,
        contracts: list[OptionContract],
        top_n: int,
        direction: str = "全部",
        min_volume: int = 0,
    ) -> list[OptionContract]:
        """
        Execute scanner against supplied contracts.

        This method intentionally accepts market data
        from outside the UI so that Excel / TDX / DDE
        readers can connect without changing the
        scanner page interface.
        """

        filtered = self.filter_contracts(
            contracts,
            direction,
            min_volume,
        )

        scanner = OptionScanner(
            filtered,
            top_n=top_n,
        )

        self.scanner = scanner

        if direction == "CALL":

            return scanner.top_calls()

        if direction == "PUT":

            return scanner.top_puts()

        return scanner.selected()

    # ======================================================
    # Scan Action
    # ======================================================

    def on_scan(self) -> None:
        """
        Execute scanner using current contract data.
        """

        try:

            top_n = self.parse_top_n(
                self.top_n_entry.get()
            )

            min_volume = self.parse_min_volume(
                self.min_volume_entry.get()
            )

            direction = (
                self.direction_selector.get()
            )

            selected = self.scan_contracts(
                self.contracts,
                top_n=top_n,
                direction=direction,
                min_volume=min_volume,
            )

        except ValueError as exc:

            self.status_label.configure(
                text=str(exc),
                text_color=COLOR_DANGER,
            )

            return

        self.selected_contracts = selected

        self.display_results(
            selected
        )

        self.status_label.configure(
            text=(
                f"扫描完成，共筛选 "
                f"{len(selected)} 个合约。"
            ),
            text_color=COLOR_SUCCESS,
        )

    # ======================================================
    # Result Display
    # ======================================================

    def display_results(
        self,
        contracts: list[OptionContract],
    ) -> None:
        """Display scanner results."""

        self.clear_result_widgets()

        if not contracts:

            if hasattr(
                self,
                "summary_label",
            ):

                self.summary_label.configure(
                    text="没有符合条件的期权合约。"
                )

            return

        if hasattr(
            self,
            "summary_label",
        ):

            self.summary_label.configure(
                text=(
                    f"共找到 {len(contracts)} 个合约"
                )
            )

        for column, key in enumerate(
            self.RESULT_COLUMNS
        ):

            label = ctk.CTkLabel(
                self.table_frame,
                text=self.RESULT_TITLES[key],
                text_color=COLOR_TEXT_SECONDARY,
                font=(
                    FONT_FAMILY,
                    FONT_SMALL_SIZE,
                    "bold",
                ),
                anchor="w",
            )

            label.grid(
                row=0,
                column=column,
                padx=6,
                pady=6,
                sticky="w",
            )

            self.result_labels.append(
                label
            )

        for row, contract in enumerate(
            contracts,
            start=1,
        ):

            values = {
                "symbol": contract.symbol,
                "direction": (
                    contract.direction.value
                ),
                "strike": (
                    f"{contract.strike:.4f}"
                ),
                "price": (
                    f"{contract.price:.6f}"
                ),
                "volume": str(
                    contract.volume
                ),
                "open_interest": str(
                    contract.open_interest
                ),
            }

            for column, key in enumerate(
                self.RESULT_COLUMNS
            ):

                label = ctk.CTkLabel(
                    self.table_frame,
                    text=values[key],
                    text_color=COLOR_TEXT,
                    font=(
                        FONT_FAMILY,
                        FONT_SMALL_SIZE,
                    ),
                    anchor="w",
                )

                label.grid(
                    row=row,
                    column=column,
                    padx=6,
                    pady=5,
                    sticky="w",
                )

                self.result_labels.append(
                    label
                )

    # ======================================================
    # Batch Valuation Execution
    # ======================================================

    def evaluate_quotes(
        self,
        quotes: list[OptionQuote] | tuple[OptionQuote, ...],
        *,
        top_n: int,
        parameters: BatchValuationParameters,
        valuator: ScannerBatchValuator | None = None,
    ) -> BatchValuationResult:
        """
        Execute the existing scanner batch valuation workflow.

        This method is the execution boundary for the Scanner UI.
        It deliberately accepts normalized ``OptionQuote`` objects
        because ``ScannerBatchValuator`` already defines the
        OptionQuote -> ScannerCandidate -> valuation pipeline.

        No pricing, Greeks, IV, Taylor, risk, or recommendation
        calculation is implemented here.

        The resulting ``BatchValuationResult`` is stored on the page
        and passed to the existing presentation boundary.
        """

        if not isinstance(
            quotes,
            (list, tuple),
        ):
            raise TypeError(
                "quotes must be a list or tuple of OptionQuote."
            )

        for quote in quotes:
            if not isinstance(
                quote,
                OptionQuote,
            ):
                raise TypeError(
                    "quotes must contain OptionQuote."
                )

        if not isinstance(
            parameters,
            BatchValuationParameters,
        ):
            raise TypeError(
                "parameters must be BatchValuationParameters."
            )

        batch_valuator = (
            valuator
            if valuator is not None
            else ScannerBatchValuator()
        )

        result = batch_valuator.scan_and_evaluate(
            quotes,
            top_n=top_n,
            parameters=parameters,
        )

        self.valuation_result = result

        if hasattr(
            self,
            "display_valuation_results",
        ):
            self.display_valuation_results(
                result
            )

        if hasattr(
            self,
            "status_label",
        ):
            self.status_label.configure(
                text=(
                    f"综合估值完成，共评价 "
                    f"{result.count} 个合约。"
                ),
                text_color=COLOR_SUCCESS,
            )

        return result

    # ======================================================
    # Batch Valuation Result
    # ======================================================

    @staticmethod
    def build_valuation_display_rows(
        batch_result: BatchValuationResult,
    ) -> list[dict[str, str]]:
        """
        Convert an existing batch valuation result into UI rows.

        This method deliberately consumes the already-computed
        ``BatchValuationResult``. It does not perform valuation,
        risk analysis, or recommendation calculations.

        The scanner UI therefore remains independent from the
        valuation calculation pipeline.
        """

        if not isinstance(
            batch_result,
            BatchValuationResult,
        ):
            raise TypeError(
                "batch_result must be a BatchValuationResult."
            )

        rows: list[dict[str, str]] = []

        for item in batch_result.items:
            evaluation = item.result.comprehensive_evaluation

            if evaluation is None:
                rows.append(
                    {
                        "symbol": item.symbol,
                        "option_type": item.option_type,
                        "volume": str(item.volume),
                        "theoretical_price": (
                            f"{item.result.current_theoretical_price:.6f}"
                        ),
                        "score": "--",
                        "decision": "--",
                        "risk_level": "--",
                        "reason": "暂无综合评价结果。",
                    }
                )
                continue

            rows.append(
                {
                    "symbol": item.symbol,
                    "option_type": item.option_type,
                    "volume": str(item.volume),
                    "theoretical_price": (
                        f"{item.result.current_theoretical_price:.6f}"
                    ),
                    "score": f"{evaluation.score:.2f}",
                    "decision": evaluation.decision.value,
                    "risk_level": evaluation.risk_level.value,
                    "reason": evaluation.reason_text,
                }
            )

        return rows

    def display_valuation_results(
        self,
        batch_result: BatchValuationResult,
    ) -> None:
        """
        Display an existing scanner batch valuation result.

        This is a presentation-only boundary. The batch valuation
        must already have been performed by ``ScannerBatchValuator``.
        """

        self.valuation_result = batch_result

        self.clear_result_widgets()

        rows = self.build_valuation_display_rows(
            batch_result
        )

        if hasattr(self, "summary_label"):
            self.summary_label.configure(
                text=(
                    f"综合估值完成，共评价 "
                    f"{len(rows)} 个合约。"
                )
            )

        columns = (
            "symbol",
            "option_type",
            "volume",
            "theoretical_price",
            "score",
            "decision",
            "risk_level",
            "reason",
        )

        titles = {
            "symbol": "合约代码",
            "option_type": "类型",
            "volume": "成交量",
            "theoretical_price": "理论价格",
            "score": "综合评分",
            "decision": "综合结论",
            "risk_level": "风险等级",
            "reason": "评价原因",
        }

        for column, key in enumerate(columns):
            label = ctk.CTkLabel(
                self.table_frame,
                text=titles[key],
                text_color=COLOR_TEXT_SECONDARY,
                font=(
                    FONT_FAMILY,
                    FONT_SMALL_SIZE,
                    "bold",
                ),
                anchor="w",
            )
            label.grid(
                row=0,
                column=column,
                padx=6,
                pady=6,
                sticky="w",
            )
            self.result_labels.append(label)

        for row_number, row_data in enumerate(
            rows,
            start=1,
        ):
            for column, key in enumerate(columns):
                label = ctk.CTkLabel(
                    self.table_frame,
                    text=row_data[key],
                    text_color=COLOR_TEXT,
                    font=(
                        FONT_FAMILY,
                        FONT_SMALL_SIZE,
                    ),
                    anchor="w",
                    justify="left",
                    wraplength=320 if key == "reason" else 0,
                )
                label.grid(
                    row=row_number,
                    column=column,
                    padx=6,
                    pady=5,
                    sticky="w",
                )
                self.result_labels.append(label)

    # ======================================================
    # Result Reset
    # ======================================================

    def clear_result_widgets(self) -> None:
        """
        Remove current result table widgets.

        This method intentionally supports objects
        constructed through object.__new__ during
        unit testing, where normal Tkinter initialization
        has not occurred yet.
        """

        if not hasattr(
            self,
            "result_labels",
        ):
            return

        for widget in self.result_labels:

            try:
                widget.destroy()
            except Exception:
                pass

        self.result_labels.clear()

    def reset_results(self) -> None:
        """Reset scanner result state."""

        self.selected_contracts = []

        self.valuation_result = None

        self.scanner = None

        self.clear_result_widgets()

        if hasattr(
            self,
            "summary_label",
        ):

            self.summary_label.configure(
                text="暂无扫描结果"
            )

        if hasattr(
            self,
            "status_label",
        ):

            self.status_label.configure(
                text="等待扫描",
                text_color=COLOR_TEXT_SECONDARY,
            )

    # ======================================================
    # Market Data Adapter
    # ======================================================

    def load_market_data(
        self,
        records,
    ) -> list[OptionContract]:
        """
        Load raw market data through MarketDataAdapter.

        Parameters
        ----------
        records:
            Raw market-data records.

        Returns
        -------
        list[OptionContract]
            A copy of the normalized contracts.

        Notes
        -----
        The adapter is intentionally kept outside the
        scanner model so that different market-data
        sources can be connected later.
        """

        if not hasattr(
            self,
            "market_data_adapter",
        ):

            self.market_data_adapter = (
                MarketDataAdapter()
            )

        contracts = (
            self.market_data_adapter.normalize_records(
                records
            )
        )

        self.set_contracts(
            contracts
        )

        return list(
            self.contracts
        )

    def set_contracts(
        self,
        contracts: list[OptionContract],
    ) -> None:
        """
        Inject normalized option chain market data.

        Future Excel / TDX / DDE readers can call
        this method directly.
        """

        self.contracts = list(
            contracts
        )

        self.selected_contracts = []

        self.valuation_result = None

        self.scanner = None

        self.clear_result_widgets()

        if hasattr(
            self,
            "summary_label",
        ):

            self.summary_label.configure(
                text=(
                    f"已载入 {len(self.contracts)} 个合约，"
                    "等待扫描。"
                )
            )

        if hasattr(
            self,
            "status_label",
        ):

            self.status_label.configure(
                text="市场数据已载入。",
                text_color=COLOR_SUCCESS,
            )

    # ======================================================
    # Market Data Snapshot
    # ======================================================

    def get_market_data(
        self,
    ) -> list[OptionContract]:
        """
        Return a copy of currently loaded contracts.
        """

        return list(
            self.contracts
        )

    def clear_market_data(self) -> None:
        """
        Clear currently loaded market data.
        """

        self.contracts = []

        self.selected_contracts = []

        self.valuation_result = None

        self.scanner = None

        self.clear_result_widgets()

        if hasattr(
            self,
            "summary_label",
        ):

            self.summary_label.configure(
                text="暂无市场数据"
            )

        if hasattr(
            self,
            "status_label",
        ):

            self.status_label.configure(
                text="市场数据已清空。",
                text_color=COLOR_TEXT_SECONDARY,
            )

    # ======================================================
    # Summary
    # ======================================================

    def get_summary(
        self,
    ) -> dict[str, object]:
        """
        Return scanner UI summary.
        """

        return {
            "contract_count": len(
                self.contracts
            ),
            "selected_count": len(
                self.selected_contracts
            ),
            "has_scanner": (
                self.scanner is not None
            ),
            "has_valuation_result": (
                self.valuation_result is not None
            ),
        }


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "ScannerPage",
]