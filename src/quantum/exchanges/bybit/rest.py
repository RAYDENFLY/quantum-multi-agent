"""Asynchronous REST client for Bybit V5 Linear Perpetuals API."""

import asyncio
import random
import time
from typing import Any, Dict, List, Optional
import aiohttp

from quantum.core.logging import get_logger
from quantum.exchanges.base import TokenBucketRateLimiter

logger = get_logger("exchanges.bybit.rest")


class BybitRestClient:
    """Non-blocking HTTP client for Bybit V5 Linear Perpetual endpoints."""

    def __init__(
        self,
        base_url: str = "https://api.bybit.com",
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

    async def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute HTTP GET with rate limiting and exponential backoff retry."""
        url = f"{self.base_url}{endpoint}"
        session = await self._get_session()

        for attempt in range(self.max_retries + 1):
            await self.rate_limiter.acquire()
            try:
                async with session.get(url, params=params) as resp:
                    status = resp.status
                    if status == 200:
                        data = await resp.json()
                        ret_code = data.get("retCode", -1)
                        if ret_code != 0:
                            ret_msg = data.get("retMsg", "Unknown Bybit error")
                            raise RuntimeError(f"Bybit API error code {ret_code}: {ret_msg}")
                        return data.get("result", {})

                    if status in (429, 500, 502, 503, 504):
                        if attempt < self.max_retries:
                            backoff = (self.retry_backoff_s * (2 ** attempt)) + random.uniform(0.1, 0.5)
                            logger.warning(
                                "Bybit REST status %d on %s. Retrying in %.2fs (attempt %d/%d)",
                                status, endpoint, backoff, attempt + 1, self.max_retries
                            )
                            await asyncio.sleep(backoff)
                            continue
                    resp.raise_for_status()

            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                if attempt < self.max_retries:
                    backoff = (self.retry_backoff_s * (2 ** attempt)) + random.uniform(0.1, 0.5)
                    logger.warning(
                        "Bybit REST error (%s) on %s. Retrying in %.2fs (attempt %d/%d)",
                        type(err).__name__, endpoint, backoff, attempt + 1, self.max_retries
                    )
                    await asyncio.sleep(backoff)
                else:
                    logger.error("Bybit REST failed after %d attempts: %s", self.max_retries + 1, err)
                    raise

        raise RuntimeError(f"Bybit REST request failed after {self.max_retries} retries: {endpoint}")

    async def get_instruments_info(self) -> List[Dict[str, Any]]:
        """Fetch linear perpetual instruments info."""
        params = {"category": "linear", "status": "Trading", "limit": 1000}
        result = await self._request("/v5/market/instruments-info", params=params)
        return result.get("list", [])

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Fetch 24h ticker for a linear perpetual symbol."""
        params = {"category": "linear", "symbol": symbol.upper()}
        result = await self._request("/v5/market/tickers", params=params)
        items = result.get("list", [])
        if not items:
            raise ValueError(f"No ticker returned for symbol {symbol}")
        return items[0]

    async def get_orderbook(self, symbol: str, limit: int = 50) -> Dict[str, Any]:
        """Fetch L2 order book snapshot for symbol."""
        params = {"category": "linear", "symbol": symbol.upper(), "limit": min(limit, 50)}
        return await self._request("/v5/market/orderbook", params=params)

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 200,
        before_ms: Optional[int] = None,
    ) -> List[List[str]]:
        """Fetch historical klines for symbol."""
        params: Dict[str, Any] = {
            "category": "linear",
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": min(limit, 1000),
        }
        if before_ms:
            params["end"] = before_ms

        result = await self._request("/v5/market/kline", params=params)
        return result.get("list", [])

    async def get_server_time(self) -> int:
        """Fetch exchange server time in milliseconds."""
        result = await self._request("/v5/market/time")
        # Bybit v5 returns timeNano or timeSecond
        if "timeNano" in result:
            return int(int(result["timeNano"]) / 1_000_000)
        if "timeSecond" in result:
            return int(result["timeSecond"]) * 1000
        return int(time.time() * 1000)
