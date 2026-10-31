"""Unit tests for exchange-specific order book synchronization (Bybit V5 vs AsterDEX Futures)."""

import pytest

from quantum.domain.enums import Exchange, OrderBookSyncStatus
from quantum.exchanges.orderbook import AsterLocalOrderBook, BybitLocalOrderBook


# ============================================================================
# 1. Bybit V5 Specific Synchronization Tests
# ============================================================================


def test_bybit_snapshot_replacement_and_repeated_overwrites() -> None:
    """Verify that Bybit snapshot replaces the entire local book on initial and repeated calls."""
    ob = BybitLocalOrderBook("BYBIT:BTCUSDT", "BTCUSDT")

    # Initial snapshot
    bids1 = [(50000.0, 1.0), (49990.0, 2.0)]
    asks1 = [(50010.0, 1.5), (50020.0, 2.5)]
    success1 = ob.apply_snapshot(bids1, asks1, update_id=100, timestamp_ms=1000, seq=100050)
    assert success1 is True
    assert ob.status == OrderBookSyncStatus.SYNCHRONIZED
    assert ob.last_update_id == 100
    assert ob.last_seq == 100050
    assert len(ob.bids) == 2

    # Second snapshot (re-pushed or fresh recovery snapshot) with completely different levels
    bids2 = [(48000.0, 5.0)]
    asks2 = [(48100.0, 4.0)]
    success2 = ob.apply_snapshot(bids2, asks2, update_id=200, timestamp_ms=2000, seq=200080)
    assert success2 is True
    assert ob.status == OrderBookSyncStatus.SYNCHRONIZED
    assert ob.last_update_id == 200
    assert ob.last_seq == 200080
    assert len(ob.bids) == 1
    assert 50000.0 not in ob.bids
    assert 48000.0 in ob.bids


def test_bybit_delta_updates_and_zero_quantity_deletions() -> None:
    """Verify Bybit delta updates: level modification, addition, and zero-size removal."""
    ob = BybitLocalOrderBook("BYBIT:BTCUSDT", "BTCUSDT")
    ob.apply_snapshot([(50000.0, 1.0), (49990.0, 2.0)], [(50010.0, 1.0)], update_id=10, timestamp_ms=1000)

    # Delta: updates 50000 to 3.0, adds 49980 at 4.0, deletes 49990 (size 0.0), deletes non-existent 49900 (size 0.0)
    delta_bids = [(50000.0, 3.0), (49980.0, 4.0), (49990.0, 0.0), (49900.0, 0.0)]
    delta_asks = [(50010.0, 2.5), (50020.0, 1.2)]

    success = ob.apply_delta(delta_bids, delta_asks, update_id=11, timestamp_ms=1100, seq=1050)
    assert success is True
    assert ob.last_update_id == 11
    assert ob.bids[50000.0] == 3.0
    assert ob.bids[49980.0] == 4.0
    assert 49990.0 not in ob.bids
    assert 49900.0 not in ob.bids
    assert ob.asks[50010.0] == 2.5
    assert ob.asks[50020.0] == 1.2


def test_bybit_service_restart_signal_u_equals_1_snapshot_replacement() -> None:
    """Verify that update_id=1 triggers Bybit matching engine restart snapshot overwrite."""
    ob = BybitLocalOrderBook("BYBIT:BTCUSDT", "BTCUSDT")
    ob.apply_snapshot([(50000.0, 1.0), (49990.0, 2.0)], [(50010.0, 1.0), (50020.0, 3.0)], update_id=500, timestamp_ms=1000)
    assert ob.status == OrderBookSyncStatus.SYNCHRONIZED
    assert len(ob.bids) == 2
    assert len(ob.asks) == 2

    # Incoming restart snapshot with u=1 immediately overwrites local book
    restart_bids = [(50005.0, 4.0)]
    restart_asks = [(50015.0, 2.5)]
    success = ob.apply_delta(restart_bids, restart_asks, update_id=1, timestamp_ms=2000)

    assert success is True
    assert ob.status == OrderBookSyncStatus.SYNCHRONIZED
    assert ob.last_update_id == 1
    # Old levels removed
    assert 50000.0 not in ob.bids
    assert 49990.0 not in ob.bids
    assert 50010.0 not in ob.asks
    assert 50020.0 not in ob.asks
    # New levels populated
    assert ob.bids[50005.0] == 4.0
    assert ob.asks[50015.0] == 2.5


def test_bybit_service_restart_subsequent_deltas() -> None:
    """Verify that normal deltas apply sequentially following a u=1 restart snapshot."""
    ob = BybitLocalOrderBook("BYBIT:BTCUSDT", "BTCUSDT")
    ob.apply_snapshot([(50000.0, 1.0)], [(50010.0, 1.0)], update_id=500, timestamp_ms=1000)

    # u=1 restart
    assert ob.apply_delta([(50005.0, 4.0)], [(50015.0, 2.0)], update_id=1, timestamp_ms=2000) is True

    # Subsequent delta with u=2 applies cleanly
    success_2 = ob.apply_delta([(50005.0, 6.0)], [(50015.0, 0.0)], update_id=2, timestamp_ms=2100)
    assert success_2 is True
    assert ob.last_update_id == 2
    assert ob.bids[50005.0] == 6.0
    assert 50015.0 not in ob.asks

    # Duplicate delta (u <= 2) is rejected
    assert ob.apply_delta([(50005.0, 7.0)], [], update_id=2, timestamp_ms=2200) is False

    # Subsequent valid delta with u=3 succeeds
    assert ob.apply_delta([(50005.0, 7.0)], [], update_id=3, timestamp_ms=2300) is True
    assert ob.last_update_id == 3
    assert ob.bids[50005.0] == 7.0


def test_bybit_service_restart_crossed_book_rejection() -> None:
    """Verify that a u=1 restart snapshot producing a crossed book marks book INVALID."""
    ob = BybitLocalOrderBook("BYBIT:BTCUSDT", "BTCUSDT")
    ob.apply_snapshot([(50000.0, 1.0)], [(50010.0, 1.0)], update_id=500, timestamp_ms=1000)

    # u=1 restart with crossed prices (bid 50020 >= ask 50010)
    crossed_bids = [(50020.0, 1.0)]
    crossed_asks = [(50010.0, 1.0)]
    success = ob.apply_delta(crossed_bids, crossed_asks, update_id=1, timestamp_ms=2000)

    assert success is False
    assert ob.status == OrderBookSyncStatus.INVALID
    assert ob.crossed_count == 1


def test_bybit_monotonic_update_id_and_duplicate_rejection() -> None:
    """Verify that Bybit delta with u <= last_u is rejected as duplicate or out of order."""
    ob = BybitLocalOrderBook("BYBIT:BTCUSDT", "BTCUSDT")
    ob.apply_snapshot([(50000.0, 1.0)], [(50010.0, 1.0)], update_id=100, timestamp_ms=1000)

    # Incoming delta with u=100 (duplicate) or u=99 (out of order) must be rejected
    assert ob.apply_delta([(50000.0, 2.0)], [], update_id=100, timestamp_ms=1100) is False
    assert ob.apply_delta([(50000.0, 2.0)], [], update_id=99, timestamp_ms=1100) is False
    assert ob.status == OrderBookSyncStatus.SYNCHRONIZED

    # Normal increment succeeds
    assert ob.apply_delta([(50000.0, 2.0)], [], update_id=101, timestamp_ms=1200) is True


def test_bybit_cross_sequence_non_consecutive_jumps() -> None:
    """Verify that Bybit cross-engine sequence (seq) jumps arbitrarily without error."""
    ob = BybitLocalOrderBook("BYBIT:BTCUSDT", "BTCUSDT")
    ob.apply_snapshot([(50000.0, 1.0)], [(50010.0, 1.0)], update_id=10, timestamp_ms=1000, seq=1000)

    # Seq jumps from 1000 to 1542 (matching engine events on other symbols/channels advance seq)
    success = ob.apply_delta([(50000.0, 1.5)], [], update_id=11, timestamp_ms=1100, seq=1542)
    assert success is True
    assert ob.last_seq == 1542
    assert ob.last_update_id == 11


# ============================================================================
# 2. AsterDEX Futures Specific Synchronization Tests
# ============================================================================


def test_aster_buffering_and_snapshot_bridging_success() -> None:
    """Verify AsterDEX depthUpdate event buffering and snapshot alignment."""
    ob = AsterLocalOrderBook("ASTER:BTCUSDT", "BTCUSDT")
    assert ob.is_buffering is True
    assert ob.status == OrderBookSyncStatus.INITIALIZING

    # 1. Buffer WebSocket events before snapshot arrives
    ob.buffer_event({
        "e": "depthUpdate", "E": 1001, "s": "BTCUSDT", "U": 90, "u": 95, "pu": 89,
        "b": [["50000.0", "1.0"]], "a": []
    })
    ob.buffer_event({
        "e": "depthUpdate", "E": 1002, "s": "BTCUSDT", "U": 96, "u": 105, "pu": 95,
        "b": [["50000.0", "2.0"]], "a": [["50010.0", "1.5"]]
    })
    ob.buffer_event({
        "e": "depthUpdate", "E": 1003, "s": "BTCUSDT", "U": 106, "u": 110, "pu": 105,
        "b": [["49990.0", "3.0"]], "a": []
    })

    # 2. REST snapshot arrives with lastUpdateId = 100
    # Event 1 (u=95) is < 100 and must be dropped.
    # Event 2 (U=96 <= 100 <= u=105) bridges the snapshot.
    # Event 3 (pu=105 == previous u=105) plays back cleanly.
    snapshot_bids = [(50000.0, 1.0), (49980.0, 5.0)]
    snapshot_asks = [(50010.0, 2.0)]
    success = ob.apply_snapshot_with_buffer(snapshot_bids, snapshot_asks, snapshot_last_update_id=100, timestamp_ms=1000)

    assert success is True
    assert ob.status == OrderBookSyncStatus.SYNCHRONIZED
    assert ob.is_buffering is False
    assert ob.last_update_id == 110
    # Verifies that Event 2 updated 50000 to 2.0 and Event 3 added 49990 at 3.0
    assert ob.bids[50000.0] == 2.0
    assert ob.bids[49990.0] == 3.0
    assert ob.bids[49980.0] == 5.0


def test_aster_buffering_gap_triggers_resync() -> None:
    """Verify that buffer failing to bridge snapshot triggers RESYNCING."""
    ob = AsterLocalOrderBook("ASTER:BTCUSDT", "BTCUSDT")

    # Buffered event has U=110, but snapshot lastUpdateId = 100 (gap between 100 and 110)
    ob.buffer_event({
        "e": "depthUpdate", "E": 1002, "s": "BTCUSDT", "U": 110, "u": 115, "pu": 109,
        "b": [["50000.0", "2.0"]], "a": []
    })

    snapshot_bids = [(50000.0, 1.0)]
    snapshot_asks = [(50010.0, 1.0)]
    success = ob.apply_snapshot_with_buffer(snapshot_bids, snapshot_asks, snapshot_last_update_id=100, timestamp_ms=1000)

    assert success is False
    assert ob.status == OrderBookSyncStatus.RESYNCING
    assert ob.is_buffering is True
    assert ob.gap_count == 1


def test_aster_subsequent_event_pu_continuity_and_mismatch() -> None:
    """Verify that live depth updates require pu == last_u, and mismatch triggers RESYNCING."""
    ob = AsterLocalOrderBook("ASTER:BTCUSDT", "BTCUSDT")
    # Initial synchronized state at update_id = 100
    ob.apply_snapshot_with_buffer([(50000.0, 1.0)], [(50010.0, 1.0)], snapshot_last_update_id=100, timestamp_ms=1000)
    ob.status = OrderBookSyncStatus.SYNCHRONIZED
    ob.is_buffering = False

    # Valid next event: pu = 100, u = 105
    event1 = {
        "e": "depthUpdate", "E": 1001, "s": "BTCUSDT", "U": 101, "u": 105, "pu": 100,
        "b": [["50000.0", "3.0"]], "a": []
    }
    assert ob.apply_delta_event(event1) is True
    assert ob.last_update_id == 105
    assert ob.bids[50000.0] == 3.0

    # Sequence mismatch: incoming pu = 108 instead of 105 (missed packet 106-107)
    event2 = {
        "e": "depthUpdate", "E": 1002, "s": "BTCUSDT", "U": 109, "u": 112, "pu": 108,
        "b": [["50000.0", "4.0"]], "a": []
    }
    assert ob.apply_delta_event(event2) is False
    assert ob.status == OrderBookSyncStatus.RESYNCING
    assert ob.is_buffering is True
    assert ob.gap_count == 1


def test_aster_zero_size_removal_and_missing_level_safety() -> None:
    """Verify AsterDEX absolute quantity updates and safe deletion of non-existent levels."""
    ob = AsterLocalOrderBook("ASTER:BTCUSDT", "BTCUSDT")
    ob.apply_snapshot_with_buffer([(50000.0, 1.0), (49990.0, 2.0)], [(50010.0, 1.0)], snapshot_last_update_id=100, timestamp_ms=1000)
    ob.status = OrderBookSyncStatus.SYNCHRONIZED
    ob.is_buffering = False

    # Delete existing 49990, delete non-existent 49800
    event = {
        "e": "depthUpdate", "E": 1001, "s": "BTCUSDT", "U": 101, "u": 105, "pu": 100,
        "b": [["49990.0", "0.0"], ["49800.0", "0.0"]], "a": [["50010.0", "0.0"], ["50020.0", "3.5"]]
    }
    assert ob.apply_delta_event(event) is True
    assert 49990.0 not in ob.bids
    assert 49800.0 not in ob.bids
    assert 50010.0 not in ob.asks
    assert ob.asks[50020.0] == 3.5
