"""
Commodity Option Valuator Pro
=============================

Single Option Valuation and Scenario Analysis.

Commit 0026
------------

Provides the core calculation workflow for evaluating
one selected commodity option under a target futures
price and a reference-volatility scenario.

Phase 2-A Extension
-------------------

The valuation result is additionally passed through the
existing ComprehensiveEvaluator.

Architecture
------------

Selected Option
    ↓
Current Market State
    ↓
Current Greeks
    ↓
Reference Volatility Scenario
    ↓
Target Option IV
    ↓
Target Futures Price
    ↓
Existing Black-Scholes Engine
    ↓
Target Theoretical Option Price
    ↓
Target Greeks
    ↓
Taylor Comparison
    ↓
SingleOptionValuationResult
    ↓
ComprehensiveEvaluator
    ↓
ComprehensiveEvaluationResult

Important
---------
This module is an orchestration layer.

It deliberately reuses the existing:

- Option
- BlackScholes
- Greeks
- TaylorValuator
- ComprehensiveEvaluator

It does not modify those existing models.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from core.comprehensive_evaluation import (
    ComprehensiveEvaluationResult,
    ComprehensiveEvaluator,
)

from models.black_scholes import BlackScholes
from models.greeks import Greeks
from models.option import (
    Option,
    OptionDirection,
    OptionType,
)
from models.taylor import TaylorValuator


# ==========================================================
# Reference Volatility Scenario
# ==========================================================


@dataclass(frozen=True)
class ReferenceVolatilityScenario:
    """
    Reference-volatility scenario.

    The reference volatility is NOT the selected option's IV.

    Example
    -------
    Reference volatility:

        26.70 → 29.55

    Relative change:

        (29.55 / 26.70) - 1
        ≈ 10.67%

    If the selected option IV is 19.54%, the target
    option IV becomes:

        19.54% × (1 + 10.67%)
    """

    current: float
    target: float

    def validate(self) -> None:
        """Validate reference volatility values."""

        if self.current <= 0:
            raise ValueError(
                "reference_volatility_current must be greater than zero."
            )

        if self.target <= 0:
            raise ValueError(
                "reference_volatility_target must be greater than zero."
            )

    @property
    def relative_change(self) -> float:
        """
        Return relative volatility change.

        Example
        -------
        26.70 → 29.55

        Returns approximately:

            0.106741...
        """

        self.validate()

        return (
            self.target / self.current
        ) - 1.0

    @property
    def relative_change_percent(self) -> float:
        """
        Return relative volatility change as percentage.

        Example
        -------
        26.70 → 29.55

        Returns approximately:

            10.67
        """

        return (
            self.relative_change
            * 100.0
        )

    def adjust_option_iv(
        self,
        current_option_iv: float,
    ) -> float:
        """
        Adjust the selected option's IV according to
        the reference-volatility change.

        The selected option IV itself is not used as
        the reference index.

        Formula
        -------

        target_option_iv =
            current_option_iv
            ×
            (1 + reference_relative_change)
        """

        if current_option_iv <= 0:
            raise ValueError(
                "current_option_iv must be greater than zero."
            )

        return (
            current_option_iv
            * (
                1.0
                + self.relative_change
            )
        )


# ==========================================================
# Single Option Valuation Input
# ==========================================================


@dataclass(frozen=True)
class SingleOptionValuationInput:
    """
    Input parameters for one selected option.

    Parameters
    ----------
    symbol:
        Option contract symbol.

    option_type:
        CALL / PUT.

    current_futures_price:
        Current underlying futures price.

    strike:
        Option strike price.

    current_option_price:
        Current market price of the selected option.

    current_option_iv:
        Current IV of the selected option.

    remaining_days:
        Remaining calendar days.

    target_futures_price:
        Futures price under the target scenario.

    reference_volatility:
        Reference volatility scenario.

    risk_free_rate:
        Internal model risk-free rate.

        This is deliberately not exposed as a user-facing
        input in the future UI.

    direction:
        LONG / SHORT.

    Notes
    -----
    Volatility values are represented as decimal values.

    Examples
    --------
    19.54% -> 0.1954
    26.70% -> 0.2670

    If the future UI accepts percentages directly,
    the UI layer should perform the conversion.
    """

    symbol: str
    option_type: OptionType | str

    current_futures_price: float
    strike: float

    current_option_price: float
    current_option_iv: float

    remaining_days: int

    target_futures_price: float

    reference_volatility: ReferenceVolatilityScenario

    risk_free_rate: float = 0.025

    direction: OptionDirection | str = (
        OptionDirection.LONG
    )

    def validate(self) -> None:
        """Validate all valuation inputs."""

        if not self.symbol:
            raise ValueError(
                "symbol cannot be empty."
            )

        if self.current_futures_price <= 0:
            raise ValueError(
                "current_futures_price must be greater than zero."
            )

        if self.strike <= 0:
            raise ValueError(
                "strike must be greater than zero."
            )

        if self.current_option_price < 0:
            raise ValueError(
                "current_option_price cannot be negative."
            )

        if self.current_option_iv <= 0:
            raise ValueError(
                "current_option_iv must be greater than zero."
            )

        if self.remaining_days <= 0:
            raise ValueError(
                "remaining_days must be greater than zero."
            )

        if self.target_futures_price <= 0:
            raise ValueError(
                "target_futures_price must be greater than zero."
            )

        if self.risk_free_rate < 0:
            raise ValueError(
                "risk_free_rate cannot be negative."
            )

        self.reference_volatility.validate()


# ==========================================================
# Valuation Result
# ==========================================================


@dataclass(frozen=True)
class SingleOptionValuationResult:
    """
    Complete result of one-option valuation.

    The result contains:

    - Current market information
    - Current theoretical price
    - Current Greeks
    - Reference volatility change
    - Target option IV
    - Target theoretical price
    - Target Greeks
    - Taylor comparison
    - Comprehensive evaluation

    ``comprehensive_evaluation`` is optional at the
    dataclass level for backward compatibility.

    ``SingleOptionValuator.evaluate()`` always populates
    it for newly evaluated options.
    """

    symbol: str

    current_futures_price: float
    target_futures_price: float
    strike: float

    current_option_price: float

    current_option_iv: float
    target_option_iv: float

    reference_volatility_current: float
    reference_volatility_target: float
    reference_volatility_change_percent: float

    current_theoretical_price: float
    target_theoretical_price: float

    current_delta: float
    current_gamma: float
    current_theta: float

    target_delta: float
    target_gamma: float
    target_theta: float

    taylor_first_order_price: float
    taylor_second_order_price: float

    comprehensive_evaluation: (
        ComprehensiveEvaluationResult | None
    ) = None

    @property
    def theoretical_price_change(self) -> float:
        """Return target theoretical price minus current theoretical price."""

        return (
            self.target_theoretical_price
            - self.current_theoretical_price
        )

    @property
    def theoretical_price_change_percent(self) -> float:
        """
        Return theoretical price change percentage.
        """

        if self.current_theoretical_price == 0:
            return 0.0

        return (
            self.theoretical_price_change
            / self.current_theoretical_price
            * 100.0
        )

    @property
    def market_price_gap(self) -> float:
        """
        Return current market price minus current theoretical price.
        """

        return (
            self.current_option_price
            - self.current_theoretical_price
        )

    @property
    def target_vs_current_market_change(self) -> float:
        """
        Return target theoretical price minus current market price.
        """

        return (
            self.target_theoretical_price
            - self.current_option_price
        )

    @property
    def target_vs_current_market_change_percent(self) -> float:
        """
        Return target theoretical price change relative
        to current market price.
        """

        if self.current_option_price == 0:
            return 0.0

        return (
            self.target_vs_current_market_change
            / self.current_option_price
            * 100.0
        )

    def to_dict(
        self,
    ) -> dict[str, object]:
        """Return result as a dictionary."""

        result: dict[str, object] = {
            "symbol": self.symbol,
            "current_futures_price": (
                self.current_futures_price
            ),
            "target_futures_price": (
                self.target_futures_price
            ),
            "strike": self.strike,
            "current_option_price": (
                self.current_option_price
            ),
            "current_option_iv": (
                self.current_option_iv
            ),
            "target_option_iv": (
                self.target_option_iv
            ),
            "reference_volatility_current": (
                self.reference_volatility_current
            ),
            "reference_volatility_target": (
                self.reference_volatility_target
            ),
            "reference_volatility_change_percent": (
                self.reference_volatility_change_percent
            ),
            "current_theoretical_price": (
                self.current_theoretical_price
            ),
            "target_theoretical_price": (
                self.target_theoretical_price
            ),
            "current_delta": self.current_delta,
            "current_gamma": self.current_gamma,
            "current_theta": self.current_theta,
            "target_delta": self.target_delta,
            "target_gamma": self.target_gamma,
            "target_theta": self.target_theta,
            "taylor_first_order_price": (
                self.taylor_first_order_price
            ),
            "taylor_second_order_price": (
                self.taylor_second_order_price
            ),
            "theoretical_price_change": (
                self.theoretical_price_change
            ),
            "theoretical_price_change_percent": (
                self.theoretical_price_change_percent
            ),
            "market_price_gap": self.market_price_gap,
            "target_vs_current_market_change": (
                self.target_vs_current_market_change
            ),
            "target_vs_current_market_change_percent": (
                self.target_vs_current_market_change_percent
            ),
        }

        if self.comprehensive_evaluation is not None:
            result[
                "comprehensive_evaluation"
            ] = self.comprehensive_evaluation.to_dict()

        return result


# ==========================================================
# Single Option Valuator
# ==========================================================


class SingleOptionValuator:
    """
    Single-option valuation orchestration service.

    This class does not implement pricing formulas itself.

    It coordinates the existing:

        Option
        ↓
        BlackScholes
        ↓
        Greeks
        ↓
        TaylorValuator
        ↓
        ComprehensiveEvaluator
    """

    DAYS_PER_YEAR = 365

    def __init__(
        self,
        comprehensive_evaluator: ComprehensiveEvaluator | None = None,
    ) -> None:
        """
        Initialize single-option valuator.

        Parameters
        ----------
        comprehensive_evaluator:
            Optional existing comprehensive evaluator.

            If omitted, a default ComprehensiveEvaluator
            is created.

        Notes
        -----
        Dependency injection is used here so that tests
        and future workflow layers can provide a controlled
        evaluator without changing the valuation logic.
        """

        self.comprehensive_evaluator = (
            comprehensive_evaluator
            if comprehensive_evaluator is not None
            else ComprehensiveEvaluator()
        )

    def evaluate(
        self,
        inputs: SingleOptionValuationInput,
    ) -> SingleOptionValuationResult:
        """
        Evaluate one selected option.

        Parameters
        ----------
        inputs:
            Single-option valuation inputs.

        Returns
        -------
        SingleOptionValuationResult
            Complete current/target valuation result
            including comprehensive evaluation.
        """

        inputs.validate()

        maturity = (
            inputs.remaining_days
            / self.DAYS_PER_YEAR
        )

        option_type = self._parse_option_type(
            inputs.option_type
        )

        direction = self._parse_direction(
            inputs.direction
        )

        # --------------------------------------------------
        # Current State
        # --------------------------------------------------

        current_option = Option(
            symbol=inputs.symbol,
            option_type=option_type,
            direction=direction,
            spot=inputs.current_futures_price,
            strike=inputs.strike,
            maturity=maturity,
            rate=inputs.risk_free_rate,
            volatility=inputs.current_option_iv,
        )

        current_bs = BlackScholes(
            current_option
        )

        current_greeks = Greeks(
            current_bs
        )

        # --------------------------------------------------
        # Target IV
        # --------------------------------------------------

        target_option_iv = (
            inputs.reference_volatility.adjust_option_iv(
                inputs.current_option_iv
            )
        )

        # --------------------------------------------------
        # Target State
        # --------------------------------------------------

        target_option = Option(
            symbol=inputs.symbol,
            option_type=option_type,
            direction=direction,
            spot=inputs.target_futures_price,
            strike=inputs.strike,
            maturity=maturity,
            rate=inputs.risk_free_rate,
            volatility=target_option_iv,
        )

        target_bs = BlackScholes(
            target_option
        )

        target_greeks = Greeks(
            target_bs
        )

        # --------------------------------------------------
        # Taylor Comparison
        # --------------------------------------------------

        taylor = TaylorValuator(
            current_greeks
        )

        taylor_first_order = (
            taylor.first_order(
                inputs.target_futures_price
            )
        )

        taylor_second_order = (
            taylor.second_order(
                inputs.target_futures_price
            )
        )

        # --------------------------------------------------
        # Base Result
        # --------------------------------------------------

        base_result = SingleOptionValuationResult(
            symbol=inputs.symbol,
            current_futures_price=(
                inputs.current_futures_price
            ),
            target_futures_price=(
                inputs.target_futures_price
            ),
            strike=inputs.strike,
            current_option_price=(
                inputs.current_option_price
            ),
            current_option_iv=(
                inputs.current_option_iv
            ),
            target_option_iv=target_option_iv,
            reference_volatility_current=(
                inputs.reference_volatility.current
            ),
            reference_volatility_target=(
                inputs.reference_volatility.target
            ),
            reference_volatility_change_percent=(
                inputs.reference_volatility.relative_change_percent
            ),
            current_theoretical_price=(
                current_bs.price
            ),
            target_theoretical_price=(
                target_bs.price
            ),
            current_delta=current_greeks.delta,
            current_gamma=current_greeks.gamma,
            current_theta=current_greeks.theta,
            target_delta=target_greeks.delta,
            target_gamma=target_greeks.gamma,
            target_theta=target_greeks.theta,
            taylor_first_order_price=(
                taylor_first_order
            ),
            taylor_second_order_price=(
                taylor_second_order
            ),
        )

        # --------------------------------------------------
        # Comprehensive Evaluation
        # --------------------------------------------------

        comprehensive_evaluation = (
            self.comprehensive_evaluator.evaluate(
                base_result
            )
        )

        # --------------------------------------------------
        # Final Result
        # --------------------------------------------------

        return replace(
            base_result,
            comprehensive_evaluation=(
                comprehensive_evaluation
            ),
        )

    # ======================================================
    # Parsers
    # ======================================================

    @staticmethod
    def _parse_option_type(
        value: OptionType | str,
    ) -> OptionType:
        """Normalize option type."""

        if isinstance(
            value,
            OptionType,
        ):
            return value

        try:
            return OptionType(
                str(value).upper()
            )
        except ValueError as exc:
            raise ValueError(
                "option_type must be CALL or PUT."
            ) from exc

    @staticmethod
    def _parse_direction(
        value: OptionDirection | str,
    ) -> OptionDirection:
        """Normalize option direction."""

        if isinstance(
            value,
            OptionDirection,
        ):
            return value

        try:
            return OptionDirection(
                str(value).upper()
            )
        except ValueError as exc:
            raise ValueError(
                "direction must be LONG or SHORT."
            ) from exc


__all__ = [
    "ReferenceVolatilityScenario",
    "SingleOptionValuationInput",
    "SingleOptionValuationResult",
    "SingleOptionValuator",
]