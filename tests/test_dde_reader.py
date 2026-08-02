"""
Commodity Option Valuator Pro
=============================

DDE Reader Tests

Author : Simon
Version : 1.0.0
"""


from __future__ import annotations


import pytest


from data.dde_reader import (

    WenhuaDDEReader,

    DDEConnectionError,

)



# ==========================================================
# Init
# ==========================================================


def test_create():

    reader = WenhuaDDEReader()


    assert (
        reader.connected
        is False
    )



def test_status():

    reader = WenhuaDDEReader()


    status = (
        reader.status()
    )


    assert (
        "server"
        in status
    )


    assert (
        "connected"
        in status
    )



# ==========================================================
# Request
# ==========================================================


def test_request_without_connect():

    reader = WenhuaDDEReader()


    with pytest.raises(
        DDEConnectionError
    ):

        reader.request(
            "TEST"
        )



# ==========================================================
# Disconnect
# ==========================================================


def test_disconnect():

    reader = WenhuaDDEReader()


    reader.disconnect()


    assert (
        reader.connected
        is False
    )



# ==========================================================
# Representation
# ==========================================================


def test_str():

    reader = WenhuaDDEReader()


    assert (
        "WenhuaDDEReader"
        in str(reader)
    )



def test_repr():

    reader = WenhuaDDEReader()


    assert (
        "WenhuaDDEReader"
        in repr(reader)
    )