# Commodity Option Valuator Pro
# =============================
# Option Scanner Tests
# Author : Simon
# Version : 0.1.0

from __future__ import annotations


import pytest


from models.option_scanner import (
    OptionContract,
    OptionDirection,
    OptionScanner,
)



# ==========================================================
# Helper
# ==========================================================


def create_contracts():

    contracts = []


    # CALL contracts

    for i, volume in enumerate(
        [1000, 5000, 3000, 9000, 7000, 2000]
    ):

        contracts.append(

            OptionContract(

                symbol=f"CALL-{i}",

                direction=(
                    OptionDirection.CALL
                ),

                strike=70000+i*100,

                price=500+i*10,

                volume=volume,

                open_interest=10000,

                bid=490,

                ask=510,
            )
        )



    # PUT contracts

    for i, volume in enumerate(
        [8000, 2000, 6000, 10000, 4000, 3000]
    ):

        contracts.append(

            OptionContract(

                symbol=f"PUT-{i}",

                direction=(
                    OptionDirection.PUT
                ),

                strike=70000+i*100,

                price=400+i*10,

                volume=volume,

                open_interest=8000,

                bid=390,

                ask=410,
            )
        )


    return contracts



# ==========================================================
# Contract Tests
# ==========================================================


def test_contract_create():

    contract = OptionContract(

        symbol="TEST",

        direction=OptionDirection.CALL,

        strike=70000,

        price=500,

        volume=1000,
    )


    assert contract.symbol == "TEST"

    assert contract.volume == 1000



def test_liquidity_score():

    contract = OptionContract(

        symbol="TEST",

        direction=OptionDirection.CALL,

        strike=70000,

        price=500,

        volume=1234,
    )


    assert (
        contract.liquidity_score()
        ==
        1234
    )



# ==========================================================
# Scanner Basic
# ==========================================================


def test_scanner_count():

    scanner = OptionScanner(
        create_contracts()
    )


    assert (
        scanner.count
        ==
        12
    )



def test_call_filter():

    scanner = OptionScanner(
        create_contracts()
    )


    assert (
        len(scanner.calls)
        ==
        6
    )



def test_put_filter():

    scanner = OptionScanner(
        create_contracts()
    )


    assert (
        len(scanner.puts)
        ==
        6
    )



# ==========================================================
# Volume Ranking
# ==========================================================


def test_sort_volume():

    scanner = OptionScanner(
        create_contracts()
    )


    result = scanner.sort_by_volume(
        scanner.calls
    )


    assert (
        result[0].volume
        ==
        9000
    )



def test_top_calls_default():

    scanner = OptionScanner(
        create_contracts()
    )


    result = scanner.top_calls()


    assert len(result) == 5


    assert (
        result[0].symbol
        ==
        "CALL-3"
    )



def test_top_puts_default():

    scanner = OptionScanner(
        create_contracts()
    )


    result = scanner.top_puts()


    assert len(result) == 5


    assert (
        result[0].symbol
        ==
        "PUT-3"
    )



# ==========================================================
# top_n
# ==========================================================


def test_custom_top_n():

    scanner = OptionScanner(

        create_contracts(),

        top_n=2,
    )


    assert (
        len(scanner.top_calls())
        ==
        2
    )


    assert (
        len(scanner.top_puts())
        ==
        2
    )



# ==========================================================
# Scan Result
# ==========================================================


def test_scan_top_volume():

    scanner = OptionScanner(
        create_contracts()
    )


    result = (
        scanner.scan_top_volume()
    )


    assert "CALL" in result

    assert "PUT" in result


    assert len(
        result["CALL"]
    ) == 5


    assert len(
        result["PUT"]
    ) == 5



def test_selected():

    scanner = OptionScanner(
        create_contracts()
    )


    result = scanner.selected()


    assert (
        len(result)
        ==
        10
    )



# ==========================================================
# Summary
# ==========================================================


def test_summary():

    scanner = OptionScanner(
        create_contracts()
    )


    result = scanner.summary()


    assert (
        result["total_contracts"]
        ==
        12
    )


    assert (
        result["selected_count"]
        ==
        10
    )



def test_to_dict():

    scanner = OptionScanner(
        create_contracts()
    )


    result = scanner.to_dict()


    assert isinstance(
        result,
        dict,
    )



# ==========================================================
# Representation
# ==========================================================


def test_str():

    scanner = OptionScanner(
        create_contracts()
    )


    assert (
        "OptionScanner"
        in str(scanner)
    )



def test_repr():

    scanner = OptionScanner(
        create_contracts()
    )


    assert (
        "OptionScanner"
        in repr(scanner)
    )