"""Unit tests for AsterDEX REST and WebSocket clients with mocked network calls."""

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from quantum.domain.enums import ConnectionState
from quantum.exchanges.aster.rest import AsterRestClient
from quantum.exchanges.aster.websocket import AsterWebSocketClient


class MockAsyncContext:
    """Mock asynchronous context manager for aiohttp response."""

    def __init__(self, response: Any) -> None:
        self.response = response

    async def __aenter__(self) -> Any:
        return self.response

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        return None


@pytest.mark.asyncio
async def test_aster_rest_methods_success() -> None:
    """Verify AsterDEX REST endpoints return correctly parsed JSON."""
    client = AsterRestClient(base_url="https://fapi.asterdex.com", max_retries=1)

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(
        return_value={"symbol": "ETHUSDT", "lastPrice": "3000.0", "bidPrice": "2999.5", "askPrice": "3000.5"}
    )

    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get.return_value = MockAsyncContext(mock_resp)

    with patch.object(client, "_get_session", return_value=mock_session):
        data = await client.get_ticker_24hr("ETHUSDT")
        assert data["symbol"] == "ETHUSDT"
        assert data["lastPrice"] == "3000.0"

    await client.close()


@pytest.mark.asyncio
async def test_aster_rest_retry_on_server_error() -> None:
    """Verify HTTP 500 triggers retry and succeeds on subsequent attempt."""
    client = AsterRestClient(max_retries=2, retry_backoff_s=0.01)

    mock_resp_500 = AsyncMock()
    mock_resp_500.status = 500

    mock_resp_200 = AsyncMock()
    mock_resp_200.status = 200
    mock_resp_200.json = AsyncMock(return_value={"serverTime": 1700000000999})

    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get.side_effect = [MockAsyncContext(mock_resp_500), MockAsyncContext(mock_resp_200)]

    with patch.object(client, "_get_session", return_value=mock_session):
        server_time = await client.get_server_time()
        assert server_time == 1700000000999

    await client.close()


@pytest.mark.asyncio
async def test_aster_ws_client_connect_and_message_routing() -> None:
    """Verify AsterDEX WebSocket connects, subscribes, and handles incoming stream events."""
    received = []

    async def on_message(data: dict) -> None:
        received.append(data)

    states = []

    def on_state(state: ConnectionState, err: str = None) -> None:
        states.append(state)

    ws_client = AsterWebSocketClient(
        url="wss://fstream.asterdex.com/ws",
        ping_interval_s=10.0,
        message_handler=on_message,
        state_callback=on_state,
    )

    mock_ws = AsyncMock()
    frames = [
        json.dumps({"result": None, "id": 2}),  # Subscription response
        json.dumps({"e": "depthUpdate", "s": "ETHUSDT", "u": 12345, "b": [["2999.0", "5.0"]], "a": [["3001.0", "5.0"]]}),
    ]

    async def frame_iter():
        for f in frames:
            yield f
        while True:
            await asyncio.sleep(0.1)

    mock_ws.__aiter__.side_effect = frame_iter

    with patch("websockets.connect", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_ws))):
        await ws_client.connect(streams=["ethusdt@depth@100ms"])
        await asyncio.sleep(0.05)

        assert ConnectionState.CONNECTED in states
        # The subscription result should be filtered out, depthUpdate received
        assert len(received) == 1
        assert received[0]["e"] == "depthUpdate"
        assert received[0]["s"] == "ETHUSDT"

        await ws_client.disconnect()
        assert ws_client.state == ConnectionState.DISCONNECTED
