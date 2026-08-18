"""
Commodity Option Valuator Pro
=============================

Option Valuation Workspace.

Commit 0010
------------

Connect the valuation UI with the core valuation engine.

Author : Simon
Version : 0.2.2
"""

from __future__ import annotations

import customtkinter as ctk

from core.valuation_engine import (
    ValuationEngine,
    ValuationResult,
)

from models.option_scanner import (
    OptionContract,
    OptionDirection,
)

from ui.components import (
    PrimaryButton,
    SectionCard,
)

from ui.styles import (
    COLOR_DANGER,
    COLOR_TEXT,
    COLOR_TEXT_SECONDARY,
    CONTENT_PADDING,
    FONT_BODY_SIZE,
    FONT_FAMILY,
    FONT_SMALL_SIZE,
    FONT_SUBTITLE_SIZE,
)


# ==========================================================
# Valuation Page
# ==========================================================


class ValuationPage(ctk.CTkFrame):
    """
    Option valuation workspace.

    Commit 0010 connects the UI with the existing
    ValuationEngine.

    Responsibilities
    ----------------
    - Collect valuation parameters.
    - Validate user input.
    - Build OptionContract.
    - Execute ValuationEngine.
    - Display ValuationResult.
    """

    RESULT_KEYS = (
        "theoretical_price",
        "delta",
        "gamma",
        "theta",
        "vega",
        "difference",
        "risk_score",
    )

    RESULT_TITLES = {
        "theoretical_price": "理论价格",
        "delta": "Delta",
        "gamma": "Gamma",
        "theta": "Theta",
        "vega": "Vega",
        "difference": "估值差",
        "risk_score": "风险评分",
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

        self.engine = ValuationEngine()

        self.last_result: ValuationResult | None = None

        self.create_header()

        self.create_workspace()

    # ======================================================
    # Header
    # ======================================================

    def create_header(self) -> None:
        """Create valuation workspace heading."""

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
            text="期权估值工作台",
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
                "输入期权合约参数，"
                "计算理论价值与风险参数"
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
        """Create valuation workspace."""

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
            weight=1,
            uniform="valuation",
        )

        self.workspace.grid_columnconfigure(
            1,
            weight=1,
            uniform="valuation",
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
        """Create option parameter input section."""

        self.parameter_section = SectionCard(
            self.workspace,
            title="合约参数",
        )

        self.parameter_section.grid(
            row=0,
            column=0,
            padx=(0, 8),
            sticky="nsew",
        )

        self.parameter_section.content.grid_columnconfigure(
            1,
            weight=1,
        )

        self.create_parameter_label(
            row=0,
            text="合约代码",
        )

        self.symbol_entry = self.create_entry(
            row=0,
            placeholder="例如 SR609C5600",
        )

        self.create_parameter_label(
            row=1,
            text="标的价格",
        )

        self.spot_entry = self.create_entry(
            row=1,
            placeholder="例如 5600",
        )

        self.create_parameter_label(
            row=2,
            text="行权价格",
        )

        self.strike_entry = self.create_entry(
            row=2,
            placeholder="例如 5600",
        )

        self.create_parameter_label(
            row=3,
            text="市场价格",
        )

        self.market_price_entry = self.create_entry(
            row=3,
            placeholder="例如 120",
        )

        self.create_parameter_label(
            row=4,
            text="剩余天数",
        )

        self.days_entry = self.create_entry(
            row=4,
            placeholder="例如 30",
        )

        self.create_parameter_label(
            row=5,
            text="波动率",
        )

        self.volatility_entry = self.create_entry(
            row=5,
            placeholder="例如 0.20",
        )

        self.create_parameter_label(
            row=6,
            text="无风险利率",
        )

        self.rate_entry = self.create_entry(
            row=6,
            placeholder="默认 0.025",
        )

        self.create_parameter_label(
            row=7,
            text="期权方向",
        )

        self.direction_selector = ctk.CTkSegmentedButton(
            self.parameter_section.content,
            values=[
                "CALL",
                "PUT",
            ],
        )

        self.direction_selector.set(
            "CALL"
        )

        self.direction_selector.grid(
            row=7,
            column=1,
            padx=(8, 0),
            pady=6,
            sticky="ew",
        )

        self.valuate_button = PrimaryButton(
            self.parameter_section.content,
            text="开始估值",
            command=self.on_valuate,
        )

        self.valuate_button.grid(
            row=8,
            column=0,
            columnspan=2,
            padx=8,
            pady=(18, 8),
            sticky="ew",
        )

        self.parameter_hint = ctk.CTkLabel(
            self.parameter_section.content,
            text=(
                "输入完整参数后点击“开始估值”。"
                "\n"
                "波动率和无风险利率使用小数表示。"
                "\n"
                "例如 20% 输入 0.20。"
            ),
            text_color=COLOR_TEXT_SECONDARY,
            font=(
                FONT_FAMILY,
                FONT_SMALL_SIZE,
            ),
            justify="left",
            anchor="w",
        )

        self.parameter_hint.grid(
            row=9,
            column=0,
            columnspan=2,
            padx=8,
            pady=(12, 8),
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
        """Create a parameter label."""

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

    def create_entry(
        self,
        row: int,
        placeholder: str,
    ) -> ctk.CTkEntry:
        """Create a parameter entry."""

        entry = ctk.CTkEntry(
            self.parameter_section.content,
            placeholder_text=placeholder,
        )

        entry.grid(
            row=row,
            column=1,
            padx=(8, 0),
            pady=6,
            sticky="ew",
        )

        return entry

    # ======================================================
    # Result Section
    # ======================================================

    def create_result_section(self) -> None:
        """Create valuation result section."""

        self.result_section = SectionCard(
            self.workspace,
            title="估值结果",
        )

        self.result_section.grid(
            row=0,
            column=1,
            padx=(8, 0),
            sticky="nsew",
        )

        self.result_section.content.grid_columnconfigure(
            1,
            weight=1,
        )

        self.result_labels: dict[
            str,
            ctk.CTkLabel,
        ] = {}

        for row, key in enumerate(
            self.RESULT_KEYS
        ):

            title = self.RESULT_TITLES[
                key
            ]

            label = ctk.CTkLabel(
                self.result_section.content,
                text=title,
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
                pady=8,
                sticky="w",
            )

            value_label = ctk.CTkLabel(
                self.result_section.content,
                text="--",
                text_color=COLOR_TEXT,
                font=(
                    FONT_FAMILY,
                    FONT_SUBTITLE_SIZE,
                    "bold",
                ),
                anchor="e",
            )

            value_label.grid(
                row=row,
                column=1,
                padx=8,
                pady=8,
                sticky="e",
            )

            self.result_labels[
                key
            ] = value_label

        self.error_label = ctk.CTkLabel(
            self.result_section.content,
            text="",
            text_color=COLOR_DANGER,
            font=(
                FONT_FAMILY,
                FONT_SMALL_SIZE,
            ),
            justify="left",
            anchor="w",
        )

        self.error_label.grid(
            row=len(self.RESULT_KEYS),
            column=0,
            columnspan=2,
            padx=8,
            pady=(16, 8),
            sticky="ew",
        )

    # ======================================================
    # Parameter Collection
    # ======================================================

    def get_parameters(self) -> dict[str, str]:
        """
        Return current UI parameters.

        Values are returned as raw strings.
        Numeric conversion is performed by the
        valuation execution layer.
        """

        return {
            "symbol": self.symbol_entry.get().strip(),
            "spot": self.spot_entry.get().strip(),
            "strike": self.strike_entry.get().strip(),
            "market_price": (
                self.market_price_entry.get().strip()
            ),
            "days": self.days_entry.get().strip(),
            "volatility": (
                self.volatility_entry.get().strip()
            ),
            "rate": self.rate_entry.get().strip(),
            "direction": (
                self.direction_selector.get()
            ),
        }

    # ======================================================
    # Parameter Conversion
    # ======================================================

    @staticmethod
    def parse_parameters(
        parameters: dict[str, str],
    ) -> dict[str, object]:
        """
        Convert raw UI parameters into typed values.

        Raises
        ------
        ValueError
            If any parameter is invalid.
        """

        symbol = parameters.get(
            "symbol",
            "",
        ).strip()

        if not symbol:
            raise ValueError(
                "请输入合约代码。"
            )

        direction_value = parameters.get(
            "direction",
            "",
        ).strip().upper()

        if direction_value not in {
            "CALL",
            "PUT",
        }:
            raise ValueError(
                "期权方向必须为 CALL 或 PUT。"
            )

        try:
            spot = float(
                parameters["spot"]
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "标的价格必须是有效数字。"
            ) from exc

        try:
            strike = float(
                parameters["strike"]
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "行权价格必须是有效数字。"
            ) from exc

        try:
            market_price = float(
                parameters["market_price"]
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "市场价格必须是有效数字。"
            ) from exc

        try:
            days = int(
                parameters["days"]
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "剩余天数必须是整数。"
            ) from exc

        try:
            volatility = float(
                parameters["volatility"]
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "波动率必须是有效数字。"
            ) from exc

        rate_text = parameters.get(
            "rate",
            "",
        ).strip()

        if not rate_text:
            rate = 0.025
        else:
            try:
                rate = float(
                    rate_text
                )
            except ValueError as exc:

                raise ValueError(
                    "无风险利率必须是有效数字。"
                ) from exc

        if spot <= 0:
            raise ValueError(
                "标的价格必须大于 0。"
            )

        if strike <= 0:
            raise ValueError(
                "行权价格必须大于 0。"
            )

        if market_price < 0:
            raise ValueError(
                "市场价格不能小于 0。"
            )

        if days <= 0:
            raise ValueError(
                "剩余天数必须大于 0。"
            )

        if volatility <= 0:
            raise ValueError(
                "波动率必须大于 0。"
            )

        if rate < 0:
            raise ValueError(
                "无风险利率不能小于 0。"
            )

        return {
            "symbol": symbol,
            "direction": (
                OptionDirection(
                    direction_value
                )
            ),
            "spot": spot,
            "strike": strike,
            "market_price": market_price,
            "days": days,
            "volatility": volatility,
            "rate": rate,
        }

    # ======================================================
    # Contract Construction
    # ======================================================

    @staticmethod
    def build_contract(
        parameters: dict[str, object],
    ) -> OptionContract:
        """
        Build OptionContract from typed parameters.

        The UI does not own market-data fields such as
        volume and open interest yet, so they remain zero.
        """

        direction = parameters[
            "direction"
        ]

        if not isinstance(
            direction,
            OptionDirection,
        ):
            raise ValueError(
                "无效的期权方向。"
            )

        return OptionContract(
            symbol=str(
                parameters["symbol"]
            ),
            direction=direction,
            strike=float(
                parameters["strike"]
            ),
            price=float(
                parameters["market_price"]
            ),
            volume=0,
        )

    # ======================================================
    # Engine Execution
    # ======================================================

    def evaluate_parameters(
        self,
        parameters: dict[str, str],
    ) -> ValuationResult:
        """
        Execute valuation using current parameters.

        This method is UI-independent apart from the
        parameter dictionary and therefore provides a
        stable boundary between UI and core valuation.
        """

        typed_parameters = (
            self.parse_parameters(
                parameters
            )
        )

        contract = self.build_contract(
            typed_parameters
        )

        engine = ValuationEngine(
            risk_free_rate=float(
                typed_parameters["rate"]
            )
        )

        result = engine.evaluate(
            option=contract,
            underlying_price=float(
                typed_parameters["spot"]
            ),
            volatility=float(
                typed_parameters["volatility"]
            ),
            days=int(
                typed_parameters["days"]
            ),
        )

        return result

    # ======================================================
    # Valuation Action
    # ======================================================

    def on_valuate(self) -> None:
        """
        Execute valuation and update the result panel.
        """

        self.clear_error()

        try:

            parameters = self.get_parameters()

            result = self.evaluate_parameters(
                parameters
            )

        except ValueError as exc:

            self.last_result = None

            self.show_error(
                str(exc)
            )

            return

        except Exception as exc:

            self.last_result = None

            self.show_error(
                f"估值失败：{exc}"
            )

            return

        self.last_result = result

        self.display_result(
            result
        )

    # ======================================================
    # Result Display
    # ======================================================

    def display_result(
        self,
        result: ValuationResult,
    ) -> None:
        """Display a ValuationResult."""

        values = {
            "theoretical_price": (
                f"{result.theoretical_price:.6f}"
            ),
            "delta": (
                f"{result.delta:.6f}"
            ),
            "gamma": (
                f"{result.gamma:.6f}"
            ),
            "theta": (
                f"{result.theta:.6f}"
            ),
            "vega": (
                f"{result.vega:.6f}"
            ),
            "difference": (
                f"{result.difference:.6f}"
                if result.difference is not None
                else "--"
            ),
            "risk_score": (
                f"{result.risk_score:.6f}"
            ),
        }

        for key, value in values.items():

            self.result_labels[
                key
            ].configure(
                text=value
            )

    # ======================================================
    # Error Display
    # ======================================================

    def show_error(
        self,
        message: str,
    ) -> None:
        """Display an error message."""

        self.error_label.configure(
            text=message
        )

    def clear_error(self) -> None:
        """Clear the current error message."""

        self.error_label.configure(
            text=""
        )

    # ======================================================
    # Reset
    # ======================================================

    def reset_results(self) -> None:
        """Reset all valuation results."""

        self.last_result = None

        for label in self.result_labels.values():

            label.configure(
                text="--"
            )

        self.clear_error()


# ==========================================================
# Public Exports
# ==========================================================


__all__ = [
    "ValuationPage",
]