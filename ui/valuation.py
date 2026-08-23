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

UI Design
---------

Current futures price:
    Can come from TDX or manual input.

Current option price:
    Can come from TDX or manual input.

Current option IV:
    Can come from TDX when available,
    otherwise manual input remains supported.

Remaining days:
    Required valuation parameter.
    It is NOT a scenario parameter.

Target futures price:
    User scenario input.

Risk-free rate:
    Internal model parameter.
    It is deliberately NOT exposed in the UI.

Bid / Ask:
    Not used by the single-option valuation UI.

Compatibility
-------------

The following legacy UI-facing methods are intentionally preserved:

- parse_parameters()
- build_contract()
- evaluate_parameters()

They exist to preserve the established UI/test boundary.

The actual valuation calculation is performed by
SingleOptionValuator.
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
    Single-option valuation workspace.

    The UI is deliberately kept as an orchestration layer.

    It collects parameters, validates them, creates
    SingleOptionValuationInput and delegates calculation to
    SingleOptionValuator.

    The UI does not implement pricing formulas.
    """

    # ------------------------------------------------------
    # IMPORTANT
    # ------------------------------------------------------
    #
    # These keys are part of the established UI/test boundary.
    #
    # Do NOT casually change this list.
    #
    # The new SingleOptionValuationResult contains considerably
    # more information, but the compatibility UI continues to
    # expose the established seven result fields.
    #
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

    # Internal model parameter.
    #
    # This value is intentionally not displayed in the UI.
    DEFAULT_RISK_FREE_RATE = 0.025

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
        # Valuation service
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

    def get_valuator(
        self,
    ) -> SingleOptionValuator:
        """
        Return the SingleOptionValuator used by this page.

        A lazy fallback is intentionally retained because
        established tests construct the page with:

            ValuationPage.__new__(ValuationPage)

        In that case __init__ is not executed.
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
                "输入期权合约与用户情景，"
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
        """
        Create input section.

        The section is split conceptually into:

        1. 当前市场参数
        2. 用户情景

        Target futures price belongs to the scenario area.

        Remaining days belongs to the valuation contract
        parameters and is NOT treated as a scenario parameter.
        """

        self.parameter_section = SectionCard(
            self.workspace,
            title="估值参数",
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

        # --------------------------------------------------
        # Current market / contract parameters
        # --------------------------------------------------

        self.create_parameter_label(
            row=0,
            text="合约代码",
        )

        self.symbol_entry = self.create_entry(
            row=0,
            placeholder="例如 A2609-C-3400",
        )

        self.create_parameter_label(
            row=1,
            text="当前期货价格",
        )

        self.spot_entry = self.create_entry(
            row=1,
            placeholder="可手动输入，例如 3400",
        )

        self.create_parameter_label(
            row=2,
            text="行权价格",
        )

        self.strike_entry = self.create_entry(
            row=2,
            placeholder="例如 3400",
        )

        self.create_parameter_label(
            row=3,
            text="期权市场价格",
        )

        self.market_price_entry = self.create_entry(
            row=3,
            placeholder="例如 144.5",
        )

        self.create_parameter_label(
            row=4,
            text="剩余天数",
        )

        self.days_entry = self.create_entry(
            row=4,
            placeholder="手动输入，例如 30",
        )

        self.create_parameter_label(
            row=5,
            text="当前隐含波动率",
        )

        self.volatility_entry = self.create_entry(
            row=5,
            placeholder="例如 0.20",
        )

        self.create_parameter_label(
            row=6,
            text="期权类型",
        )

        self.direction_selector = (
            ctk.CTkSegmentedButton(
                self.parameter_section.content,
                values=[
                    "CALL",
                    "PUT",
                ],
            )
        )

        self.direction_selector.set(
            "CALL"
        )

        self.direction_selector.grid(
            row=6,
            column=1,
            padx=(8, 0),
            pady=6,
            sticky="ew",
        )

        # --------------------------------------------------
        # User scenario
        # --------------------------------------------------

        self.scenario_label = ctk.CTkLabel(
            self.parameter_section.content,
            text="用户情景",
            text_color=COLOR_TEXT,
            font=(
                FONT_FAMILY,
                FONT_SUBTITLE_SIZE,
                "bold",
            ),
            anchor="w",
        )

        self.scenario_label.grid(
            row=7,
            column=0,
            columnspan=2,
            padx=8,
            pady=(18, 8),
            sticky="w",
        )

        self.create_parameter_label(
            row=8,
            text="目标期货价格",
        )

        self.target_futures_price_entry = (
            self.create_entry(
                row=8,
                placeholder="用户手动输入，例如 3600",
            )
        )

        # --------------------------------------------------
        # Action
        # --------------------------------------------------

        self.valuate_button = PrimaryButton(
            self.parameter_section.content,
            text="开始估值",
            command=self.on_valuate,
        )

        self.valuate_button.grid(
            row=9,
            column=0,
            columnspan=2,
            padx=8,
            pady=(18, 8),
            sticky="ew",
        )

        self.parameter_hint = ctk.CTkLabel(
            self.parameter_section.content,
            text=(
                "当前期货价格、期权价格和隐含波动率"
                "支持手动输入；"
                "\n"
                "后续可由通达信数据自动填充。"
                "\n"
                "目标期货价格始终由用户输入，"
                "用于用户情景分析。"
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
            row=10,
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
        Return current UI parameters as raw strings.

        Risk-free rate is intentionally absent from the UI.
        The internal valuation layer uses the established
        default rate of 0.025.

        Target futures price is explicitly collected from
        the user scenario input.
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
            "target_futures_price": (
                self.target_futures_price_entry
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

        Existing tests use the established parameter set
        without target_futures_price.

        Therefore target_futures_price is optional at this
        compatibility boundary.

        If it is omitted or blank:

            target_futures_price = spot

        This keeps all existing tests and callers valid while
        allowing the new UI to provide a real user scenario.

        Risk-free rate is also retained as an optional legacy
        parameter, but the actual UI no longer displays it.
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

        # --------------------------------------------------
        # Current futures price
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Strike
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Current option market price
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Remaining days
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Current option IV
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Target futures price
        # --------------------------------------------------
        #
        # New UI:
        #
        #     user enters target_futures_price
        #
        # Legacy callers/tests:
        #
        #     field may not exist
        #
        # Compatibility rule:
        #
        #     omitted / blank -> current futures price
        #

        target_text = parameters.get(
            "target_futures_price",
            "",
        ).strip()

        if not target_text:

            target_futures_price = spot

        else:

            try:
                target_futures_price = float(
                    target_text
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                raise ValueError(
                    "目标期货价格必须是有效数字。"
                ) from exc

        # --------------------------------------------------
        # Legacy rate compatibility
        # --------------------------------------------------
        #
        # UI no longer exposes rate.
        #
        # Existing callers may still provide it.
        #

        rate_text = parameters.get(
            "rate",
            "",
        ).strip()

        if not rate_text:

            rate = (
                ValuationPage.DEFAULT_RISK_FREE_RATE
            )

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

        if target_futures_price <= 0:

            raise ValueError(
                "目标期货价格必须大于 0。"
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
            "target_futures_price": (
                target_futures_price
            ),
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

        Retained for established UI/test compatibility.

        It is NOT used by the new valuation execution path.
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

        CALL / PUT from the established UI are mapped to
        OptionType.CALL / OptionType.PUT.

        Position direction remains LONG because the current
        single-option valuation UI does not expose a separate
        LONG / SHORT selector.
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

        current_volatility_percent = float(
            parameters["volatility"]
        )

        current_volatility = (
            current_volatility_percent / 100.0
        )

        # --------------------------------------------------
        # Reference volatility
        # --------------------------------------------------
        #
        # At the current stage there is no separate
        # reference-volatility input in the UI.
        #
        # Therefore:
        #
        #     current reference volatility
        #         = current option IV
        #
        #     target reference volatility
        #         = current option IV
        #
        # This creates a neutral volatility scenario.
        #
        # The core architecture remains ready for a future
        # TDX/reference-volatility source without changing
        # SingleOptionValuator.
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
                parameters[
                    "target_futures_price"
                ]
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
        Execute the SingleOptionValuator workflow.
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

        The calculation itself has already been performed by
        SingleOptionValuator.
        """

        difference = (
            result.target_theoretical_price
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
                result.target_theoretical_price
            ),
            delta=float(
                result.target_delta
            ),
            gamma=float(
                result.target_gamma
            ),
            theta=float(
                result.target_theta
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

        This method remains because the existing UI/test
        boundary expects ValuationResult.
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
        """Execute valuation and update result panel."""

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
        Display target-scenario valuation results.

        The seven established UI result slots are retained.

        The displayed theoretical price / Greeks correspond
        to the target futures-price scenario.
        """

        difference = (
            result.target_theoretical_price
            - result.current_option_price
        )

        values = {
            "theoretical_price": (
                f"{result.target_theoretical_price:.6f}"
            ),
            "delta": (
                f"{result.target_delta:.6f}"
            ),
            "gamma": (
                f"{result.target_gamma:.6f}"
            ),
            "theta": (
                f"{result.target_theta:.6f}"
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

        Retained for compatibility with established callers.
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