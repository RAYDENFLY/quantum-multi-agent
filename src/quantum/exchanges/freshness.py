"""Market data feed freshness monitoring using monotonic clocks.

Maintains strict separation between:
- WebSocket connection state
- Ticker feed freshness
- Order book feed freshness
- Order book synchronization validity
- Candlestick feed freshness
"""

import time
from typing import Callable, Dict, Optional

from quantum.core.logging import get_logger
from quantum.domain.enums import OrderBookSyncStatus

logger = get_logger("exchanges.freshness")


class MarketDataFreshnessMonitor:
    """Monitors independent incoming feed streams and detects stale or stalled feeds."""

    def __init__(
        self,
        stale_threshold_s: float = 5.0,
        invalid_threshold_s: float = 15.0,
        on_stale_callback: Optional[Callable[[str, OrderBookSyncStatus], None]] = None,
    ) -> None:
        self.stale_threshold_s = stale_threshold_s
        self.invalid_threshold_s = invalid_threshold_s
        self.on_stale_callback = on_stale_callback

        # Independent channel monotonic timestamps: instrument_id -> float
        self._last_ticker_monotonic: Dict[str, float] = {}
        self._last_orderbook_monotonic: Dict[str, float] = {}
        self._last_candle_monotonic: Dict[str, float] = {}

        # Status tracking per channel
        self._orderbook_statuses: Dict[str, OrderBookSyncStatus] = {}
        self._ticker_statuses: Dict[str, OrderBookSyncStatus] = {}
        self._candle_statuses: Dict[str, OrderBookSyncStatus] = {}

    @property
    def _last_seen_monotonic(self) -> Dict[str, float]:
        """Backward compatibility alias for order book monotonic tracking."""
        return self._last_orderbook_monotonic

    @property
    def _statuses(self) -> Dict[str, OrderBookSyncStatus]:
        """Backward compatibility alias for order book status tracking."""
        return self._orderbook_statuses

    def record_ticker_heartbeat(self, instrument_id: str) -> None:
        """Record monotonic arrival time for a ticker update.

        Notice: Ticker heartbeats update only ticker freshness. They NEVER modify
        or restore order book synchronization validity.
        """
        now = time.monotonic()
        self._last_ticker_monotonic[instrument_id] = now
        prev_status = self._ticker_statuses.get(instrument_id)
        self._ticker_statuses[instrument_id] = OrderBookSyncStatus.SYNCHRONIZED
        if prev_status in (OrderBookSyncStatus.STALE, OrderBookSyncStatus.INVALID):
            logger.info("Ticker feed recovered for %s (marked SYNCHRONIZED)", instrument_id)

    def record_orderbook_heartbeat(self, instrument_id: str) -> None:
        """Record monotonic arrival time for an order book update."""
        now = time.monotonic()
        self._last_orderbook_monotonic[instrument_id] = now
        prev_status = self._orderbook_statuses.get(instrument_id)
        self._orderbook_statuses[instrument_id] = OrderBookSyncStatus.SYNCHRONIZED
        if prev_status in (OrderBookSyncStatus.STALE, OrderBookSyncStatus.INVALID):
            logger.info("Order book feed recovered for %s (marked SYNCHRONIZED)", instrument_id)
            if self.on_stale_callback:
                self.on_stale_callback(instrument_id, OrderBookSyncStatus.SYNCHRONIZED)

    def record_candle_heartbeat(self, instrument_id: str) -> None:
        """Record monotonic arrival time for a candlestick update."""
        now = time.monotonic()
        self._last_candle_monotonic[instrument_id] = now
        self._candle_statuses[instrument_id] = OrderBookSyncStatus.SYNCHRONIZED

    def record_heartbeat(self, instrument_id: str) -> None:
        """Backward compatibility generic heartbeat recorder (updates orderbook & ticker)."""
        self.record_ticker_heartbeat(instrument_id)
        self.record_orderbook_heartbeat(instrument_id)

    def check_orderbook_freshness(self, instrument_id: str) -> OrderBookSyncStatus:
        """Evaluate freshness of order book feed strictly based on order book message arrival."""
        last_seen = self._last_orderbook_monotonic.get(instrument_id)
        if last_seen is None:
            return OrderBookSyncStatus.INITIALIZING

        elapsed = time.monotonic() - last_seen
        new_status = OrderBookSyncStatus.SYNCHRONIZED

        if elapsed >= self.invalid_threshold_s:
            new_status = OrderBookSyncStatus.INVALID
        elif elapsed >= self.stale_threshold_s:
            new_status = OrderBookSyncStatus.STALE

        old_status = self._orderbook_statuses.get(instrument_id, OrderBookSyncStatus.SYNCHRONIZED)
        if new_status != old_status:
            self._orderbook_statuses[instrument_id] = new_status
            logger.warning(
                "Order book freshness state change for %s: %s -> %s (elapsed %.2fs)",
                instrument_id,
                old_status.value,
                new_status.value,
                elapsed,
            )
            if self.on_stale_callback:
                self.on_stale_callback(instrument_id, new_status)

        return new_status

    def check_ticker_freshness(self, instrument_id: str) -> OrderBookSyncStatus:
        """Evaluate freshness of ticker feed strictly based on ticker message arrival."""
        last_seen = self._last_ticker_monotonic.get(instrument_id)
        if last_seen is None:
            return OrderBookSyncStatus.INITIALIZING

        elapsed = time.monotonic() - last_seen
        if elapsed >= self.invalid_threshold_s:
            return OrderBookSyncStatus.INVALID
        elif elapsed >= self.stale_threshold_s:
            return OrderBookSyncStatus.STALE
        return OrderBookSyncStatus.SYNCHRONIZED

    def check_instrument(self, instrument_id: str) -> OrderBookSyncStatus:
        """Evaluate order book feed freshness (primary feed safety check)."""
        return self.check_orderbook_freshness(instrument_id)

    def check_all(self) -> Dict[str, OrderBookSyncStatus]:
        """Evaluate order book freshness across all monitored instruments."""
        results = {}
        for instrument_id in list(self._last_orderbook_monotonic.keys()):
            results[instrument_id] = self.check_orderbook_freshness(instrument_id)
        return results

    def remove_instrument(self, instrument_id: str) -> None:
        """Remove instrument from all channel monitoring."""
        self._last_ticker_monotonic.pop(instrument_id, None)
        self._last_orderbook_monotonic.pop(instrument_id, None)
        self._last_candle_monotonic.pop(instrument_id, None)
        self._orderbook_statuses.pop(instrument_id, None)
        self._ticker_statuses.pop(instrument_id, None)
        self._candle_statuses.pop(instrument_id, None)
