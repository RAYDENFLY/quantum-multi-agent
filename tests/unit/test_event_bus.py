"""Unit tests for asynchronous priority EventBus.

Tests priority ordering, bounded saturation, backpressure, slow consumer isolation,
starvation prevention, ring-buffer eviction, and graceful shutdown.
"""

import asyncio
import time
from typing import List
import pytest

from quantum.core.event_bus import EventBus, QueueSaturationError
from quantum.domain.enums import EventPriority
from quantum.domain.events import MessageEnvelope


def make_envelope(topic: str, priority: EventPriority, key: str, run_id: str = "run_1") -> MessageEnvelope:
    return MessageEnvelope(
        message_id=f"msg_{key}",
        pipeline_run_id=run_id,
        idempotency_key=key,
        source="TEST",
        topic=topic,
        priority=priority,
        created_at_ms=1000,
        snapshot_timestamp_ms=1000,
        model_version="test_v1",
        payload={"sample": "data"},
    )


@pytest.mark.asyncio
async def test_event_bus_start_stop_lifecycle() -> None:
    bus = EventBus()
    await bus.start()
    assert bus.is_running
    await bus.stop()
    assert not bus.is_running


@pytest.mark.asyncio
async def test_event_bus_priority_ordering() -> None:
    bus = EventBus()
    received_order: List[EventPriority] = []
    done_event = asyncio.Event()

    async def on_event(msg: MessageEnvelope) -> None:
        received_order.append(msg.priority)
        if len(received_order) == 3:
            done_event.set()

    bus.subscribe("test.*", on_event)

    # Publish in reverse order: P2, then P1, then P0 before starting the bus workers
    await bus.publish(make_envelope("test.telemetry", EventPriority.P2, "key_p2"))
    await bus.publish(make_envelope("test.pipeline", EventPriority.P1, "key_p1"))
    await bus.publish(make_envelope("test.critical", EventPriority.P0, "key_p0"))

    await bus.start()
    await asyncio.wait_for(done_event.wait(), timeout=2.0)
    await bus.stop()

    assert received_order == [EventPriority.P0, EventPriority.P1, EventPriority.P2]


@pytest.mark.asyncio
async def test_event_bus_deduplication() -> None:
    bus = EventBus()
    received: List[str] = []
    done_event = asyncio.Event()

    async def on_event(msg: MessageEnvelope) -> None:
        received.append(msg.idempotency_key)
        if len(received) == 1:
            done_event.set()

    bus.subscribe("test.dedup", on_event)
    await bus.start()

    pub1 = await bus.publish(make_envelope("test.dedup", EventPriority.P1, "duplicate_key_1"))
    pub2 = await bus.publish(make_envelope("test.dedup", EventPriority.P1, "duplicate_key_1"))

    assert pub1 is True
    assert pub2 is False  # Deduplicated

    await asyncio.wait_for(done_event.wait(), timeout=1.0)
    await asyncio.sleep(0.05)
    await bus.stop()

    assert len(received) == 1
    assert received[0] == "duplicate_key_1"


@pytest.mark.asyncio
async def test_event_bus_error_isolation() -> None:
    bus = EventBus()
    isolated_subscriber_called = asyncio.Event()

    async def failing_subscriber(msg: MessageEnvelope) -> None:
        raise RuntimeError("Simulated subscriber failure")

    async def healthy_subscriber(msg: MessageEnvelope) -> None:
        isolated_subscriber_called.set()

    bus.subscribe("test.error", failing_subscriber)
    bus.subscribe("test.error", healthy_subscriber)

    await bus.start()
    await bus.publish(make_envelope("test.error", EventPriority.P0, "err_key_1"))

    await asyncio.wait_for(isolated_subscriber_called.wait(), timeout=1.0)
    await bus.stop()

    assert isolated_subscriber_called.is_set()


@pytest.mark.asyncio
async def test_event_bus_wildcard_topic_matching() -> None:
    bus = EventBus()
    matched_topics: List[str] = []
    done_event = asyncio.Event()

    async def handler(msg: MessageEnvelope) -> None:
        matched_topics.append(msg.topic)
        if len(matched_topics) == 2:
            done_event.set()

    bus.subscribe("market.*", handler)
    await bus.start()

    await bus.publish(make_envelope("market.bybit.btc", EventPriority.P1, "m1"))
    await bus.publish(make_envelope("market.asterdex.eth", EventPriority.P1, "m2"))
    await bus.publish(make_envelope("order.fill", EventPriority.P1, "m3"))

    await asyncio.wait_for(done_event.wait(), timeout=1.0)
    await bus.stop()

    assert "market.bybit.btc" in matched_topics
    assert "market.asterdex.eth" in matched_topics
    assert "order.fill" not in matched_topics


@pytest.mark.asyncio
async def test_event_bus_p0_processed_while_p2_saturated() -> None:
    # Small capacity P2 queue to test saturation
    bus = EventBus(capacity_p0=50, capacity_p1=50, capacity_p2=5)
    p0_delivered = asyncio.Event()

    async def on_critical(msg: MessageEnvelope) -> None:
        if msg.priority == EventPriority.P0:
            p0_delivered.set()

    bus.subscribe("critical.*", on_critical)
    await bus.start()

    # Flood P2 beyond its capacity of 5
    for i in range(15):
        await bus.publish(make_envelope("telemetry.tick", EventPriority.P2, f"p2_flood_{i}"))

    # Publish P0 message; it must be dispatched without delay despite P2 overflow
    await bus.publish(make_envelope("critical.risk", EventPriority.P0, "p0_vital"))

    await asyncio.wait_for(p0_delivered.wait(), timeout=1.0)
    await bus.stop()

    assert p0_delivered.is_set()


@pytest.mark.asyncio
async def test_event_bus_slow_p2_subscriber_protection() -> None:
    # Test that a slow subscriber with timeout does not lock up dispatch
    bus = EventBus(subscriber_timeout_s=0.05)
    fast_subscriber_called = asyncio.Event()

    async def slow_subscriber(msg: MessageEnvelope) -> None:
        await asyncio.sleep(0.5)  # Exceeds 0.05s timeout

    async def fast_subscriber(msg: MessageEnvelope) -> None:
        fast_subscriber_called.set()

    bus.subscribe("test.slow", slow_subscriber)
    bus.subscribe("test.fast", fast_subscriber)
    await bus.start()

    await bus.publish(make_envelope("test.slow", EventPriority.P2, "slow_msg"))
    await bus.publish(make_envelope("test.fast", EventPriority.P0, "fast_msg"))

    # Fast subscriber on P0 must finish quickly despite slow subscriber on P2
    await asyncio.wait_for(fast_subscriber_called.wait(), timeout=0.2)
    await bus.stop()

    assert fast_subscriber_called.is_set()


@pytest.mark.asyncio
async def test_event_bus_queue_saturation_raises_error() -> None:
    # Bounded queue of capacity 2
    bus = EventBus(capacity_p0=2)

    await bus.publish(make_envelope("risk.1", EventPriority.P0, "k1"))
    await bus.publish(make_envelope("risk.2", EventPriority.P0, "k2"))

    # Third publish into full P0 queue raises QueueSaturationError
    with pytest.raises(QueueSaturationError, match="Queue saturation in lane P0"):
        await bus.publish(make_envelope("risk.3", EventPriority.P0, "k3"))


@pytest.mark.asyncio
async def test_event_bus_starvation_prevention() -> None:
    # Test anti-starvation: sustained P0 burst yields a turn to P1
    bus = EventBus(capacity_p0=100, capacity_p1=50)
    dispatch_order: List[EventPriority] = []
    p1_dispatched = asyncio.Event()

    async def tracker(msg: MessageEnvelope) -> None:
        dispatch_order.append(msg.priority)
        if msg.priority == EventPriority.P1:
            p1_dispatched.set()

    bus.subscribe("starve.*", tracker)

    # Enqueue 1 P1 message, then a large burst of 20 P0 messages before starting workers
    await bus.publish(make_envelope("starve.pipe", EventPriority.P1, "p1_msg"))
    for i in range(20):
        await bus.publish(make_envelope("starve.crit", EventPriority.P0, f"p0_{i}"))

    await bus.start()
    # P1 must be dispatched within the first 10 messages due to MAX_CONSECUTIVE_P0=8 quota
    await asyncio.wait_for(p1_dispatched.wait(), timeout=2.0)
    await bus.stop()

    assert EventPriority.P1 in dispatch_order
    p1_index = dispatch_order.index(EventPriority.P1)
    assert p1_index <= 9  # Dispatched at or before 9th item, proving anti-starvation!


@pytest.mark.asyncio
async def test_event_bus_shutdown_with_pending_events() -> None:
    bus = EventBus()
    processed_count = 0

    async def handler(msg: MessageEnvelope) -> None:
        nonlocal processed_count
        processed_count += 1

    bus.subscribe("shutdown.*", handler)

    # Publish messages without starting workers
    await bus.publish(make_envelope("shutdown.p0", EventPriority.P0, "k_p0"))
    await bus.publish(make_envelope("shutdown.p1", EventPriority.P1, "k_p1"))

    # Calling stop(drain_pending=True) should drain pending P0/P1 messages before stopping
    await bus.stop(drain_pending=True, timeout_s=1.0)
    assert processed_count == 2


@pytest.mark.asyncio
async def test_event_bus_sync_blocking_callback_isolation() -> None:
    bus = EventBus(subscriber_timeout_s=1.0)
    loop = asyncio.get_running_loop()
    sync_started = asyncio.Event()
    sync_finished = False
    p0_delivery_time_ms = 0.0
    p0_event = asyncio.Event()

    # Synchronous blocking callback (runs on worker thread via asyncio.to_thread)
    def blocking_sync_subscriber(msg: MessageEnvelope) -> None:
        nonlocal sync_finished
        # Signal that the worker thread has started execution
        loop.call_soon_threadsafe(sync_started.set)
        time.sleep(0.3)  # Heavy blocking sleep on OS thread
        sync_finished = True

    async def p0_critical_subscriber(msg: MessageEnvelope) -> None:
        nonlocal p0_delivery_time_ms
        p0_delivery_time_ms = (time.perf_counter() - publish_time) * 1000.0
        p0_event.set()

    bus.subscribe("telemetry.tick", blocking_sync_subscriber)
    bus.subscribe("critical.risk", p0_critical_subscriber)
    await bus.start()

    # 1. Publish P2 event with blocking sync subscriber and wait for it to enter time.sleep
    await bus.publish(make_envelope("telemetry.tick", EventPriority.P2, "p2_sync_block"))
    await asyncio.wait_for(sync_started.wait(), timeout=1.0)

    # 2. While the sync subscriber is actively sleeping in its background thread,
    # publish P0 critical event
    publish_time = time.perf_counter()
    await bus.publish(make_envelope("critical.risk", EventPriority.P0, "p0_fast"))

    # 3. The P0 event must be received and processed promptly (< 80ms)
    # well before the 300ms sleep finishes, proving the event loop was not blocked!
    await asyncio.wait_for(p0_event.wait(), timeout=0.15)
    p0_latency = p0_delivery_time_ms

    # Wait for the background thread to finish cleanly
    await bus.stop(timeout_s=1.0)

    assert p0_event.is_set()
    assert p0_latency < 80.0
    assert sync_finished is True


@pytest.mark.asyncio
async def test_event_bus_sync_callback_normal_execution() -> None:
    bus = EventBus()
    loop = asyncio.get_running_loop()
    received_keys: List[str] = []
    sync_done = asyncio.Event()

    # Standard synchronous callback
    def regular_sync_handler(msg: MessageEnvelope) -> None:
        received_keys.append(msg.idempotency_key)
        # Thread-safe event setting for asyncio
        loop.call_soon_threadsafe(sync_done.set)

    bus.subscribe("pipeline.candidate", regular_sync_handler)
    await bus.start()

    await bus.publish(make_envelope("pipeline.candidate", EventPriority.P1, "sync_key_1"))
    await asyncio.wait_for(sync_done.wait(), timeout=1.0)
    await bus.stop()

    assert received_keys == ["sync_key_1"]


@pytest.mark.asyncio
async def test_event_bus_sustained_p2_production_and_bounded_concurrency() -> None:
    # Bounded P2 capacity of 50 and bounded background concurrency of 8
    bus = EventBus(capacity_p2=50, max_p2_concurrency=8, subscriber_timeout_s=1.0)
    p2_processed = 0
    max_active_tasks_observed = 0
    p0_event = asyncio.Event()
    p0_delivery_time_ms = 0.0

    async def slow_p2_handler(msg: MessageEnvelope) -> None:
        nonlocal p2_processed, max_active_tasks_observed
        active = bus.stats()["active_p2_tasks_count"]
        if active > max_active_tasks_observed:
            max_active_tasks_observed = active
        p2_processed += 1
        await asyncio.sleep(0.04)

    async def p0_critical_handler(msg: MessageEnvelope) -> None:
        nonlocal p0_delivery_time_ms
        p0_delivery_time_ms = (time.perf_counter() - publish_time) * 1000.0
        p0_event.set()

    bus.subscribe("telemetry.*", slow_p2_handler)
    bus.subscribe("critical.*", p0_critical_handler)
    await bus.start()

    # Rapidly publish 200 P2 telemetry events (exceeds queue capacity of 50)
    for i in range(200):
        await bus.publish(make_envelope("telemetry.tick", EventPriority.P2, f"p2_stress_{i}"))

    # Verify active tasks are strictly bounded
    await asyncio.sleep(0.08)
    assert len(bus._background_tasks) <= 8
    assert max_active_tasks_observed <= 8

    # While P2 is saturated and backlog is draining, publish a P0 critical message
    publish_time = time.perf_counter()
    await bus.publish(make_envelope("critical.risk", EventPriority.P0, "p0_vital_during_p2_stress"))

    # P0 must be dispatched and processed promptly (< 60ms) despite P2 saturation
    await asyncio.wait_for(p0_event.wait(), timeout=0.15)
    assert p0_delivery_time_ms < 60.0

    # Ring-buffer eviction must have engaged for the overflow telemetry
    stats = bus.stats()
    assert stats["dropped_count"] > 0
    assert stats["active_p2_tasks_count"] <= 8

    # Graceful shutdown must clean up all tasks safely without hanging or throwing
    await bus.stop(timeout_s=0.5)
    assert not bus.is_running
    assert len(bus._background_tasks) == 0


