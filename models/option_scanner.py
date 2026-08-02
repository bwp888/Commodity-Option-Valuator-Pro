"""
Commodity Option Valuator Pro
=============================

Option Chain Scanner

Scan option chain data and select
top liquid contracts.

Default Strategy
----------------

CALL:
    top N by volume

PUT:
    top N by volume


Author : Simon
Version : 1.0.0
Python : 3.12
"""
from __future__ import annotations

from models.option import (
    Option,
    OptionType,
)

from models.black_scholes import (
    BlackScholes,
)

from models.greeks import (
    Greeks,
)

from models.implied_volatility import (
    ImpliedVolatility,
)

from models.taylor import (
    TaylorValuator,
)

from models.risk import (
    RiskAnalyzer,
)

from dataclasses import (
    dataclass,
)

from enum import Enum

from typing import (
    Any,
)



# ==========================================================
# Option Direction
# ==========================================================


class OptionDirection(Enum):
    """
    Option type.
    """

    CALL = "CALL"

    PUT = "PUT"



# ==========================================================
# Option Chain Contract
# ==========================================================


@dataclass(
    frozen=True
)
class OptionContract:
    """
    Single option chain record.

    Represents market data from
    DDE / Excel source.
    """


    symbol: str


    direction: OptionDirection


    strike: float


    price: float


    volume: int


    open_interest: int = 0


    bid: float = 0.0


    ask: float = 0.0



    def liquidity_score(
        self,
    ) -> float:
        """
        Simple liquidity score.

        Current version:
        based on volume.

        Future:
        add spread and OI.
        """

        return float(
            self.volume
        )



# ==========================================================
# Option Scanner
# ==========================================================


class OptionScanner:
    """
    Option chain scanner.

    Selects the most active
    CALL and PUT contracts.

    Parameters
    ----------
    contracts:
        Option chain list.

    top_n:
        Number of contracts
        selected for each direction.
    """


    DEFAULT_TOP_N: int = 5



    def __init__(
        self,
        contracts: list[OptionContract],
        top_n: int = DEFAULT_TOP_N,
    ) -> None:
        """
        Initialize scanner.

        Parameters
        ----------
        contracts:
            Option chain data.

        top_n:
            Selection count.
        """

        self.contracts = contracts

        self.top_n = top_n



    # ------------------------------------------------------
    # Basic Properties
    # ------------------------------------------------------


    @property
    def count(self) -> int:
        """
        Total contracts count.
        """

        return len(
            self.contracts
        )



    @property
    def calls(
        self,
    ) -> list[OptionContract]:
        """
        Return CALL contracts.
        """

        return [
            item
            for item in self.contracts
            if item.direction
            ==
            OptionDirection.CALL
        ]



    @property
    def puts(
        self,
    ) -> list[OptionContract]:
        """
        Return PUT contracts.
        """

        return [
            item
            for item in self.contracts
            if item.direction
            ==
            OptionDirection.PUT
        ]
    # ------------------------------------------------------
    # Sort By Volume
    # ------------------------------------------------------

    def sort_by_volume(
        self,
        contracts: list[OptionContract],
    ) -> list[OptionContract]:
        """
        Sort contracts by volume descending.

        Parameters
        ----------
        contracts:
            Option contract list.

        Returns
        -------
        list
            Sorted contracts.
        """

        return sorted(
            contracts,
            key=lambda x: x.volume,
            reverse=True,
        )



    # ------------------------------------------------------
    # Top CALL Contracts
    # ------------------------------------------------------

    def top_calls(
        self,
    ) -> list[OptionContract]:
        """
        Select top CALL contracts
        by trading volume.

        Returns
        -------
        list
            Top CALL options.
        """

        sorted_calls = (
            self.sort_by_volume(
                self.calls
            )
        )


        return sorted_calls[
            : self.top_n
        ]



    # ------------------------------------------------------
    # Top PUT Contracts
    # ------------------------------------------------------

    def top_puts(
        self,
    ) -> list[OptionContract]:
        """
        Select top PUT contracts
        by trading volume.

        Returns
        -------
        list
            Top PUT options.
        """

        sorted_puts = (
            self.sort_by_volume(
                self.puts
            )
        )


        return sorted_puts[
            : self.top_n
        ]



    # ------------------------------------------------------
    # Scan Top Volume
    # ------------------------------------------------------

    def scan_top_volume(
        self,
    ) -> dict[str, list[OptionContract]]:
        """
        Scan active option contracts.

        Strategy
        --------
        CALL:
            volume top N

        PUT:
            volume top N


        Returns
        -------
        dict
            Selected contracts.
        """

        return {

            "CALL": (
                self.top_calls()
            ),


            "PUT": (
                self.top_puts()
            ),
        }



    # ------------------------------------------------------
    # Selected Contracts
    # ------------------------------------------------------

    def selected(
        self,
    ) -> list[OptionContract]:
        """
        Return all selected contracts.

        Order:

        CALL Top N
        PUT Top N

        Returns
        -------
        list
        """

        result = (
            self.scan_top_volume()
        )


        return (
            result["CALL"]
            +
            result["PUT"]
        )
    # ------------------------------------------------------
    # Convert Contract To Option
    # ------------------------------------------------------

    def to_option(
        self,
        contract: OptionContract,
        maturity: float,
        rate: float,
        volatility: float,
        spot: float,
    ) -> Option:
        """
        Convert market contract into
        internal Option model.

        Parameters
        ----------
        contract:
            Option chain contract.

        maturity:
            Remaining time.

        rate:
            Risk free rate.

        volatility:
            Initial volatility.

        spot:
            Underlying price.

        Returns
        -------
        Option
        """

        option_type = (
            OptionType.CALL
            if contract.direction
            ==
            OptionDirection.CALL
            else
            OptionType.PUT
        )


        return Option(
            option_type=option_type,
            spot=spot,
            strike=contract.strike,
            maturity=maturity,
            rate=rate,
            volatility=volatility,
        )



    # ------------------------------------------------------
    # Analyze Single Contract
    # ------------------------------------------------------

    def analyze_contract(
        self,
        contract: OptionContract,
        maturity: float,
        rate: float,
        volatility: float,
        spot: float,
    ) -> dict[str, Any]:
        """
        Complete quantitative analysis
        for single option contract.

        Returns
        -------
        dict
            Analysis result.
        """

        option = self.to_option(
            contract,
            maturity,
            rate,
            volatility,
            spot,
        )


        bs = BlackScholes(
            option
        )


        greeks = Greeks(
            bs
        )


        iv_solver = ImpliedVolatility(
            option,
            contract.price,
        )


        taylor = TaylorValuator(
            greeks
        )


        risk = RiskAnalyzer(
            greeks,
            iv_solver,
            taylor,
        )


        return {

            "symbol":
                contract.symbol,


            "direction":
                contract.direction.value,


            "strike":
                contract.strike,


            "volume":
                contract.volume,


            "market_price":
                contract.price,


            "theoretical_price":
                bs.price,


            "implied_volatility":
                iv_solver.solve_cached(),


            "delta":
                greeks.delta,


            "gamma":
                greeks.gamma,


            "theta":
                greeks.theta,


            "vega":
                greeks.vega,


            "risk":
                risk.analyze(),
        }



    # ------------------------------------------------------
    # Analyze Selected Contracts
    # ------------------------------------------------------

    def analyze_selected(
        self,
        maturity: float,
        rate: float,
        volatility: float,
        spot: float,
    ) -> list[dict[str, Any]]:
        """
        Analyze selected TOP volume contracts.

        Default:

        CALL Top5
        +
        PUT Top5
        """

        contracts = (
            self.selected()
        )


        return [
            self.analyze_contract(
                contract,
                maturity,
                rate,
                volatility,
                spot,
            )

            for contract in contracts
        ]
    # ------------------------------------------------------
    # Summary
    # ------------------------------------------------------

    def summary(
        self,
    ) -> dict[str, Any]:
        """
        Return scanner summary.

        Returns
        -------
        dict
            Scanner information.
        """

        result = self.scan_top_volume()


        return {

            "total_contracts":
                self.count,


            "call_count":
                len(self.calls),


            "put_count":
                len(self.puts),


            "selected_count":
                len(self.selected()),


            "top_n":
                self.top_n,


            "selected":

                {
                    "CALL":
                        [
                            item.symbol
                            for item
                            in result["CALL"]
                        ],


                    "PUT":
                        [
                            item.symbol
                            for item
                            in result["PUT"]
                        ],
                },
        }



    # ------------------------------------------------------
    # Dictionary Export
    # ------------------------------------------------------

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Export scanner result.

        Returns
        -------
        dict
        """

        return self.summary()



    # ------------------------------------------------------
    # String Representation
    # ------------------------------------------------------

    def __str__(
        self,
    ) -> str:
        """
        Human-readable representation.
        """

        return (
            "OptionScanner("
            f"contracts={self.count}, "
            f"top_n={self.top_n}"
            ")"
        )



    # ------------------------------------------------------

    def __repr__(
        self,
    ) -> str:
        """
        Developer representation.
        """

        return (
            "OptionScanner("
            f"contracts={self.contracts!r}, "
            f"top_n={self.top_n}"
            ")"
        )



# ==========================================================
# Public Exports
# ==========================================================

__all__ = [
    "OptionDirection",
    "OptionContract",
    "OptionScanner",
]