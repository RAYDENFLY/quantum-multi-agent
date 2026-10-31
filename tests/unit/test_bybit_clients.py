"""Unit tests for Bybit REST and WebSocket clients with mocked network calls."""

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from quantum.domain.enums import ConnectionState
from quantum.exchanges.base import TokenBucketRateLimiter
from quantum.exchanges.bybit.rest import BybitRestClient
from quantum.exchanges.bybit.websocket import BybitWebSocketClient


class MockAsyncContext:
    """Mock asynchronous context manager for aiohttp response."""

    def __init__(self, response: Any) -> None:
        self.response = response

    async def __aenter__(self) -> Any:
        return self.response

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        return None


@pytest.mark.asyncio
async def test_bybit_rest_get_ticker_success() -> None:
    """Verify REST get_ticker method parses standard Bybit V5 structure."""
    client = BybitRestClient(base_url="https://api.bybit.com", max_retries=1)

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(
        return_value={
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "list": [
                    {"symbol": "BTCUSDT", "lastPrice": "50000.0", "bid1Price": "49999.0", "ask1Price": "50001.0"}
                ]
            },
        }
    )

    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get.return_value = MockAsyncContext(mock_resp)

    with patch.object(client, "_get_session", return_value=mock_session):
        data = await client.get_ticker("BTCUSDT")
        assert data["symbol"] == "BTCUSDT"
        assert data["lastPrice"] == "50000.0"

    await client.close()


@pytest.mark.asyncio
async def test_bybit_rest_error_code_raises_runtime_error() -> None:
    """Verify Bybit non-zero retCode raises RuntimeError."""
    client = BybitRestClient(max_retries=0)

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"retCode": 10001, "retMsg": "Params error", "result": {}})

    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get.return_value = MockAsyncContext(mock_resp)

    with patch.object(client, "_get_session", return_value=mock_session):
        with pytest.raises(RuntimeError, match="Bybit API error code 10001"):
            await client.get_instruments_info()

    await client.close()


@pytest.mark.asyncio
async def test_bybit_rest_rate_limit_retry() -> None:
    """Verify HTTP 429 triggers exponential backoff retry and succeeds."""
    client = BybitRestClient(max_retries=2, retry_backoff_s=0.01)

    mock_resp_429 = AsyncMock()
    mock_resp_429.status = 429

    mock_resp_200 = AsyncMock()
    mock_resp_200.status = 200
    mock_resp_200.json = AsyncMock(
        return_value={"retCode": 0, "retMsg": "OK", "result": {"timeNano": "1700000000000000000"}}
    )

    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get.side_effect = [MockAsyncContext(mock_resp_429), MockAsyncContext(mock_resp_200)]

    with patch.object(client, "_get_session", return_value=mock_session):
        server_time = await client.get_server_time()
        assert server_time == 1700000000000

    await client.close()


@pytest.mark.asyncio
async def test_bybit_ws_client_connect_and_message_routing() -> None:
    """Verify WebSocket message handling, subscriptions, and graceful disconnect."""
    received = []

    async def on_message(data: dict) -> None:
        received.append(data)

    states = []

    def on_state(state: ConnectionState, err: str = None) -> None:
        states.append(state)

    ws_client = BybitWebSocketClient(
        url="wss://stream.bybit.com/v5/public/linear",
        ping_interval_s=10.0,
        message_handler=on_message,
        state_callback=on_state,
    )

    # Mock websocket protocol
    mock_ws = AsyncMock()
    # Simulate receiving a ticker frame, a pong frame, and then completing
    frames = [
        json.dumps({"topic": "tickers.BTCUSDT", "data": {"symbol": "BTCUSDT", "lastPrice": "50000.0"}}),
        json.dumps({"op": "pong"}),
    ]

    async def frame_iter():
        for f in frames:
            yield f
        # Wait until cancelled
        while True:
            await asyncio.sleep(0.1)

    mock_ws.__aiter__.side_effect = frame_iter

    with patch("websockets.connect", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_ws))):
        await ws_client.connect(topics=["tickers.BTCUSDT"])
        await asyncio.sleep(0.05)

        # Verify state transitioned to CONNECTED
        assert ConnectionState.CONNECTED in states
        # Verify ticker message was received
        assert len(received) == 1
        assert received[0]["topic"] == "tickers.BTCUSDT"

        await ws_client.disconnect()
        assert ws_client.state == ConnectionState.DISCONNECTED
