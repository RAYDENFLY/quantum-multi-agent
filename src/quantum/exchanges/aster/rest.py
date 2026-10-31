"""Asynchronous REST client for AsterDEX Futures API."""

import asyncio
import random
import time
from typing import Any, Dict, List, Optional
import aiohttp

from quantum.core.logging import get_logger
from quantum.exchanges.base import TokenBucketRateLimiter

logger = get_logger("exchanges.aster.rest")


class AsterRestClient:
    """Non-blocking HTTP client for AsterDEX /fapi/v1 endpoints."""

    def __init__(
        self,
        base_url: str = "https://fapi.asterdex.com",
        rate_limiter: Optional[TokenBucketRateLimiter] = None,
        timeout_s: float = 10.0,
        max_retries: int = 3,
        retry_backoff_s: float = 1.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.rate_limiter = rate_limiter or TokenBucketRateLimiter(rate_limit_rps=10.0)
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.retry_backoff_s = retry_backoff_s
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout_s)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close underlying aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute HTTP GET with rate limiting and exponential backoff retry."""
        url = f"{self.base_url}{endpoint}"
        session = await self._get_session()

        for attempt in range(self.max_retries + 1):
            await self.rate_limiter.acquire()
            try:
                async with session.get(url, params=params) as resp:
                    status = resp.status
                    if status == 200:
                        return await resp.json()

                    if status in (429, 500, 502, 503, 504):
                        if attempt < self.max_retries:
                            backoff = (self.retry_backoff_s * (2 ** attempt)) + random.uniform(0.1, 0.5)
                            logger.warning(
                                "AsterDEX REST status %d on %s. Retrying in %.2fs (attempt %d/%d)",
                                status, endpoint, backoff, attempt + 1, self.max_retries
                            )
                            await asyncio.sleep(backoff)
                            continue
                    resp.raise_for_status()

            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                if attempt < self.max_retries:
                    backoff = (self.retry_backoff_s * (2 ** attempt)) + random.uniform(0.1, 0.5)
                    logger.warning(
                        "AsterDEX REST error (%s) on %s. Retrying in %.2fs (attempt %d/%d)",
                        type(err).__name__, endpoint, backoff, attempt + 1, self.max_retries
                    )
                    await asyncio.sleep(backoff)
                else:
                    logger.error("AsterDEX REST failed after %d attempts: %s", self.max_retries + 1, err)
                    raise

        raise RuntimeError(f"AsterDEX REST request failed after {self.max_retries} retries: {endpoint}")

    async def get_exchange_info(self) -> Dict[str, Any]:
        """Fetch exchange symbol metadata and trading rules."""
        return await self._request("/fapi/v1/exchangeInfo")

    async def get_ticker_24hr(self, symbol: str) -> Dict[str, Any]:
        """Fetch 24-hour ticker price change statistics."""
        params = {"symbol": symbol.upper()}
        return await self._request("/fapi/v1/ticker/24hr", params=params)

    async def get_premium_index(self, symbol: str) -> Dict[str, Any]:
        """Fetch mark price, index price, and funding rate."""
        params = {"symbol": symbol.upper()}
        return await self._request("/fapi/v1/premiumIndex", params=params)

    async def get_depth(self, symbol: str, limit: int = 50) -> Dict[str, Any]:
        """Fetch order book depth snapshot."""
        params = {"symbol": symbol.upper(), "limit": min(limit, 100)}
        return await self._request("/fapi/v1/depth", params=params)

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 200,
        before_ms: Optional[int] = None,
    ) -> List[List[Any]]:
        """Fetch candlestick bars."""
        params: Dict[str, Any] = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": min(limit, 1000),
        }
        if before_ms:
            params["endTime"] = before_ms

        return await self._request("/fapi/v1/klines", params=params)

    async def get_server_time(self) -> int:
        """Fetch AsterDEX server time in milliseconds."""
        result = await self._request("/fapi/v1/time")
        if isinstance(result, dict) and "serverTime" in result:
            return int(result["serverTime"])
        return int(time.time() * 1000)
