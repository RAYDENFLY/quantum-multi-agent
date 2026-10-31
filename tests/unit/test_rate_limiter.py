"""Unit tests for TokenBucketRateLimiter and rate throttling."""

import asyncio
import time
import pytest

from quantum.exchanges.base import TokenBucketRateLimiter


@pytest.mark.asyncio
async def test_token_bucket_immediate_acquisition() -> None:
    """Verify immediate acquisition when bucket has available capacity."""
    limiter = TokenBucketRateLimiter(rate_limit_rps=10.0, capacity=10.0)
    start = time.perf_counter()
    for _ in range(5):
        await limiter.acquire(1.0)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.1  # Immediate without blocking


@pytest.mark.asyncio
async def test_token_bucket_throttling_delay() -> None:
    """Verify rate limiter pauses when capacity is exhausted."""
    # 5 tokens per second, initial capacity 2
    limiter = TokenBucketRateLimiter(rate_limit_rps=5.0, capacity=2.0)

    # Exhaust capacity
    await limiter.acquire(1.0)
    await limiter.acquire(1.0)

    # Third token must wait ~0.20s (1 / 5)
    start = time.perf_counter()
    await limiter.acquire(1.0)
    elapsed = time.perf_counter() - start
    assert elapsed >= 0.15  # Waited approximately 0.20s


@pytest.mark.asyncio
async def test_token_bucket_concurrent_acquisitions() -> None:
    """Verify concurrent coroutines acquire tokens safely without race conditions."""
    limiter = TokenBucketRateLimiter(rate_limit_rps=20.0, capacity=10.0)

    async def worker() -> None:
        await limiter.acquire(1.0)

    tasks = [asyncio.create_task(worker()) for _ in range(10)]
    start = time.perf_counter()
    await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.2  # 10 tokens within capacity
