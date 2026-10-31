"""WebSocket client for AsterDEX Futures public streams."""

import asyncio
import json
import random
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set
import websockets

from quantum.core.logging import get_logger
from quantum.domain.enums import ConnectionState

logger = get_logger("exchanges.aster.ws")


class AsterWebSocketClient:
    """Manages resilient WebSocket connectivity to AsterDEX public streams."""

    def __init__(
        self,
        url: str = "wss://fstream.asterdex.com/ws",
        ping_interval_s: float = 20.0,
        ping_timeout_s: float = 10.0,
        max_reconnect_attempts: int = 10,
        initial_backoff_s: float = 1.0,
        max_backoff_s: float = 60.0,
        message_handler: Optional[Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]] = None,
        state_callback: Optional[Callable[[ConnectionState, Optional[str]], None]] = None,
    ) -> None:
        self.url = url
        self.ping_interval_s = ping_interval_s
        self.ping_timeout_s = ping_timeout_s
        self.max_reconnect_attempts = max_reconnect_attempts
        self.initial_backoff_s = initial_backoff_s
        self.max_backoff_s = max_backoff_s
        self.message_handler = message_handler
        self.state_callback = state_callback

        self._subscriptions: Set[str] = set()
        self._running: bool = False
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._listen_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._reconnect_count: int = 0
        self._sub_req_id: int = 1
        self.last_message_ms: int = 0
        self.state: ConnectionState = ConnectionState.DISCONNECTED

    def _set_state(self, new_state: ConnectionState, error_msg: Optional[str] = None) -> None:
        self.state = new_state
        if self.state_callback:
            self.state_callback(new_state, error_msg)

    async def connect(self, streams: Optional[List[str]] = None) -> None:
        """Start WebSocket connection loop and register subscriptions."""
        if streams:
            self._subscriptions.update(streams)

        self._running = True
        self._listen_task = asyncio.create_task(self._connection_loop(), name="aster_ws_loop")

    async def disconnect(self) -> None:
        """Gracefully close WebSocket connection and background tasks."""
        self._running = False
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None

        self._set_state(ConnectionState.DISCONNECTED)
        logger.info("AsterDEX WebSocket disconnected successfully")

    async def subscribe(self, streams: List[str]) -> None:
        """Add streams to subscriptions and send subscription payload if connected."""
        self._subscriptions.update(streams)
        if self._ws and self.state == ConnectionState.CONNECTED:
            self._sub_req_id += 1
            msg = {
                "method": "SUBSCRIBE",
                "params": streams,
                "id": self._sub_req_id,
            }
            await self._ws.send(json.dumps(msg))
            logger.info("Subscribed to AsterDEX streams: %s", streams)

    async def _connection_loop(self) -> None:
        """Manage auto-reconnect with exponential backoff."""
        while self._running:
            self._set_state(
                ConnectionState.CONNECTING if self._reconnect_count == 0 else ConnectionState.RECONNECTING
            )
            try:
                logger.info("Connecting to AsterDEX WebSocket at %s", self.url)
                async with websockets.connect(
                    self.url,
                    ping_interval=20,
                    ping_timeout=self.ping_timeout_s,
                    close_timeout=5.0,
                ) as ws:
                    self._ws = ws
                    self._set_state(ConnectionState.CONNECTED)
                    self._reconnect_count = 0
                    logger.info("Connected to AsterDEX WebSocket")

                    # Resubscribe all registered streams
                    if self._subscriptions:
                        self._sub_req_id += 1
                        sub_msg = {
                            "method": "SUBSCRIBE",
                            "params": list(self._subscriptions),
                            "id": self._sub_req_id,
                        }
                        await ws.send(json.dumps(sub_msg))
                        logger.info("Sent subscriptions for %d AsterDEX streams", len(self._subscriptions))

                    # Read messages
                    async for raw_message in ws:
                        if not self._running:
                            break
                        self.last_message_ms = int(time.time() * 1000)
                        await self._handle_message(raw_message)

            except asyncio.CancelledError:
                break
            except Exception as err:
                self._reconnect_count += 1
                logger.warning(
                    "AsterDEX WS connection dropped: %s (attempt %d/%d)",
                    err, self._reconnect_count, self.max_reconnect_attempts
                )
                self._set_state(ConnectionState.RECONNECTING, str(err))

                if not self._running:
                    break

                if self._reconnect_count >= self.max_reconnect_attempts:
                    logger.error("Max reconnect attempts (%d) reached for AsterDEX WS", self.max_reconnect_attempts)
                    self._set_state(ConnectionState.FAILED, "Max reconnect attempts reached")
                    break

                backoff = min(
                    self.max_backoff_s,
                    (self.initial_backoff_s * (2 ** (self._reconnect_count - 1))) + random.uniform(0.1, 0.5)
                )
                logger.info("Reconnecting AsterDEX WS in %.2fs", backoff)
                await asyncio.sleep(backoff)

        self._set_state(ConnectionState.DISCONNECTED)

    async def _handle_message(self, raw_text: str) -> None:
        """Parse incoming frame and route to handler."""
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            logger.warning("Received invalid JSON on AsterDEX WS: %s", raw_text[:100])
            return

        # Check for subscription confirmation
        if "result" in data and "id" in data:
            logger.debug("Received AsterDEX subscription response id=%s", data["id"])
            return

        if self.message_handler:
            try:
                await self.message_handler(data)
            except Exception as err:
                logger.error("Error in AsterDEX WS message handler: %s", err, exc_info=True)
