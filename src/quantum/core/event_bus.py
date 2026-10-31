"""Asynchronous priority-lane pub/sub event bus with deduplication, anti-starvation, and backpressure.

Scheduling & Backpressure Semantics:
1. Priority Lanes:
   - P0 (Critical): Risk decisions, circuit breakers, emergency halts (capacity: 200).
   - P1 (Pipeline): Candidate evaluations, trade proposals, stage events (capacity: 1,000).
   - P2 (Telemetry): Ticker ticks, order book snapshots, scan updates (capacity: 2,500).

2. Anti-Starvation Quota Scheduling:
   - Normal order: P0 drained before P1, P1 before P2.
   - Starvation prevention: After 8 consecutive P0 dispatches, if P1 has pending items,
     P1 receives a guaranteed slot. After 16 consecutive P1 dispatches, if P2 has pending items,
     P2 receives a guaranteed slot. This prevents starvation during sustained high-priority bursts.

3. Backpressure & Overflow:
   - P0 / P1: Strict backpressure. If saturated, raises QueueSaturationError. Never silently drops.
   - P2: Loss-tolerant ring-buffer eviction. When full, oldest item is evicted to accommodate new ticks.

4. Subscriber Isolation & Slow Consumer Protection:
   - Subscribers are executed concurrently with error isolation.
   - Each subscriber call is bounded by a 2.0s execution timeout so a slow P2 consumer cannot
     block high-priority P0/P1 dispatch.
"""

import asyncio
from collections import deque
import fnmatch
import inspect
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set

from quantum.core.logging import get_logger
from quantum.domain.enums import EventPriority
from quantum.domain.events import MessageEnvelope

logger = get_logger("core.event_bus")

# Bounded queue capacities per lane
CAPACITY_P0 = 200    # Critical: Risk decisions, emergency cancellations
CAPACITY_P1 = 1000   # Pipeline: Stage outputs, candidate proposals
CAPACITY_P2 = 2500   # Telemetry: Ticker updates, scan telemetry

# Anti-starvation quotas
MAX_CONSECUTIVE_P0 = 8
MAX_CONSECUTIVE_P1 = 16

HandlerFunc = Callable[[MessageEnvelope], Any]


class QueueSaturationError(Exception):
    """Raised when a non-telemetry priority lane exceeds its bounded capacity."""
    pass


class EventBus:
    """Asynchronous priority-lane pub/sub event bus with deduplication and error isolation."""

    def __init__(
        self,
        capacity_p0: int = CAPACITY_P0,
        capacity_p1: int = CAPACITY_P1,
        capacity_p2: int = CAPACITY_P2,
        dedup_window_size: int = 5000,
        subscriber_timeout_s: float = 2.0,
        max_p2_concurrency: int = 25,
    ) -> None:
        self.capacity_p0 = capacity_p0
        self.capacity_p1 = capacity_p1
        self.capacity_p2 = capacity_p2
        self.subscriber_timeout_s = subscriber_timeout_s
        self.max_p2_concurrency = max_p2_concurrency

        # Priority queues
        self._queue_p0: asyncio.Queue[MessageEnvelope] = asyncio.Queue(maxsize=capacity_p0)
        self._queue_p1: asyncio.Queue[MessageEnvelope] = asyncio.Queue(maxsize=capacity_p1)
        self._queue_p2: asyncio.Queue[MessageEnvelope] = asyncio.Queue(maxsize=capacity_p2)

        # Anti-starvation counters
        self._consecutive_p0 = 0
        self._consecutive_p1 = 0

        # Topic subscribers: topic_pattern -> list of handler callables
        self._subscribers: Dict[str, List[HandlerFunc]] = {}
        self._all_handlers: Set[HandlerFunc] = set()

        # Idempotency deduplication cache
        self._dedup_cache: deque[str] = deque(maxlen=dedup_window_size)
        self._dedup_set: Set[str] = set()

        # Lifecycle
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._background_tasks: Set[asyncio.Task] = set()
        self._published_count = 0
        self._processed_count = 0
        self._dropped_count = 0

    @property
    def is_running(self) -> bool:
        """Return True if background dispatch worker is active."""
        return self._running

    def subscribe(self, topic_pattern: str, handler: HandlerFunc) -> None:
        """Register an async handler callable for a specific topic or wildcard pattern."""
        if topic_pattern not in self._subscribers:
            self._subscribers[topic_pattern] = []

        if handler not in self._subscribers[topic_pattern]:
            self._subscribers[topic_pattern].append(handler)
            self._all_handlers.add(handler)
            logger.debug("Subscribed handler %s to topic pattern '%s'", getattr(handler, "__name__", str(handler)), topic_pattern)

    def unsubscribe(self, topic: str, handler: HandlerFunc) -> None:
        """Unregister a handler from a topic pattern."""
        if topic in self._subscribers and handler in self._subscribers[topic]:
            self._subscribers[topic].remove(handler)
            if not self._subscribers[topic]:
                del self._subscribers[topic]
            logger.debug("Unsubscribed handler %s from topic '%s'", getattr(handler, "__name__", str(handler)), topic)

    async def publish(self, envelope: MessageEnvelope) -> bool:
        """Publish an envelope to the appropriate priority lane.

        Returns True if enqueued, or False if discarded as duplicate.
        Raises QueueSaturationError if critical or pipeline queue is full.
        """
        # 1. Deduplication check
        if envelope.idempotency_key:
            if envelope.idempotency_key in self._dedup_set:
                logger.debug("Dropping duplicate event key: %s", envelope.idempotency_key)
                return False

            if len(self._dedup_cache) >= self._dedup_cache.maxlen:
                oldest_key = self._dedup_cache.popleft()
                self._dedup_set.discard(oldest_key)

            self._dedup_cache.append(envelope.idempotency_key)
            self._dedup_set.add(envelope.idempotency_key)

        # 2. Select destination lane by priority
        target_queue: asyncio.Queue[MessageEnvelope]
        priority = envelope.priority

        if priority == EventPriority.P0:
            target_queue = self._queue_p0
        elif priority == EventPriority.P1:
            target_queue = self._queue_p1
        else:
            target_queue = self._queue_p2

        # 3. Enqueue with lane-specific saturation handling
        try:
            target_queue.put_nowait(envelope)
            self._published_count += 1
            return True
        except asyncio.QueueFull:
            if priority == EventPriority.P2:
                # Telemetry is loss-tolerant: drop oldest item and insert new
                try:
                    self._queue_p2.get_nowait()
                    self._queue_p2.task_done()
                    self._dropped_count += 1
                except asyncio.QueueEmpty:
                    pass
                try:
                    self._queue_p2.put_nowait(envelope)
                    self._published_count += 1
                    return True
                except asyncio.QueueFull:
                    self._dropped_count += 1
                    logger.warning("P2 telemetry queue completely saturated; dropped message on topic %s", envelope.topic)
                    return False
            else:
                # Critical / Pipeline queues do not silently discard
                error_msg = f"Queue saturation in lane {priority.name} (topic: {envelope.topic})"
                logger.error(error_msg)
                raise QueueSaturationError(error_msg)

    async def start(self) -> None:
        """Start the background dispatch worker loop."""
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._dispatch_loop())
        logger.info("EventBus started with P0, P1, and P2 priority dispatch lanes")

    async def stop(self, drain_pending: bool = True, timeout_s: float = 2.0) -> None:
        """Gracefully drain remaining critical/pipeline messages and stop dispatch loop."""
        if drain_pending:
            # Drain remaining P0 and P1 queues up to timeout
            start_drain = asyncio.get_event_loop().time()
            while (not self._queue_p0.empty() or not self._queue_p1.empty()) and (asyncio.get_event_loop().time() - start_drain < timeout_s):
                try:
                    if not self._queue_p0.empty():
                        env = self._queue_p0.get_nowait()
                        await self._deliver(env)
                        self._queue_p0.task_done()
                        self._processed_count += 1
                    elif not self._queue_p1.empty():
                        env = self._queue_p1.get_nowait()
                        await self._deliver(env)
                        self._queue_p1.task_done()
                        self._processed_count += 1
                except Exception:
                    pass

        if not self._running:
            return
        self._running = False

        # Drain active background tasks
        if self._background_tasks:
            pending = [t for t in self._background_tasks if not t.done()]
            if pending:
                try:
                    await asyncio.wait(pending, timeout=timeout_s)
                except Exception:
                    pass
                for t in pending:
                    if not t.done():
                        t.cancel()

        # Cancel worker loop
        if self._worker_task is not None:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None

        logger.info(
            "EventBus stopped (Published: %d, Processed: %d, Dropped: %d)",
            self._published_count,
            self._processed_count,
            self._dropped_count,
        )

    async def _dispatch_loop(self) -> None:
        """Prioritized dispatch loop draining P0, P1, and P2 with anti-starvation and bounded P2 concurrency."""
        while self._running:
            envelope: Optional[MessageEnvelope] = None
            queue_used: Optional[asyncio.Queue[MessageEnvelope]] = None

            # Check anti-starvation condition for P1
            if self._consecutive_p0 >= MAX_CONSECUTIVE_P0 and not self._queue_p1.empty():
                try:
                    envelope = self._queue_p1.get_nowait()
                    queue_used = self._queue_p1
                    self._consecutive_p0 = 0
                    self._consecutive_p1 += 1
                except asyncio.QueueEmpty:
                    pass

            # Check anti-starvation condition for P2 (only if under max P2 background concurrency)
            if (
                envelope is None
                and self._consecutive_p1 >= MAX_CONSECUTIVE_P1
                and not self._queue_p2.empty()
                and len(self._background_tasks) < self.max_p2_concurrency
            ):
                try:
                    envelope = self._queue_p2.get_nowait()
                    queue_used = self._queue_p2
                    self._consecutive_p1 = 0
                except asyncio.QueueEmpty:
                    pass

            # Normal priority selection if quota didn't select an envelope
            if envelope is None:
                # 1. P0 (Highest priority)
                try:
                    envelope = self._queue_p0.get_nowait()
                    queue_used = self._queue_p0
                    self._consecutive_p0 += 1
                except asyncio.QueueEmpty:
                    # 2. P1 (Pipeline priority)
                    try:
                        envelope = self._queue_p1.get_nowait()
                        queue_used = self._queue_p1
                        self._consecutive_p0 = 0
                        self._consecutive_p1 += 1
                    except asyncio.QueueEmpty:
                        # 3. P2 (Telemetry priority): strictly bounded by max_p2_concurrency
                        if len(self._background_tasks) < self.max_p2_concurrency:
                            try:
                                envelope = self._queue_p2.get_nowait()
                                queue_used = self._queue_p2
                                self._consecutive_p0 = 0
                                self._consecutive_p1 = 0
                            except asyncio.QueueEmpty:
                                # All queues empty; yield control briefly
                                await asyncio.sleep(0.002)
                                continue
                        else:
                            # P2 concurrency ceiling reached; yield control so workers can finish
                            await asyncio.sleep(0.002)
                            continue

            # Process envelope
            if envelope.priority == EventPriority.P2:
                # Decouple P2 telemetry delivery: spawn as tracked background task
                # so slow or blocking P2 subscribers cannot delay high-priority P0/P1 dispatch.
                task = asyncio.create_task(self._deliver_p2(envelope, queue_used))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
            else:
                # Critical P0 and Pipeline P1 events are delivered in priority order
                try:
                    await self._deliver(envelope)
                    self._processed_count += 1
                except Exception as e:
                    logger.critical("Unexpected internal error delivering event %s: %s", envelope.message_id, e)
                finally:
                    if queue_used is not None:
                        queue_used.task_done()

    async def _deliver_p2(self, envelope: MessageEnvelope, queue_used: Optional[asyncio.Queue[MessageEnvelope]]) -> None:
        """Deliver P2 telemetry event asynchronously in background task."""
        try:
            await self._deliver(envelope)
            self._processed_count += 1
        except Exception as e:
            logger.critical("Unexpected internal error delivering P2 event %s: %s", envelope.message_id, e)
        finally:
            if queue_used is not None:
                queue_used.task_done()

    async def _deliver(self, envelope: MessageEnvelope) -> None:
        """Deliver envelope to all matching subscriber handlers with error isolation."""
        matching_handlers: List[HandlerFunc] = []

        for pattern, handlers in list(self._subscribers.items()):
            if pattern == envelope.topic or fnmatch.fnmatch(envelope.topic, pattern):
                matching_handlers.extend(handlers)

        if not matching_handlers:
            return

        # Execute all matching handlers concurrently with error isolation and timeout protection
        coros = [self._invoke_handler(handler, envelope) for handler in matching_handlers]
        await asyncio.gather(*coros, return_exceptions=True)

    async def _invoke_handler(self, handler: HandlerFunc, envelope: MessageEnvelope) -> None:
        """Invoke a single handler with error isolation and timeout protection.

        CRITICAL CONCURRENCY AND ISOLATION RULES:
        1. Asynchronous coroutine handlers are bounded with asyncio.wait_for.
        2. Synchronous handlers are executed in Python's default threadpool via asyncio.to_thread
           so that synchronous blocking operations (e.g. time.sleep, CPU-bound processing, or blocking I/O)
           execute on worker threads and never block or freeze the main asyncio event loop.
        3. Note on timeouts: In Python, OS threads cannot be forcibly killed upon timeout.
           Wrapping asyncio.to_thread with asyncio.wait_for stops waiting for the worker thread on timeout,
           while the worker thread continues independently in the background without blocking the loop.
        """
        try:
            if inspect.iscoroutinefunction(handler):
                await asyncio.wait_for(handler(envelope), timeout=self.subscriber_timeout_s)
            else:
                # Synchronous callback: execute in worker thread to prevent blocking main event loop
                res = await asyncio.wait_for(
                    asyncio.to_thread(handler, envelope),
                    timeout=self.subscriber_timeout_s,
                )
                if inspect.isawaitable(res):
                    await asyncio.wait_for(res, timeout=self.subscriber_timeout_s)
        except asyncio.TimeoutError:
            logger.warning(
                "Subscriber %s timed out after %.1fs processing topic %s",
                getattr(handler, "__name__", str(handler)),
                self.subscriber_timeout_s,
                envelope.topic,
            )
        except Exception as e:
            logger.error(
                "Error in subscriber %s processing topic %s: %s",
                getattr(handler, "__name__", str(handler)),
                envelope.topic,
                e,
                exc_info=True,
            )

    def stats(self) -> Dict[str, int]:
        """Return operational queue metrics."""
        return {
            "p0_queue_size": self._queue_p0.qsize(),
            "p1_queue_size": self._queue_p1.qsize(),
            "p2_queue_size": self._queue_p2.qsize(),
            "active_p2_tasks_count": len(self._background_tasks),
            "max_p2_concurrency": self.max_p2_concurrency,
            "published_count": self._published_count,
            "processed_count": self._processed_count,
            "dropped_count": self._dropped_count,
            "active_subscribers_count": len(self._all_handlers),
        }
