"""WebSocket client for Bybit V5 Linear Perpetuals public streams."""

import asyncio
import json
import random
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set
import websockets

from quantum.core.logging import get_logger
from quantum.domain.enums import ConnectionState

logger = get_logger("exchanges.bybit.ws")


class BybitWebSocketClient:
    """Manages resilient WebSocket connectivity to Bybit V5 public channels."""

    def __init__(
        self,
        url: str = "wss://stream.bybit.com/v5/public/linear",
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
        self.last_message_ms: int = 0
        self.state: ConnectionState = ConnectionState.DISCONNECTED

    def _set_state(self, new_state: ConnectionState, error_msg: Optional[str] = None) -> None:
        self.state = new_state
        if self.state_callback:
            self.state_callback(new_state, error_msg)

    async def connect(self, topics: Optional[List[str]] = None) -> None:
        """Start WebSocket connection loop and register subscriptions."""
        if topics:
            self._subscriptions.update(topics)

        self._running = True
        self._listen_task = asyncio.create_task(self._connection_loop(), name="bybit_ws_loop")

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
        logger.info("Bybit WebSocket disconnected successfully")

    async def subscribe(self, topics: List[str]) -> None:
        """Add topics to subscriptions and subscribe immediately if connected."""
        self._subscriptions.update(topics)
        if self._ws and self.state == ConnectionState.CONNECTED:
            msg = {"op": "subscribe", "args": topics}
            await self._ws.send(json.dumps(msg))
            logger.info("Subscribed to Bybit topics: %s", topics)

    async def _connection_loop(self) -> None:
        """Manage auto-reconnect with exponential backoff."""
        while self._running:
            self._set_state(
                ConnectionState.CONNECTING if self._reconnect_count == 0 else ConnectionState.RECONNECTING
            )
            try:
                logger.info("Connecting to Bybit WebSocket at %s", self.url)
                async with websockets.connect(
                    self.url,
                    ping_interval=None,  # Application sends custom Bybit JSON pings
                    ping_timeout=None,
                    close_timeout=5.0,
                ) as ws:
                    self._ws = ws
                    self._set_state(ConnectionState.CONNECTED)
                    self._reconnect_count = 0
                    logger.info("Connected to Bybit WebSocket")

                    # Resubscribe all registered topics
                    if self._subscriptions:
                        sub_msg = {"op": "subscribe", "args": list(self._subscriptions)}
                        await ws.send(json.dumps(sub_msg))
                        logger.info("Sent subscriptions for %d topics", len(self._subscriptions))

                    # Start heartbeat task
                    self._heartbeat_task = asyncio.create_task(self._heartbeat_loop(), name="bybit_ws_ping")

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
                    "Bybit WS connection dropped: %s (attempt %d/%d)",
                    err, self._reconnect_count, self.max_reconnect_attempts
                )
                self._set_state(ConnectionState.RECONNECTING, str(err))

                if self._heartbeat_task and not self._heartbeat_task.done():
                    self._heartbeat_task.cancel()

                if not self._running:
                    break

                if self._reconnect_count >= self.max_reconnect_attempts:
                    logger.error("Max reconnect attempts (%d) reached for Bybit WS", self.max_reconnect_attempts)
                    self._set_state(ConnectionState.FAILED, "Max reconnect attempts reached")
                    break

                backoff = min(
                    self.max_backoff_s,
                    (self.initial_backoff_s * (2 ** (self._reconnect_count - 1))) + random.uniform(0.1, 0.5)
                )
                logger.info("Reconnecting Bybit WS in %.2fs", backoff)
                await asyncio.sleep(backoff)

        self._set_state(ConnectionState.DISCONNECTED)

    async def _heartbeat_loop(self) -> None:
        """Send application-level JSON ping frames every ping_interval_s."""
        while self._running and self._ws:
            try:
                await asyncio.sleep(self.ping_interval_s)
                if self._ws:
                    ping_payload = json.dumps({"op": "ping"})
                    await self._ws.send(ping_payload)
                    logger.debug("Sent Bybit WebSocket ping")
            except asyncio.CancelledError:
                break
            except Exception as err:
                logger.warning("Error sending Bybit heartbeat ping: %s", err)
                break

    async def _handle_message(self, raw_text: str) -> None:
        """Parse incoming frame and route to handler."""
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            logger.warning("Received invalid JSON on Bybit WS: %s", raw_text[:100])
            return

        op = data.get("op")
        if op == "pong":
            logger.debug("Received Bybit WebSocket pong")
            return
        if op == "subscribe":
            success = data.get("success", False)
            ret_msg = data.get("ret_msg", "")
            if not success:
                logger.error("Bybit subscription error: %s", ret_msg)
            return

        if self.message_handler:
            try:
                await self.message_handler(data)
            except Exception as err:
                logger.error("Error in Bybit WS message handler: %s", err, exc_info=True)
