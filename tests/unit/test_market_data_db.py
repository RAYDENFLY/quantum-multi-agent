"""Unit tests for Phase 3 market data SQLite tables, migrations, and repository."""

from pathlib import Path
import time
import pytest

from quantum.storage.database import DatabaseManager
from quantum.storage.market_repository import MarketRepository

PHASE3_TABLES = [
    "market_tickers",
    "market_orderbook_snapshots",
    "market_candles",
    "exchange_connection_health",
    "market_data_audit",
]


@pytest.mark.asyncio
async def test_migration_002_creates_market_data_tables(tmp_path: Path) -> None:
    """Verify migration 002 applies successfully and creates all 5 market data tables."""
    db_file = tmp_path / "test_market_db.db"
    db = DatabaseManager(db_file)
    await db.initialize()

    tables = await db.get_table_names()
    for t in PHASE3_TABLES:
        assert t in tables, f"Expected table {t} missing from database"

    applied = await db.get_applied_migrations()
    assert len(applied) >= 2
    assert applied[1][0] == 2
    assert "002_market_data.sql" in applied[1][1]

    await db.close()


@pytest.mark.asyncio
async def test_market_repository_batch_persistence_and_queries(tmp_path: Path) -> None:
    """Verify batch inserts for instruments, tickers, orderbooks, and candles."""
    db_file = tmp_path / "test_repo.db"
    db = DatabaseManager(db_file)
    await db.initialize()
    repo = MarketRepository(db)

    now_ms = int(time.time() * 1000)

    # 1. Upsert instrument
    inst_record = {
        "instrument_id": "BYBIT:BTCUSDT",
        "exchange": "BYBIT",
        "symbol": "BTCUSDT",
        "base_asset": "BTC",
        "quote_asset": "USDT",
        "status": "TRADING",
        "tick_size": 0.1,
        "lot_step": 0.001,
        "min_order_qty": 0.001,
        "max_order_qty": 100.0,
        "min_notional_usdt": 5.0,
        "max_leverage": 50.0,
        "maker_fee_rate": 0.0002,
        "taker_fee_rate": 0.00055,
        "onboard_timestamp_ms": now_ms,
        "updated_at_ms": now_ms,
    }
    count = await repo.save_instruments([inst_record])
    assert count == 1

    instruments = await repo.get_instruments(exchange="BYBIT")
    assert len(instruments) == 1
    assert instruments[0]["symbol"] == "BTCUSDT"

    # 2. Batch tickers
    ticker_records = [
        {
            "instrument_id": "BYBIT:BTCUSDT",
            "timestamp_ms": now_ms - 1000,
            "last_price": 50000.0,
            "mark_price": 50001.0,
            "index_price": 50000.5,
            "bid1_price": 49999.0,
            "bid1_size": 1.0,
            "ask1_price": 50001.0,
            "ask1_size": 2.0,
            "spread_bps": 0.4,
            "volume_24h": 1000.0,
            "turnover_24h_usdt": 50000000.0,
            "open_interest": 20000.0,
            "funding_rate": 0.0001,
            "next_funding_time_ms": now_ms + 28800000,
        },
        {
            "instrument_id": "BYBIT:BTCUSDT",
            "timestamp_ms": now_ms,
            "last_price": 50050.0,
            "mark_price": 50051.0,
            "index_price": 50050.5,
            "bid1_price": 50049.0,
            "bid1_size": 1.5,
            "ask1_price": 50051.0,
            "ask1_size": 2.5,
            "spread_bps": 0.4,
            "volume_24h": 1010.0,
            "turnover_24h_usdt": 50500000.0,
            "open_interest": 20050.0,
            "funding_rate": 0.0001,
            "next_funding_time_ms": now_ms + 28800000,
        },
    ]
    t_count = await repo.save_tickers_batch(ticker_records)
    assert t_count == 2

    latest_ticker = await repo.get_latest_ticker("BYBIT:BTCUSDT")
    assert latest_ticker is not None
    assert latest_ticker["last_price"] == 50050.0

    # 3. Batch candles and deduplication
    candle_records = [
        {
            "instrument_id": "BYBIT:BTCUSDT",
            "timeframe": "1m",
            "open_time_ms": now_ms - 60000,
            "close_time_ms": now_ms - 1,
            "open_price": 50000.0,
            "high_price": 50060.0,
            "low_price": 49990.0,
            "close_price": 50050.0,
            "volume": 12.0,
            "turnover_usdt": 600000.0,
            "trades_count": 45,
            "is_closed": 1,
        }
    ]
    await repo.save_candles_batch(candle_records)

    # Upsert with updated close_price on same open_time_ms
    updated_candle = dict(candle_records[0], close_price=50055.0)
    await repo.save_candles_batch([updated_candle])

    candles = await repo.get_candles("BYBIT:BTCUSDT", "1m")
    assert len(candles) == 1
    assert candles[0]["close_price"] == 50055.0  # Successfully updated without duplicate primary key error

    # 4. Exchange health and audit events
    health_payload = {
        "exchange": "BYBIT",
        "state": "CONNECTED",
        "rest_latency_ms": 15.2,
        "ws_latency_ms": 8.1,
        "last_heartbeat_ms": now_ms,
        "last_message_ms": now_ms,
        "reconnect_count": 0,
        "error_count": 0,
        "last_error": None,
        "updated_at_ms": now_ms,
    }
    await repo.update_exchange_health(health_payload)
    health = await repo.get_exchange_health("BYBIT")
    assert health is not None
    assert health["state"] == "CONNECTED"
    assert health["rest_latency_ms"] == 15.2

    await repo.save_audit_event("BYBIT", "SEQUENCE_GAP", {"expected": 100, "received": 105})

    # 5. Purge expired data
    # All items inserted with now_ms should NOT be deleted if retention window is > 0 days
    purged = await repo.purge_expired_data(candle_retention_days=1, ticker_retention_days=1, ob_retention_hours=1)
    assert purged["deleted_candles"] == 0
    assert purged["deleted_tickers"] == 0

    await db.close()
