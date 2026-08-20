"""
Commodity Option Valuator Pro
=============================

Option Valuation Workspace.

Commit 0027
------------

Connect the valuation UI with the SingleOptionValuator.

Architecture
------------

UI
 ↓
SingleOptionValuationInput
 ↓
SingleOptionValuator
 ↓
BlackScholes / Greeks / TaylorValuator

Compatibility
-------------

The following legacy UI-facing methods are intentionally preserved:

- parse_parameters()
- build_contract()
- evaluate_parameters()

They exist only to preserve the established UI/test boundary.

The UI valuation execution itself no longer uses ValuationEngine.
"""

from __future__ import annotations

import customtkinter as ctk

from core.single_option_valuation import (
    ReferenceVolatilityScenario,
    SingleOptionValuationInput,
    SingleOptionValuationResult,
    SingleOptionValuator,
)

from core.valuation_engine import (
    ValuationResult,
)

from models.option import (
    OptionDirection as CoreOptionDirection,
    OptionType,
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

    Responsibilities
    ----------------
    - Collect valuation parameters.
    - Validate user input.
    - Build SingleOptionValuationInput.
    - Execute SingleOptionValuator.
    - Display valuation result.

    Compatibility
    -------------
    Existing UI tests still expect:

        parse_parameters()
        build_contract()
        evaluate_parameters()

    Those methods are preserved as compatibility boundaries.

    Important
    ---------
    The actual valuation calculation is performed by
    SingleOptionValuator.
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

        # --------------------------------------------------
        # New valuation service
        # --------------------------------------------------

        self.valuator = SingleOptionValuator()

        self.last_result: (
            SingleOptionValuationResult | None
        ) = None

        self.create_header()

        self.create_workspace()

    # ======================================================
    # Valuator Access
    # ======================================================

    def get_valuator(self) -> SingleOptionValuator:
        """
        Return the SingleOptionValuator used by this page.

        Normally the valuator is created during __init__.

        A lazy fallback is intentionally provided because
        some established tests construct ValuationPage with:

            ValuationPage.__new__(ValuationPage)

        In that situation __init__ is not executed, so
        self.valuator does not yet exist.

        This method keeps that compatibility boundary while
        ensuring the actual calculation still uses
        SingleOptionValuator.
        """

        valuator = getattr(
            self,
            "valuator",
            None,
        )

        if not isinstance(
            valuator,
            SingleOptionValuator,
        ):
            valuator = SingleOptionValuator()

            self.valuator = valuator

        return valuator

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
            text="期权类型",
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

    def get_parameters(
        self,
    ) -> dict[str, str]:
        """
        Return current UI parameters.

        Values remain raw strings.

        Numeric conversion is performed by
        parse_parameters().
        """

        return {
            "symbol": (
                self.symbol_entry
                .get()
                .strip()
            ),
            "spot": (
                self.spot_entry
                .get()
                .strip()
            ),
            "strike": (
                self.strike_entry
                .get()
                .strip()
            ),
            "market_price": (
                self.market_price_entry
                .get()
                .strip()
            ),
            "days": (
                self.days_entry
                .get()
                .strip()
            ),
            "volatility": (
                self.volatility_entry
                .get()
                .strip()
            ),
            "rate": (
                self.rate_entry
                .get()
                .strip()
            ),
            "direction": (
                self.direction_selector
                .get()
                .strip()
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

        Compatibility
        -------------

        The established UI contract uses:

            direction = CALL / PUT

        They represent the option type in the current
        single-option valuation UI.

        SingleOptionValuator itself separates:

            OptionType = CALL / PUT
            OptionDirection = LONG / SHORT

        The adapter is created later by
        build_single_option_input().
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

        # --------------------------------------------------
        # Validation order intentionally preserved.
        #
        # Existing tests depend on these validation results.
        # --------------------------------------------------

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
            "direction": OptionDirection(
                direction_value
            ),
            "spot": spot,
            "strike": strike,
            "market_price": market_price,
            "days": days,
            "volatility": volatility,
            "rate": rate,
        }

    # ======================================================
    # Legacy Contract Compatibility
    # ======================================================

    @staticmethod
    def build_contract(
        parameters: dict[str, object],
    ) -> OptionContract:
        """
        Build the legacy OptionContract.

        This method is retained for compatibility with the
        existing UI/test boundary.

        It is NOT used by the new SingleOptionValuator
        execution path.
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
    # SingleOption Input Adapter
    # ======================================================

    @staticmethod
    def build_single_option_input(
        parameters: dict[str, object],
    ) -> SingleOptionValuationInput:
        """
        Convert typed UI parameters into
        SingleOptionValuationInput.

        The current UI keeps the established CALL / PUT
        selector.

        Therefore:

            CALL
                ↓
            OptionType.CALL

            PUT
                ↓
            OptionType.PUT

        Position direction remains LONG internally because
        the current valuation page does not expose a separate
        LONG / SHORT selector yet.
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

        if direction == OptionDirection.CALL:

            option_type = OptionType.CALL

        elif direction == OptionDirection.PUT:

            option_type = OptionType.PUT

        else:

            raise ValueError(
                "期权类型必须为 CALL 或 PUT。"
            )

        current_volatility = float(
            parameters["volatility"]
        )

        # --------------------------------------------------
        # Current-state compatibility scenario
        # --------------------------------------------------
        #
        # The present UI does not yet expose separate:
        #
        # - target futures price
        # - target/reference volatility
        #
        # Therefore the current valuation is represented as
        # a neutral scenario:
        #
        # target futures price
        #     = current futures price
        #
        # target volatility
        #     = current volatility
        #
        # This preserves the existing UI semantics while the
        # new core architecture is already in place.
        #

        reference_volatility = (
            ReferenceVolatilityScenario(
                current=current_volatility,
                target=current_volatility,
            )
        )

        return SingleOptionValuationInput(
            symbol=str(
                parameters["symbol"]
            ),
            option_type=option_type,
            current_futures_price=float(
                parameters["spot"]
            ),
            strike=float(
                parameters["strike"]
            ),
            current_option_price=float(
                parameters["market_price"]
            ),
            current_option_iv=current_volatility,
            remaining_days=int(
                parameters["days"]
            ),
            target_futures_price=float(
                parameters["spot"]
            ),
            reference_volatility=(
                reference_volatility
            ),
            risk_free_rate=float(
                parameters["rate"]
            ),
            direction=CoreOptionDirection.LONG,
        )

    # ======================================================
    # Single Option Evaluation
    # ======================================================

    def evaluate_single_option(
        self,
        parameters: dict[str, str],
    ) -> SingleOptionValuationResult:
        """
        Execute the new single-option valuation path.

        This is the actual calculation entry point.

        ValuationEngine is intentionally not used here.

        The valuator is obtained through get_valuator()
        instead of directly accessing self.valuator so that
        the established __new__()-based tests remain valid.
        """

        typed_parameters = (
            self.parse_parameters(
                parameters
            )
        )

        inputs = (
            self.build_single_option_input(
                typed_parameters
            )
        )

        valuator = self.get_valuator()

        return valuator.evaluate(
            inputs
        )

    # ======================================================
    # Compatibility Result Adapter
    # ======================================================

    @staticmethod
    def single_result_to_legacy_result(
        result: SingleOptionValuationResult,
        direction: OptionDirection,
    ) -> ValuationResult:
        """
        Adapt SingleOptionValuationResult to the established
        ValuationResult interface.

        This adapter exists only for the current test/UI
        compatibility boundary.

        The calculation itself has already been performed by
        SingleOptionValuator.
        """

        difference = (
            result.current_theoretical_price
            - result.current_option_price
        )

        risk_score = abs(
            difference
        )

        return ValuationResult(
            symbol=result.symbol,
            direction=direction,
            premium=float(
                result.current_option_price
            ),
            theoretical_price=float(
                result.current_theoretical_price
            ),
            delta=float(
                result.current_delta
            ),
            gamma=float(
                result.current_gamma
            ),
            theta=float(
                result.current_theta
            ),
            vega=0.0,
            difference=float(
                difference
            ),
            risk_score=float(
                risk_score
            ),
        )

    # ======================================================
    # Compatibility Evaluation API
    # ======================================================

    def evaluate_parameters(
        self,
        parameters: dict[str, str],
    ) -> ValuationResult:
        """
        Execute valuation through SingleOptionValuator.

        Compatibility
        -------------

        The method still returns ValuationResult because
        existing tests and older UI boundaries depend on it.

        Internally:

            parameters
                ↓
            SingleOptionValuationInput
                ↓
            SingleOptionValuator
                ↓
            SingleOptionValuationResult
                ↓
            compatibility adapter
                ↓
            ValuationResult
        """

        typed_parameters = (
            self.parse_parameters(
                parameters
            )
        )

        single_result = (
            self.evaluate_single_option(
                parameters
            )
        )

        direction = typed_parameters[
            "direction"
        ]

        if not isinstance(
            direction,
            OptionDirection,
        ):
            raise ValueError(
                "无效的期权方向。"
            )

        return (
            self.single_result_to_legacy_result(
                single_result,
                direction,
            )
        )

    # ======================================================
    # Valuation Action
    # ======================================================

    def on_valuate(self) -> None:
        """
        Execute valuation and update the result panel.
        """

        self.clear_error()

        try:

            parameters = (
                self.get_parameters()
            )

            result = (
                self.evaluate_single_option(
                    parameters
                )
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

        self.display_single_result(
            result
        )

    # ======================================================
    # Result Display
    # ======================================================

    def display_single_result(
        self,
        result: SingleOptionValuationResult,
    ) -> None:
        """
        Display SingleOptionValuationResult.
        """

        difference = (
            result.current_theoretical_price
            - result.current_option_price
        )

        values = {
            "theoretical_price": (
                f"{result.current_theoretical_price:.6f}"
            ),
            "delta": (
                f"{result.current_delta:.6f}"
            ),
            "gamma": (
                f"{result.current_gamma:.6f}"
            ),
            "theta": (
                f"{result.current_theta:.6f}"
            ),
            "vega": "--",
            "difference": (
                f"{difference:.6f}"
            ),
            "risk_score": (
                f"{abs(difference):.6f}"
            ),
        }

        for key, value in values.items():

            self.result_labels[
                key
            ].configure(
                text=value
            )

    # ======================================================
    # Legacy Result Display
    # ======================================================

    def display_result(
        self,
        result: ValuationResult,
    ) -> None:
        """
        Display legacy ValuationResult.

        Retained for compatibility with existing callers.
        """

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

        for label in (
            self.result_labels.values()
        ):

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