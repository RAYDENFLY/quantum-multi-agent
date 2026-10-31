"""Feature engineering package providing causal indicators, schema, and multi-timeframe joins."""

from quantum.features.engine import FeatureEngine
from quantum.features.indicators import (
    compute_atr,
    compute_bollinger_bands,
    compute_donchian_channels,
    compute_ema,
    compute_macd,
    compute_rsi,
    compute_stochastic,
)
from quantum.features.multitimeframe import MultiTimeframeJoiner
from quantum.features.schema import BASE_FEATURE_COLUMNS, FEATURE_SCHEMA_VERSION

__all__ = [
    "FeatureEngine",
    "MultiTimeframeJoiner",
    "FEATURE_SCHEMA_VERSION",
    "BASE_FEATURE_COLUMNS",
    "compute_ema",
    "compute_rsi",
    "compute_macd",
    "compute_stochastic",
    "compute_atr",
    "compute_bollinger_bands",
    "compute_donchian_channels",
]
