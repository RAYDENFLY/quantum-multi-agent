"""Local order book maintenance, exchange-specific synchronization, and sequence validation.

Provides specialized synchronizers for:
- Bybit V5 Linear Perpetuals (BybitLocalOrderBook):
  Full snapshot replacement, delta updates, zero-quantity level deletion,
  monotonically increasing update ID (u), u=1 service restart detection,
  and cross-sequence (seq) handling without consecutive ID assumptions.
- AsterDEX Futures (AsterLocalOrderBook):
  Binance Futures-compatible depth protocol with delta buffering before snapshot,
  snapshot bridging verification (U <= lastUpdateId <= u), subsequent event continuity
  (pu == last_u), and absolute quantity updates with safe missing-level deletions.
"""

import time
from typing import Any, Dict, List, Optional, Tuple

from quantum.core.logging import get_logger
from quantum.domain.enums import Exchange, OrderBookSyncStatus
from quantum.exchanges.models import NormalizedOrderBook, OrderBookLevel

logger = get_logger("exchanges.orderbook")


class BaseLocalOrderBook:
    """Abstract base class for in-memory L2 order books."""

    def __init__(
        self,
        instrument_id: str,
        exchange: Exchange,
        symbol: str,
        depth: int = 50,
    ) -> None:
        self.instrument_id = instrument_id
        self.exchange = exchange
        self.symbol = symbol
        self.depth = depth

        self.bids: Dict[float, float] = {}
        self.asks: Dict[float, float] = {}
        self.last_update_id: int = 0
        self.last_update_time_ms: int = 0
        self._last_monotonic: float = 0.0
        self.status: OrderBookSyncStatus = OrderBookSyncStatus.INITIALIZING
        self.gap_count: int = 0
        self.crossed_count: int = 0

    def reset(self) -> None:
        """Reset order book state back to INITIALIZING."""
        self.bids.clear()
        self.asks.clear()
        self.last_update_id = 0
        self.last_update_time_ms = 0
        self._last_monotonic = 0.0
        self.status = OrderBookSyncStatus.INITIALIZING

    def _is_crossed(self) -> bool:
        """Return True if best bid >= best ask."""
        if not self.bids or not self.asks:
            return False
        best_bid = max(self.bids.keys())
        best_ask = min(self.asks.keys())
        return best_bid >= best_ask

    def check_freshness(
        self,
        stale_threshold_s: float = 5.0,
        invalid_threshold_s: float = 15.0,
    ) -> OrderBookSyncStatus:
        """Update and return sync status based on monotonic elapsed time.

        Notice: A degraded book (STALE or INVALID) can only return to SYNCHRONIZED
        via explicit order book update/snapshot synchronization, not elapsed time.
        """
        if self.status in (OrderBookSyncStatus.INITIALIZING, OrderBookSyncStatus.RESYNCING):
            return self.status

        if self._last_monotonic == 0.0:
            return self.status

        elapsed = time.monotonic() - self._last_monotonic
        if elapsed > invalid_threshold_s:
            self.status = OrderBookSyncStatus.INVALID
        elif elapsed > stale_threshold_s:
            if self.status == OrderBookSyncStatus.SYNCHRONIZED:
                self.status = OrderBookSyncStatus.STALE

        return self.status

    def to_normalized(self) -> NormalizedOrderBook:
        """Export sorted and depth-truncated NormalizedOrderBook."""
        sorted_bids = sorted(self.bids.items(), key=lambda x: x[0], reverse=True)[: self.depth]
        sorted_asks = sorted(self.asks.items(), key=lambda x: x[0])[: self.depth]

        bids_models = [OrderBookLevel(price=p, size=s) for p, s in sorted_bids]
        asks_models = [OrderBookLevel(price=p, size=s) for p, s in sorted_asks]

        return NormalizedOrderBook(
            instrument_id=self.instrument_id,
            exchange=self.exchange,
            symbol=self.symbol,
            timestamp_ms=self.last_update_time_ms,
            update_id=self.last_update_id,
            bids=bids_models,
            asks=asks_models,
        )


class BybitLocalOrderBook(BaseLocalOrderBook):
    """Bybit V5 Linear Perpetuals local order book synchronizer.

    Adheres strictly to Bybit V5 public order book channel semantics:
    - Snapshot: Clears local book and replaces all levels. Repeated snapshots
      cleanly overwrite the entire book.
    - Delta: Modifies existing levels. Quantity of 0 deletes price level.
      Updates to non-existent levels are handled safely.
    - Sequence check:
      - 'u' is monotonically increasing. If delta u <= last_u, it is rejected as duplicate.
      - 'u = 1' signals Bybit matching engine service restart snapshot. Local book is
        immediately overwritten with the incoming snapshot levels.
      - 'seq' is cross-engine sequence and is NOT consecutive. It is never validated
        as seq == last_seq + 1.
      - Bybit linear order book channel does not provide 'pu'.
    """

    def __init__(
        self,
        instrument_id: str,
        symbol: str = "",
        depth: int = 50,
        exchange: Exchange = Exchange.BYBIT,
    ) -> None:
        # Handle cases where symbol or exchange are passed positionally
        sym = symbol if isinstance(symbol, str) else getattr(exchange, "value", str(exchange))
        if isinstance(symbol, Exchange):
            sym = str(depth) if isinstance(depth, str) else instrument_id.split(":")[-1]
        super().__init__(instrument_id, Exchange.BYBIT, sym, depth if isinstance(depth, int) else 50)
        self.last_seq: int = 0

    def apply_snapshot(
        self,
        bids: List[Tuple[float, float]],
        asks: List[Tuple[float, float]],
        update_id: int,
        timestamp_ms: int,
        seq: int = 0,
    ) -> bool:
        """Load complete Bybit orderbook snapshot. Repeated snapshots overwrite local book."""
        self.bids.clear()
        self.asks.clear()

        for price, size in bids:
            if price > 0.0 and size > 0.0:
                self.bids[price] = size

        for price, size in asks:
            if price > 0.0 and size > 0.0:
                self.asks[price] = size

        self.last_update_id = update_id
        self.last_seq = seq
        self.last_update_time_ms = timestamp_ms
        self._last_monotonic = time.monotonic()

        if self._is_crossed():
            self.crossed_count += 1
            self.status = OrderBookSyncStatus.INVALID
            logger.warning("Bybit snapshot crossed for %s: bid1 >= ask1", self.instrument_id)
            return False

        self.status = OrderBookSyncStatus.SYNCHRONIZED
        return True

    def apply_delta(
        self,
        bids: List[Tuple[float, float]],
        asks: List[Tuple[float, float]],
        update_id: int,
        timestamp_ms: int,
        seq: int = 0,
        prev_update_id: Optional[int] = None,
    ) -> bool:
        """Apply incremental Bybit L2 updates with Bybit V5 sequence checks."""
        # 1. Bybit service reset check: u=1 indicates service restart snapshot
        if update_id == 1:
            logger.info(
                "Bybit service restart snapshot (u=1) received for %s. Overwriting local book immediately.",
                self.instrument_id,
            )
            return self.apply_snapshot(bids, asks, update_id, timestamp_ms, seq=seq)

        if self.status != OrderBookSyncStatus.SYNCHRONIZED:
            logger.debug(
                "Ignoring Bybit delta for %s while status is %s (awaiting snapshot)",
                self.instrument_id,
                self.status.value,
            )
            return False

        # 2. Monotonic update ID check: delta u must be strictly greater than last_u
        if self.last_update_id > 0 and update_id <= self.last_update_id:
            logger.warning(
                "Out-of-order or duplicate Bybit delta for %s: last_u=%d, incoming_u=%d. Discarded.",
                self.instrument_id,
                self.last_update_id,
                update_id,
            )
            return False

        # Sequence gap check if prev_update_id is explicitly supplied
        if prev_update_id is not None and self.last_update_id > 0 and prev_update_id != self.last_update_id:
            self.gap_count += 1
            self.status = OrderBookSyncStatus.RESYNCING
            logger.warning(
                "Sequence gap for %s: expected prev_id=%d, got %d. Initiating resync.",
                self.instrument_id,
                self.last_update_id,
                prev_update_id,
            )
            return False

        # Note on seq: Bybit seq is cross-sequence and can jump arbitrarily; do not check continuity.
        self.last_seq = seq

        # 3. Apply bids: size <= 0 deletes level
        for price, size in bids:
            if size <= 0.0:
                self.bids.pop(price, None)
            elif price > 0.0:
                self.bids[price] = size

        # 4. Apply asks: size <= 0 deletes level
        for price, size in asks:
            if size <= 0.0:
                self.asks.pop(price, None)
            elif price > 0.0:
                self.asks[price] = size

        self.last_update_id = update_id
        self.last_update_time_ms = timestamp_ms
        self._last_monotonic = time.monotonic()

        # 5. Check crossed book
        if self._is_crossed():
            self.crossed_count += 1
            self.status = OrderBookSyncStatus.INVALID
            logger.warning(
                "Crossed book detected for %s after Bybit delta update_id=%d",
                self.instrument_id,
                update_id,
            )
            return False

        return True


class AsterLocalOrderBook(BaseLocalOrderBook):
    """AsterDEX Futures local order book synchronizer.

    Adheres strictly to Binance Futures-compatible depth protocol:
    1. Buffers incoming WebSocket depthUpdate events prior to snapshot.
    2. Drops buffered events where u < lastUpdateId in snapshot.
    3. Verifies that the first processed event bridges the snapshot:
       first_event U <= lastUpdateId <= first_event u.
    4. Enforces subsequent event continuity:
       subsequent_event pu == previous_event u.
    5. A sequence gap triggers book invalidation and resynchronization.
    6. Updates represent absolute quantities; quantity 0 deletes the level.
       Deletion of a non-existent level is handled safely.
    """

    def __init__(
        self,
        instrument_id: str,
        symbol: str = "",
        depth: int = 50,
        exchange: Exchange = Exchange.ASTER,
    ) -> None:
        sym = symbol if isinstance(symbol, str) else getattr(exchange, "value", str(exchange))
        if isinstance(symbol, Exchange):
            sym = str(depth) if isinstance(depth, str) else instrument_id.split(":")[-1]
        super().__init__(instrument_id, Exchange.ASTER, sym, depth if isinstance(depth, int) else 50)
        self._event_buffer: List[Dict[str, Any]] = []
        self.is_buffering: bool = True

    def reset(self) -> None:
        """Reset order book and event buffer."""
        super().reset()
        self._event_buffer.clear()
        self.is_buffering = True

    def buffer_event(self, event: Dict[str, Any]) -> None:
        """Buffer incoming depthUpdate event prior to snapshot alignment."""
        if len(self._event_buffer) < 1000:
            self._event_buffer.append(event)
        else:
            # Drop oldest event if buffer is overflowing
            self._event_buffer.pop(0)
            self._event_buffer.append(event)

    def apply_snapshot_with_buffer(
        self,
        snapshot_bids: List[Tuple[float, float]],
        snapshot_asks: List[Tuple[float, float]],
        snapshot_last_update_id: int,
        timestamp_ms: int,
    ) -> bool:
        """Initialize local book from REST snapshot and align buffered WebSocket events."""
        self.bids.clear()
        self.asks.clear()

        for price, size in snapshot_bids:
            if price > 0.0 and size > 0.0:
                self.bids[price] = size

        for price, size in snapshot_asks:
            if price > 0.0 and size > 0.0:
                self.asks[price] = size

        self.last_update_id = snapshot_last_update_id
        self.last_update_time_ms = timestamp_ms
        self._last_monotonic = time.monotonic()

        if self._is_crossed():
            self.crossed_count += 1
            self.status = OrderBookSyncStatus.INVALID
            self._event_buffer.clear()
            self.is_buffering = True
            logger.warning("AsterDEX snapshot crossed for %s: bid1 >= ask1", self.instrument_id)
            return False

        # Drop events where final update id u < snapshot_last_update_id
        valid_events = [e for e in self._event_buffer if int(e.get("u", 0)) >= snapshot_last_update_id]
        self._event_buffer = valid_events

        if not valid_events:
            # Buffer did not yet capture events after snapshot. Keep buffering.
            logger.info(
                "AsterDEX order book snapshot loaded for %s (id=%d). Awaiting bridging event in stream.",
                self.instrument_id,
                snapshot_last_update_id,
            )
            # Remain in INITIALIZING until first bridging event arrives
            return True

        # First event must bridge the snapshot:
        # U <= lastUpdateId <= u (or pu <= lastUpdateId <= u)
        first_event = valid_events[0]
        first_U = int(first_event.get("U", 0))
        first_u = int(first_event.get("u", 0))
        first_pu = int(first_event.get("pu", 0))

        # Check bridging condition
        bridged = (first_U <= snapshot_last_update_id <= first_u) or (first_pu <= snapshot_last_update_id <= first_u)

        if not bridged:
            self.gap_count += 1
            self.status = OrderBookSyncStatus.RESYNCING
            self._event_buffer.clear()
            self.is_buffering = True
            logger.error(
                "AsterDEX buffer alignment gap for %s: snapshot_id=%d, first_U=%d, first_u=%d, first_pu=%d",
                self.instrument_id,
                snapshot_last_update_id,
                first_U,
                first_u,
                first_pu,
            )
            return False

        # Playback all buffered events from first_event onward
        for idx, event in enumerate(valid_events):
            if idx > 0:
                event_pu = int(event.get("pu", 0))
                if event_pu != self.last_update_id:
                    self.gap_count += 1
                    self.status = OrderBookSyncStatus.RESYNCING
                    self._event_buffer.clear()
                    self.is_buffering = True
                    logger.error(
                        "AsterDEX buffer playback gap for %s: expected pu=%d, got %d",
                        self.instrument_id,
                        self.last_update_id,
                        event_pu,
                    )
                    return False

            self._apply_raw_event_levels(event)
            self.last_update_id = int(event["u"])
            self.last_update_time_ms = int(event.get("E", timestamp_ms))
            self._last_monotonic = time.monotonic()

        self._event_buffer.clear()
        self.is_buffering = False

        if self._is_crossed():
            self.crossed_count += 1
            self.status = OrderBookSyncStatus.INVALID
            return False

        self.status = OrderBookSyncStatus.SYNCHRONIZED
        logger.info(
            "AsterDEX order book successfully synchronized for %s with %d buffered events",
            self.instrument_id,
            len(valid_events),
        )
        return True

    def apply_delta_event(self, event: Dict[str, Any]) -> bool:
        """Apply live AsterDEX depthUpdate event with pu == last_u verification."""
        if self.status != OrderBookSyncStatus.SYNCHRONIZED:
            if self.is_buffering:
                self.buffer_event(event)
            return False

        event_pu = int(event.get("pu", 0))
        event_u = int(event.get("u", 0))

        # Check consecutive sequence: pu must equal last_u
        if self.last_update_id > 0 and event_pu != self.last_update_id:
            self.gap_count += 1
            self.status = OrderBookSyncStatus.RESYNCING
            self.is_buffering = True
            self._event_buffer.clear()
            logger.error(
                "AsterDEX sequence mismatch for %s: expected pu=%d, got %d. Initiating resync.",
                self.instrument_id,
                self.last_update_id,
                event_pu,
            )
            return False

        self._apply_raw_event_levels(event)
        self.last_update_id = event_u
        self.last_update_time_ms = int(event.get("E", time.time() * 1000))
        self._last_monotonic = time.monotonic()

        if self._is_crossed():
            self.crossed_count += 1
            self.status = OrderBookSyncStatus.INVALID
            logger.warning(
                "Crossed book detected for %s after AsterDEX delta u=%d",
                self.instrument_id,
                event_u,
            )
            return False

        return True

    def _apply_raw_event_levels(self, event: Dict[str, Any]) -> None:
        """Apply bids and asks price levels from a raw AsterDEX depthUpdate event."""
        # Bids
        for item in event.get("b", []):
            p, s = float(item[0]), float(item[1])
            if s <= 0.0:
                self.bids.pop(p, None)  # Safe deletion even if non-existent
            elif p > 0.0:
                self.bids[p] = s

        # Asks
        for item in event.get("a", []):
            p, s = float(item[0]), float(item[1])
            if s <= 0.0:
                self.asks.pop(p, None)  # Safe deletion even if non-existent
            elif p > 0.0:
                self.asks[p] = s

    # Backwards compatibility wrappers
    def apply_snapshot(
        self,
        bids: List[Tuple[float, float]],
        asks: List[Tuple[float, float]],
        update_id: int,
        timestamp_ms: int,
    ) -> bool:
        """Compatibility wrapper calling apply_snapshot_with_buffer."""
        res = self.apply_snapshot_with_buffer(bids, asks, update_id, timestamp_ms)
        # If no events in buffer, mark SYNCHRONIZED for static snapshots
        if not self._event_buffer and self.status == OrderBookSyncStatus.INITIALIZING:
            self.status = OrderBookSyncStatus.SYNCHRONIZED
            self.is_buffering = False
        return res

    def apply_delta(
        self,
        bids: List[Tuple[float, float]],
        asks: List[Tuple[float, float]],
        update_id: int,
        timestamp_ms: int,
        prev_update_id: Optional[int] = None,
    ) -> bool:
        """Compatibility wrapper calling apply_delta_event."""
        event = {
            "b": bids,
            "a": asks,
            "u": update_id,
            "pu": prev_update_id if prev_update_id is not None else self.last_update_id,
            "E": timestamp_ms,
        }
        return self.apply_delta_event(event)


# Backward compatibility default alias
LocalOrderBook = BybitLocalOrderBook
