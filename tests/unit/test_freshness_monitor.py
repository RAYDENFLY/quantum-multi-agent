"""Unit tests for MarketDataFreshnessMonitor and monotonic clock tracking."""

import time
import pytest

from quantum.domain.enums import OrderBookSyncStatus
from quantum.exchanges.freshness import MarketDataFreshnessMonitor


def test_freshness_monitor_heartbeat_and_transitions() -> None:
    """Verify heartbeat recording and degradation to STALE and INVALID."""
    transitions = []

    def on_stale(instrument_id: str, status: OrderBookSyncStatus) -> None:
        transitions.append((instrument_id, status))

    monitor = MarketDataFreshnessMonitor(
        stale_threshold_s=2.0,
        invalid_threshold_s=5.0,
        on_stale_callback=on_stale,
    )

    inst = "BYBIT:BTCUSDT"

    # 1. Unseen instrument
    assert monitor.check_instrument(inst) == OrderBookSyncStatus.INITIALIZING

    # 2. Record heartbeat
    monitor.record_heartbeat(inst)
    assert monitor.check_instrument(inst) == OrderBookSyncStatus.SYNCHRONIZED

    # 3. Simulate elapsed time past stale threshold
    monitor._last_seen_monotonic[inst] = time.monotonic() - 2.5
    status = monitor.check_instrument(inst)
    assert status == OrderBookSyncStatus.STALE
    assert (inst, OrderBookSyncStatus.STALE) in transitions

    # 4. Simulate elapsed time past invalid threshold
    monitor._last_seen_monotonic[inst] = time.monotonic() - 5.5
    status = monitor.check_instrument(inst)
    assert status == OrderBookSyncStatus.INVALID
    assert (inst, OrderBookSyncStatus.INVALID) in transitions

    # 5. Recovery on new heartbeat
    monitor.record_heartbeat(inst)
    assert monitor.check_instrument(inst) == OrderBookSyncStatus.SYNCHRONIZED
    assert (inst, OrderBookSyncStatus.SYNCHRONIZED) in transitions


def test_freshness_monitor_check_all_and_removal() -> None:
    """Verify check_all multi-symbol evaluation and instrument removal."""
    monitor = MarketDataFreshnessMonitor(stale_threshold_s=1.0, invalid_threshold_s=3.0)

    monitor.record_heartbeat("BYBIT:BTCUSDT")
    monitor.record_heartbeat("ASTER:ETHUSDT")

    statuses = monitor.check_all()
    assert statuses["BYBIT:BTCUSDT"] == OrderBookSyncStatus.SYNCHRONIZED
    assert statuses["ASTER:ETHUSDT"] == OrderBookSyncStatus.SYNCHRONIZED

    monitor.remove_instrument("ASTER:ETHUSDT")
    statuses_after = monitor.check_all()
    assert "ASTER:ETHUSDT" not in statuses_after
    assert "BYBIT:BTCUSDT" in statuses_after
