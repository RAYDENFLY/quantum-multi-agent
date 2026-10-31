"""Unit tests for LocalOrderBook state machine, deltas, and gap detection."""

import time
import pytest

from quantum.domain.enums import Exchange, OrderBookSyncStatus
from quantum.exchanges.orderbook import LocalOrderBook


def test_orderbook_lifecycle_and_snapshot() -> None:
    """Verify initial state, snapshot application, and sorting."""
    ob = LocalOrderBook(
        instrument_id="BYBIT:BTCUSDT",
        exchange=Exchange.BYBIT,
        symbol="BTCUSDT",
        depth=10,
    )
    assert ob.status == OrderBookSyncStatus.INITIALIZING
    assert len(ob.bids) == 0
    assert len(ob.asks) == 0

    snapshot_bids = [(50000.0, 1.0), (49990.0, 2.0), (49980.0, 3.0)]
    snapshot_asks = [(50010.0, 1.5), (50020.0, 2.5), (50030.0, 3.5)]

    success = ob.apply_snapshot(snapshot_bids, snapshot_asks, update_id=100, timestamp_ms=1700000000000)
    assert success is True
    assert ob.status == OrderBookSyncStatus.SYNCHRONIZED
    assert ob.last_update_id == 100

    normalized = ob.to_normalized()
    assert normalized.bid1_price == 50000.0
    assert normalized.bid1_size == 1.0
    assert normalized.ask1_price == 50010.0
    assert normalized.ask1_size == 1.5
    assert not normalized.is_crossed


def test_orderbook_apply_delta_modifications_and_deletions() -> None:
    """Verify delta updates: addition, price modification, and level removal on zero size."""
    ob = LocalOrderBook("BYBIT:BTCUSDT", Exchange.BYBIT, "BTCUSDT")
    ob.apply_snapshot([(50000.0, 1.0), (49990.0, 2.0)], [(50010.0, 1.0), (50020.0, 2.0)], update_id=10, timestamp_ms=1000)

    # 1. Modify bid size, add new ask level, delete ask level 50020
    delta_bids = [(50000.0, 5.0)]  # Size updated from 1.0 to 5.0
    delta_asks = [(50015.0, 0.8), (50020.0, 0.0)]  # 50015 added, 50020 removed

    success = ob.apply_delta(delta_bids, delta_asks, update_id=11, timestamp_ms=1100, prev_update_id=10)
    assert success is True
    assert ob.last_update_id == 11
    assert ob.bids[50000.0] == 5.0
    assert ob.asks[50015.0] == 0.8
    assert 50020.0 not in ob.asks


def test_orderbook_delta_ignored_when_not_synchronized() -> None:
    """Verify deltas are rejected if order book has not received an initial snapshot."""
    ob = LocalOrderBook("BYBIT:BTCUSDT", Exchange.BYBIT, "BTCUSDT")
    assert ob.status == OrderBookSyncStatus.INITIALIZING

    success = ob.apply_delta([(50000.0, 1.0)], [(50010.0, 1.0)], update_id=5, timestamp_ms=1000)
    assert success is False
    assert len(ob.bids) == 0


def test_orderbook_sequence_gap_detection() -> None:
    """Verify sequence gap transitions order book to RESYNCING."""
    ob = LocalOrderBook("BYBIT:BTCUSDT", Exchange.BYBIT, "BTCUSDT")
    ob.apply_snapshot([(50000.0, 1.0)], [(50010.0, 1.0)], update_id=100, timestamp_ms=1000)

    # Delta arrives expecting prev_update_id=105 instead of 100
    success = ob.apply_delta([(50000.0, 2.0)], [], update_id=106, timestamp_ms=1100, prev_update_id=105)
    assert success is False
    assert ob.status == OrderBookSyncStatus.RESYNCING
    assert ob.gap_count == 1


def test_orderbook_crossed_book_detection() -> None:
    """Verify crossed book condition (bid1 >= ask1) transitions state to INVALID."""
    ob = LocalOrderBook("BYBIT:BTCUSDT", Exchange.BYBIT, "BTCUSDT")
    ob.apply_snapshot([(50000.0, 1.0)], [(50010.0, 1.0)], update_id=10, timestamp_ms=1000)

    # Delta pushes bid above ask: bid=50015, ask=50010
    success = ob.apply_delta([(50015.0, 1.0)], [], update_id=11, timestamp_ms=1100, prev_update_id=10)
    assert success is False
    assert ob.status == OrderBookSyncStatus.INVALID
    assert ob.crossed_count == 1


def test_orderbook_freshness_evaluation() -> None:
    """Verify time-based freshness degradation."""
    ob = LocalOrderBook("BYBIT:BTCUSDT", Exchange.BYBIT, "BTCUSDT")
    ob.apply_snapshot([(50000.0, 1.0)], [(50010.0, 1.0)], update_id=1, timestamp_ms=1000)
    assert ob.status == OrderBookSyncStatus.SYNCHRONIZED

    # Simulate time elapsed
    ob._last_monotonic = time.monotonic() - 6.0
    status = ob.check_freshness(stale_threshold_s=5.0, invalid_threshold_s=15.0)
    assert status == OrderBookSyncStatus.STALE

    ob._last_monotonic = time.monotonic() - 16.0
    status = ob.check_freshness(stale_threshold_s=5.0, invalid_threshold_s=15.0)
    assert status == OrderBookSyncStatus.INVALID


def test_orderbook_reset() -> None:
    """Verify reset clears depth and resets status to INITIALIZING."""
    ob = LocalOrderBook("BYBIT:BTCUSDT", Exchange.BYBIT, "BTCUSDT")
    ob.apply_snapshot([(50000.0, 1.0)], [(50010.0, 1.0)], update_id=1, timestamp_ms=1000)
    ob.reset()

    assert ob.status == OrderBookSyncStatus.INITIALIZING
    assert len(ob.bids) == 0
    assert len(ob.asks) == 0
    assert ob.last_update_id == 0
