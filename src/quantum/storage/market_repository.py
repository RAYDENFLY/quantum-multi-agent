"""Market data repository for SQLite persistence.

Handles batch inserts for candles, tickers, orderbook snapshots, instrument
discovery metadata, and exchange connection health tracking. All operations
are non-blocking and compatible with asyncio.
"""

import json
import time
from typing import Any, Dict, List, Optional, Sequence
import aiosqlite

from quantum.core.logging import get_logger
from quantum.storage.database import DatabaseManager

logger = get_logger("storage.market_repository")


class MarketRepository:
    """Repository handling persistence of market data and exchange state."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    async def save_instruments(self, instruments: Sequence[Dict[str, Any]]) -> int:
        """Upsert exchange instruments into exchange_instruments table."""
        if not instruments:
            return 0

        sql = """
        INSERT INTO exchange_instruments (
            instrument_id, exchange, symbol, base_asset, quote_asset, status,
            tick_size, lot_step, min_order_qty, max_order_qty, min_notional_usdt,
            max_leverage, maker_fee_rate, taker_fee_rate, onboard_timestamp_ms, updated_at_ms
        ) VALUES (
            :instrument_id, :exchange, :symbol, :base_asset, :quote_asset, :status,
            :tick_size, :lot_step, :min_order_qty, :max_order_qty, :min_notional_usdt,
            :max_leverage, :maker_fee_rate, :taker_fee_rate, :onboard_timestamp_ms, :updated_at_ms
        )
        ON CONFLICT(instrument_id) DO UPDATE SET
            status = excluded.status,
            tick_size = excluded.tick_size,
            lot_step = excluded.lot_step,
            min_order_qty = excluded.min_order_qty,
            max_order_qty = excluded.max_order_qty,
            min_notional_usdt = excluded.min_notional_usdt,
            max_leverage = excluded.max_leverage,
            maker_fee_rate = excluded.maker_fee_rate,
            taker_fee_rate = excluded.taker_fee_rate,
            updated_at_ms = excluded.updated_at_ms;
        """
        conn = await self.db.connect()
        cursor = await conn.executemany(sql, instruments)
        await conn.commit()
        return cursor.rowcount

    async def save_tickers_batch(self, tickers: Sequence[Dict[str, Any]]) -> int:
        """Batch insert ticker snapshots."""
        if not tickers:
            return 0

        sql = """
        INSERT INTO market_tickers (
            instrument_id, timestamp_ms, last_price, mark_price, index_price,
            bid1_price, bid1_size, ask1_price, ask1_size, spread_bps,
            volume_24h, turnover_24h_usdt, open_interest, funding_rate, next_funding_time_ms
        ) VALUES (
            :instrument_id, :timestamp_ms, :last_price, :mark_price, :index_price,
            :bid1_price, :bid1_size, :ask1_price, :ask1_size, :spread_bps,
            :volume_24h, :turnover_24h_usdt, :open_interest, :funding_rate, :next_funding_time_ms
        );
        """
        conn = await self.db.connect()
        cursor = await conn.executemany(sql, tickers)
        await conn.commit()
        return cursor.rowcount

    async def save_orderbook_snapshots_batch(self, snapshots: Sequence[Dict[str, Any]]) -> int:
        """Batch insert orderbook depth snapshots."""
        if not snapshots:
            return 0

        sql = """
        INSERT INTO market_orderbook_snapshots (
            instrument_id, timestamp_ms, update_id, bids_json, asks_json,
            bid1_price, ask1_price, spread_bps, is_crossed
        ) VALUES (
            :instrument_id, :timestamp_ms, :update_id, :bids_json, :asks_json,
            :bid1_price, :ask1_price, :spread_bps, :is_crossed
        );
        """
        conn = await self.db.connect()
        cursor = await conn.executemany(sql, snapshots)
        await conn.commit()
        return cursor.rowcount

    async def save_candles_batch(self, candles: Sequence[Dict[str, Any]]) -> int:
        """Batch insert or replace OHLCV candles."""
        if not candles:
            return 0

        sql = """
        INSERT INTO market_candles (
            instrument_id, timeframe, open_time_ms, close_time_ms,
            open_price, high_price, low_price, close_price,
            volume, turnover_usdt, trades_count, is_closed
        ) VALUES (
            :instrument_id, :timeframe, :open_time_ms, :close_time_ms,
            :open_price, :high_price, :low_price, :close_price,
            :volume, :turnover_usdt, :trades_count, :is_closed
        )
        ON CONFLICT(instrument_id, timeframe, open_time_ms) DO UPDATE SET
            close_time_ms = excluded.close_time_ms,
            open_price = excluded.open_price,
            high_price = excluded.high_price,
            low_price = excluded.low_price,
            close_price = excluded.close_price,
            volume = excluded.volume,
            turnover_usdt = excluded.turnover_usdt,
            trades_count = excluded.trades_count,
            is_closed = excluded.is_closed;
        """
        conn = await self.db.connect()
        cursor = await conn.executemany(sql, candles)
        await conn.commit()
        return cursor.rowcount

    async def update_exchange_health(self, health_data: Dict[str, Any]) -> None:
        """Upsert exchange connection health record."""
        sql = """
        INSERT INTO exchange_connection_health (
            exchange, state, rest_latency_ms, ws_latency_ms,
            last_heartbeat_ms, last_message_ms, reconnect_count, error_count,
            last_error, updated_at_ms
        ) VALUES (
            :exchange, :state, :rest_latency_ms, :ws_latency_ms,
            :last_heartbeat_ms, :last_message_ms, :reconnect_count, :error_count,
            :last_error, :updated_at_ms
        )
        ON CONFLICT(exchange) DO UPDATE SET
            state = excluded.state,
            rest_latency_ms = excluded.rest_latency_ms,
            ws_latency_ms = excluded.ws_latency_ms,
            last_heartbeat_ms = excluded.last_heartbeat_ms,
            last_message_ms = excluded.last_message_ms,
            reconnect_count = excluded.reconnect_count,
            error_count = excluded.error_count,
            last_error = excluded.last_error,
            updated_at_ms = excluded.updated_at_ms;
        """
        conn = await self.db.connect()
        await conn.execute(sql, health_data)
        await conn.commit()

    async def save_audit_event(self, exchange: str, event_type: str, details: Dict[str, Any]) -> None:
        """Log an event into market_data_audit table."""
        sql = """
        INSERT INTO market_data_audit (timestamp_ms, exchange, event_type, details_json)
        VALUES (?, ?, ?, ?);
        """
        now_ms = int(time.time() * 1000)
        conn = await self.db.connect()
        await conn.execute(sql, (now_ms, exchange, event_type, json.dumps(details)))
        await conn.commit()

    async def get_candles(
        self,
        instrument_id: str,
        timeframe: str,
        limit: int = 200,
        before_ms: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch candles for an instrument and timeframe sorted ascending by open_time_ms."""
        conn = await self.db.connect()
        if before_ms is not None:
            sql = """
            SELECT instrument_id, timeframe, open_time_ms, close_time_ms,
                   open_price, high_price, low_price, close_price,
                   volume, turnover_usdt, trades_count, is_closed
            FROM market_candles
            WHERE instrument_id = ? AND timeframe = ? AND open_time_ms < ?
            ORDER BY open_time_ms DESC
            LIMIT ?;
            """
            cursor = await conn.execute(sql, (instrument_id, timeframe, before_ms, limit))
        else:
            sql = """
            SELECT instrument_id, timeframe, open_time_ms, close_time_ms,
                   open_price, high_price, low_price, close_price,
                   volume, turnover_usdt, trades_count, is_closed
            FROM market_candles
            WHERE instrument_id = ? AND timeframe = ?
            ORDER BY open_time_ms DESC
            LIMIT ?;
            """
            cursor = await conn.execute(sql, (instrument_id, timeframe, limit))

        rows = await cursor.fetchall()
        result = [dict(row) for row in rows]
        # Return sorted ascending by open_time_ms
        result.reverse()
        return result

    async def get_latest_ticker(self, instrument_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve most recent ticker for an instrument."""
        conn = await self.db.connect()
        sql = """
        SELECT * FROM market_tickers
        WHERE instrument_id = ?
        ORDER BY timestamp_ms DESC
        LIMIT 1;
        """
        cursor = await conn.execute(sql, (instrument_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_instruments(
        self,
        exchange: Optional[str] = None,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """Retrieve instruments filtered optionally by exchange and status."""
        conn = await self.db.connect()
        clauses = []
        params = []
        if exchange:
            clauses.append("exchange = ?")
            params.append(exchange.upper())
        if active_only:
            clauses.append("status = 'TRADING'")

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM exchange_instruments {where} ORDER BY instrument_id ASC;"
        cursor = await conn.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_exchange_health(self, exchange: str) -> Optional[Dict[str, Any]]:
        """Retrieve connection health status for an exchange."""
        conn = await self.db.connect()
        sql = "SELECT * FROM exchange_connection_health WHERE exchange = ?;"
        cursor = await conn.execute(sql, (exchange.upper(),))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def purge_expired_data(
        self,
        candle_retention_days: int = 30,
        ticker_retention_days: int = 7,
        ob_retention_hours: int = 24,
    ) -> Dict[str, int]:
        """Purge stale market data beyond configured retention windows."""
        now_ms = int(time.time() * 1000)
        candle_cutoff_ms = now_ms - (candle_retention_days * 86_400_000)
        ticker_cutoff_ms = now_ms - (ticker_retention_days * 86_400_000)
        ob_cutoff_ms = now_ms - (ob_retention_hours * 3_600_000)

        conn = await self.db.connect()

        # Candles
        cur_c = await conn.execute("DELETE FROM market_candles WHERE open_time_ms < ?;", (candle_cutoff_ms,))
        deleted_candles = cur_c.rowcount

        # Tickers
        cur_t = await conn.execute("DELETE FROM market_tickers WHERE timestamp_ms < ?;", (ticker_cutoff_ms,))
        deleted_tickers = cur_t.rowcount

        # Orderbooks
        cur_ob = await conn.execute("DELETE FROM market_orderbook_snapshots WHERE timestamp_ms < ?;", (ob_cutoff_ms,))
        deleted_obs = cur_ob.rowcount

        await conn.commit()

        logger.info(
            "Purged expired market data: %d candles (< %d d), %d tickers (< %d d), %d orderbooks (< %d h)",
            deleted_candles, candle_retention_days, deleted_tickers, ticker_retention_days, deleted_obs, ob_retention_hours
        )
        return {
            "deleted_candles": deleted_candles,
            "deleted_tickers": deleted_tickers,
            "deleted_orderbooks": deleted_obs,
        }
