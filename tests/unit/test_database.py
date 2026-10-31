"""Unit tests for SQLite WAL persistence and schema migrations."""

from pathlib import Path
import sqlite3
import pytest
from quantum.storage.database import DatabaseManager

EXPECTED_TABLES = [
    "agent_messages",
    "agent_runs",
    "app_settings",
    "exchange_instruments",
    "executions",
    "funding_events",
    "market_snapshots",
    "model_evaluations",
    "model_registry",
    "paper_orders",
    "performance_metrics",
    "positions",
    "risk_decisions",
    "scanner_candidates",
    "schema_migrations",
    "trade_journal",
    "trade_proposals",
    "training_runs",
]


@pytest.mark.asyncio
async def test_database_initialization_and_wal_mode(tmp_path: Path) -> None:
    """Verify SQLite WAL pragmas and connection initialization."""
    db_file = tmp_path / "test_desk.db"
    db = DatabaseManager(db_file)

    await db.initialize()
    assert db.is_connected

    # 1. Verify WAL mode
    journal_mode = await db.get_journal_mode()
    assert journal_mode == "WAL"

    # 2. Verify synchronous = NORMAL (1 in SQLite)
    async with (await db.connect()).execute("PRAGMA synchronous;") as cursor:
        row = await cursor.fetchone()
        assert row[0] == 1  # 1 corresponds to NORMAL

    # 3. Verify foreign keys = ON (1)
    async with (await db.connect()).execute("PRAGMA foreign_keys;") as cursor:
        row = await cursor.fetchone()
        assert row[0] == 1

    await db.close()
    assert not db.is_connected


@pytest.mark.asyncio
async def test_migration_execution_creates_all_18_tables(tmp_path: Path) -> None:
    """Verify all 18 tables from docs/DATABASE_SCHEMA.md are created accurately."""
    import shutil
    mig_dir = tmp_path / "initial_migrations"
    mig_dir.mkdir()
    shutil.copy(Path(__file__).parents[2] / "src" / "quantum" / "storage" / "migrations" / "001_initial.sql", mig_dir)
    db_file = tmp_path / "test_schema.db"
    db = DatabaseManager(db_file, migrations_dir=mig_dir)

    await db.initialize()

    tables = await db.get_table_names()
    assert len(tables) == 18
    assert sorted(tables) == sorted(EXPECTED_TABLES)

    # Verify migration record
    applied = await db.get_applied_migrations()
    assert len(applied) == 1
    assert applied[0][0] == 1
    assert "001_initial.sql" in applied[0][1]

    # Verify migration idempotency (second apply does nothing)
    reapplied_count = await db.apply_migrations()
    assert reapplied_count == 0

    await db.close()


@pytest.mark.asyncio
async def test_foreign_key_enforcement(tmp_path: Path) -> None:
    """Verify foreign key constraints prevent orphan records."""
    db_file = tmp_path / "test_fk.db"
    db = DatabaseManager(db_file)
    await db.initialize()

    # Attempt inserting a market_snapshot referencing non-existent instrument
    with pytest.raises(sqlite3.IntegrityError):
        await db.execute_commit(
            """
            INSERT INTO market_snapshots (
                snapshot_id, instrument_id, timestamp_ms, last_price, mark_price,
                index_price, bid1_price, ask1_price, spread_bps, turnover_24h_usdt,
                price_change_24h_pct, funding_rate, next_funding_time_ms,
                feature_schema_version, features_json
            ) VALUES (
                'snap_001', 'NONEXISTENT:BTCUSDT', 1700000000000, 50000.0, 50000.0,
                50000.0, 49999.0, 50001.0, 4.0, 10000000.0, 2.5, 0.0001, 1700028800000,
                'FEATURE_SCHEMA_V1', '{}'
            )
            """
        )

    # Insert valid exchange instrument first
    await db.execute_commit(
        """
        INSERT INTO exchange_instruments (
            instrument_id, exchange, symbol, base_asset, quote_asset, status,
            tick_size, lot_step, min_order_qty, max_order_qty, min_notional_usdt,
            max_leverage, maker_fee_rate, taker_fee_rate, onboard_timestamp_ms, updated_at_ms
        ) VALUES (
            'BYBIT:BTCUSDT', 'BYBIT', 'BTCUSDT', 'BTC', 'USDT', 'TRADING',
            0.1, 0.001, 0.001, 100.0, 5.0, 50.0, 0.0002, 0.00055, 1700000000000, 1700000000000
        )
        """
    )

    # Now snapshot insert succeeds
    await db.execute_commit(
        """
        INSERT INTO market_snapshots (
            snapshot_id, instrument_id, timestamp_ms, last_price, mark_price,
            index_price, bid1_price, ask1_price, spread_bps, turnover_24h_usdt,
            price_change_24h_pct, funding_rate, next_funding_time_ms,
            feature_schema_version, features_json
        ) VALUES (
            'snap_001', 'BYBIT:BTCUSDT', 1700000000000, 50000.0, 50000.0,
            50000.0, 49999.0, 50001.0, 4.0, 10000000.0, 2.5, 0.0001, 1700028800000,
            'FEATURE_SCHEMA_V1', '{}'
        )
        """
    )

    row = await db.fetch_one("SELECT snapshot_id, last_price FROM market_snapshots WHERE snapshot_id = 'snap_001'")
    assert row is not None
    assert row[0] == "snap_001"
    assert row[1] == 50000.0

    await db.close()
