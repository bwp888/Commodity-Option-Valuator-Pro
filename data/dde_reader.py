"""
Commodity Option Valuator Pro
=============================

Wenhua Finance DDE Reader

Windows DDE market data interface.

Author : Simon
Version : 1.0.0
"""


from __future__ import annotations


from typing import Any


import pandas as pd



# ==========================================================
# DDE Exception
# ==========================================================


class DDEConnectionError(
    Exception
):
    """
    DDE connection error.
    """

    pass



# ==========================================================
# DDE Reader
# ==========================================================


class WenhuaDDEReader:
    """
    Wenhua Finance DDE reader.

    This class provides a unified
    interface for market data access.


    Notes
    -----

    Actual DDE communication depends on
    Windows COM/DDE environment.

    When unavailable,
    fallback to Excel reader.

    """
    DEFAULT_SERVER = (
        "WH6"
    )

    DEFAULT_TOPIC = (
        "Quote"
    )

    def __init__(
        self,
        server: str = DEFAULT_SERVER,
        topic: str = DEFAULT_TOPIC,
    ) -> None:
        """
        Initialize DDE reader.

        Parameters
        ----------
        server:
            DDE server name.

        topic:
            DDE topic name.
        """

        self.server = server

        self.topic = topic


        self.connected = False


        self._dde = None



    # ------------------------------------------------------
    # Connect
    # ------------------------------------------------------

    def connect(
        self,
    ) -> bool:
        """
        Connect Wenhua DDE.

        Returns
        -------
        bool
        """

        try:

            import win32ui


            self._dde = (
                win32ui.CreateObject(
                    "DDEClient"
                )
            )


            self.connected = True


            return True


        except Exception as exc:

            self.connected = False


            raise DDEConnectionError(
                "Unable to connect Wenhua DDE"
            ) from exc



    # ------------------------------------------------------
    # Disconnect
    # ------------------------------------------------------

    def disconnect(
        self,
    ) -> None:
        """
        Close DDE connection.
        """

        self._dde = None

        self.connected = False



    # ------------------------------------------------------
    # Request Data
    # ------------------------------------------------------

    def request(
        self,
        item: str,
    ) -> str:
        """
        Request single DDE item.

        Parameters
        ----------
        item:
            DDE item name.

        Returns
        -------
        str
        """

        if not self.connected:

            raise DDEConnectionError(
                "DDE not connected"
            )


        try:

            result = (
                self._dde.Request(
                    item
                )
            )


            return str(
                result
            )


        except Exception as exc:

            raise DDEConnectionError(
                f"DDE request failed: {item}"
            ) from exc



    # ------------------------------------------------------
    # Request Table
    # ------------------------------------------------------

    def request_dataframe(
        self,
        items: list[str],
    ) -> pd.DataFrame:
        """
        Request multiple DDE items.

        Parameters
        ----------
        items:
            DDE item list.

        Returns
        -------
        DataFrame
        """

        rows = []


        for item in items:

            value = self.request(
                item
            )


            rows.append(
                {
                    "item": item,

                    "value": value,
                }
            )



        return pd.DataFrame(
            rows
        )



    # ------------------------------------------------------
    # Status
    # ------------------------------------------------------

    def status(
        self,
    ) -> dict[str, Any]:
        """
        Return connection status.
        """

        return {

            "server":
                self.server,


            "topic":
                self.topic,


            "connected":
                self.connected,
        }



    # ------------------------------------------------------
    # Representation
    # ------------------------------------------------------

    def __str__(
        self,
    ) -> str:

        return (
            "WenhuaDDEReader("
            f"server={self.server}, "
            f"connected={self.connected}"
            ")"
        )



    def __repr__(
        self,
    ) -> str:

        return (
            "WenhuaDDEReader("
            f"server={self.server!r}, "
            f"topic={self.topic!r}"
            ")"
        )



__all__ = [

    "WenhuaDDEReader",

    "DDEConnectionError",

]