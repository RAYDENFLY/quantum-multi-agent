"""AsterDEX exchange adapter package."""

from quantum.exchanges.aster.adapter import AsterExchangeAdapter
from quantum.exchanges.aster.normalizer import (
    normalize_aster_instrument,
    normalize_aster_klines,
    normalize_aster_orderbook,
    normalize_aster_ticker,
)
from quantum.exchanges.aster.rest import AsterRestClient
from quantum.exchanges.aster.websocket import AsterWebSocketClient

__all__ = [
    "AsterExchangeAdapter",
    "AsterRestClient",
    "AsterWebSocketClient",
    "normalize_aster_instrument",
    "normalize_aster_ticker",
    "normalize_aster_orderbook",
    "normalize_aster_klines",
]
