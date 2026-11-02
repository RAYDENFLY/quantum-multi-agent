"""Computational thread and resource limit enforcement for QUANTUM backtesting.

Enforces strict hardware constraints across PyArrow, OpenBLAS, OpenMP,
and numerical libraries at package initialization and evaluation execution boundaries.
"""

from contextlib import contextmanager
import os
from typing import Any, Dict, Iterator, List, Optional
import pyarrow as pa
import threadpoolctl

BACKTEST_MAX_THREADS: int = 2

# Module-level handle to prevent garbage collection of threadpoolctl controller
_ACTIVE_THREADPOOL_CONTROLLER: Optional[Any] = None


def enforce_backtest_thread_limits(max_threads: int = BACKTEST_MAX_THREADS) -> Dict[str, Any]:
    """Enforce computational thread limits across PyArrow and numerical libraries.

    Applies:
    1. PyArrow CPU thread pool limit (pa.set_cpu_count).
    2. PyArrow I/O worker thread pool limit (pa.set_io_thread_count).
    3. Numerical library thread limit via threadpoolctl (OpenBLAS, OpenMP, MKL, BLIS).
    4. Process environment variables for late-imported numerical backends.

    Args:
        max_threads: Maximum computational threads (default: 2, must be 1 or 2).

    Returns:
        Dict detailing active thread pool configurations.
    """
    global _ACTIVE_THREADPOOL_CONTROLLER

    if max_threads < 1 or max_threads > 2:
        raise ValueError(f"Backtest thread limit must be between 1 and 2, got {max_threads}")

    # 1. PyArrow CPU and I/O thread pools
    pa.set_cpu_count(max_threads)
    pa.set_io_thread_count(max_threads)

    # 2. Process environment variables for any newly loaded C/Fortran libraries
    str_val = str(max_threads)
    for env_var in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        os.environ[env_var] = str_val

    # 3. threadpoolctl active controller for currently loaded shared libraries
    _ACTIVE_THREADPOOL_CONTROLLER = threadpoolctl.threadpool_limits(limits=max_threads)

    return get_active_thread_limits()


def get_active_thread_limits() -> Dict[str, Any]:
    """Inspect and return current thread limits across numerical runtimes."""
    tp_info = threadpoolctl.threadpool_info()
    return {
        "pyarrow_cpu": pa.cpu_count(),
        "pyarrow_io": pa.io_thread_count(),
        "threadpool_controllers": [
            {
                "user_api": c.get("user_api"),
                "internal_api": c.get("internal_api"),
                "num_threads": c.get("num_threads"),
                "prefix": c.get("prefix"),
            }
            for c in tp_info
        ],
    }


def verify_thread_limits(max_threads: int = BACKTEST_MAX_THREADS) -> bool:
    """Return True if all PyArrow and numerical thread pools are <= max_threads."""
    if pa.cpu_count() > max_threads or pa.io_thread_count() > max_threads:
        return False
    for pool in threadpoolctl.threadpool_info():
        nt = pool.get("num_threads")
        if nt is not None and nt > max_threads:
            return False
    return True


def check_thread_limits(max_threads: int = BACKTEST_MAX_THREADS) -> None:
    """Enforce and verify thread limits, raising RuntimeError if any pool exceeds limit."""
    enforce_backtest_thread_limits(max_threads)
    if pa.cpu_count() > max_threads:
        raise RuntimeError(f"PyArrow CPU thread pool exceeds limit: {pa.cpu_count()} > {max_threads}")
    if pa.io_thread_count() > max_threads:
        raise RuntimeError(f"PyArrow I/O thread pool exceeds limit: {pa.io_thread_count()} > {max_threads}")
    for pool in threadpoolctl.threadpool_info():
        nt = pool.get("num_threads")
        if nt is not None and nt > max_threads:
            api_name = pool.get("internal_api", "unknown")
            raise RuntimeError(f"Numerical thread pool ({api_name}) exceeds limit: {nt} > {max_threads}")


@contextmanager
def limit_computational_threads(max_threads: int = BACKTEST_MAX_THREADS) -> Iterator[None]:
    """Context manager for scoping thread pool limits to specific code blocks."""
    enforce_backtest_thread_limits(max_threads)
    try:
        yield
    finally:
        enforce_backtest_thread_limits(max_threads)
