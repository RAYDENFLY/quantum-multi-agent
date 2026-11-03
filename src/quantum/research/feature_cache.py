"""High-Speed Reproducible Intermediate Feature Cache for Continuous Research."""

import hashlib
from pathlib import Path
import threading
import time
from typing import Dict, Optional, Tuple
import pandas as pd

from quantum.features.market_context import compute_market_context_dataframe


class IntermediateFeatureCache:
    """Thread-safe in-memory and disk-backed cache for reproducible market context features.
    
    Prevents cache stampede / thundering herd via fine-grained per-key synchronization.
    """

    def __init__(self, disk_cache_dir: Optional[Path] = None) -> None:
        self.disk_cache_dir = disk_cache_dir
        if self.disk_cache_dir:
            self.disk_cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, pd.DataFrame] = {}
        self._key_locks: Dict[str, threading.Lock] = {}
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0
        self.compute_seconds_saved = 0.0

    def _generate_cache_key(self, symbol: str, timeframe: str, dataset_sha256: str) -> str:
        raw = f"{symbol}_{timeframe}_{dataset_sha256}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get_or_compute(
        self,
        df_raw: pd.DataFrame,
        symbol: str,
        timeframe: str,
        dataset_sha256: str,
    ) -> Tuple[pd.DataFrame, bool]:
        """Returns cached market context dataframe if available, otherwise computes and stores it.
        
        Returns:
            Tuple of (enriched_df, was_cached)
        """
        key = self._generate_cache_key(symbol, timeframe, dataset_sha256)

        # 1. Fast path check without per-key lock
        with self._lock:
            if key in self._memory_cache:
                self.hits += 1
                self.compute_seconds_saved += 3.5
                return self._memory_cache[key].copy(), True
            if key not in self._key_locks:
                self._key_locks[key] = threading.Lock()
            key_lock = self._key_locks[key]

        # 2. Synchronized computation per key (prevents cache stampede)
        with key_lock:
            with self._lock:
                if key in self._memory_cache:
                    self.hits += 1
                    self.compute_seconds_saved += 3.5
                    return self._memory_cache[key].copy(), True

            # Check disk cache if configured
            if self.disk_cache_dir:
                cache_file = self.disk_cache_dir / f"{key}.parquet"
                if cache_file.exists():
                    try:
                        cached_df = pd.read_parquet(cache_file)
                        with self._lock:
                            self._memory_cache[key] = cached_df
                            self.hits += 1
                            self.compute_seconds_saved += 3.5
                        return cached_df.copy(), True
                    except Exception:
                        pass

            # Compute features causally
            t0 = time.perf_counter()
            enriched_df = compute_market_context_dataframe(df_raw)
            elapsed = time.perf_counter() - t0

            with self._lock:
                self._memory_cache[key] = enriched_df.copy()
                self.misses += 1

            # Write to disk cache if configured
            if self.disk_cache_dir:
                cache_file = self.disk_cache_dir / f"{key}.parquet"
                try:
                    enriched_df.to_parquet(cache_file, index=False)
                except Exception:
                    pass

            return enriched_df, False

    def clear(self) -> None:
        """Clears memory cache."""
        with self._lock:
            self._memory_cache.clear()
            self._key_locks.clear()
            self.hits = 0
            self.misses = 0
            self.compute_seconds_saved = 0.0
