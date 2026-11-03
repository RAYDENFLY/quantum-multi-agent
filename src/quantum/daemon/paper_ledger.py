"""SQLite WAL Persistence and Ledger Manager for Phase 6A Paper Trading.

Implements:
1. Account state, active positions, pending maker orders, and closed trades in SQLite WAL.
2. DEC_05 Option 3 risk envelope:
   - Hard aggregate gross exposure cap: sum(|N_i|) <= 0.30 * Equity.
   - Volatility risk-budget sizing: N_i = R_budget * Equity / (1.0 * sigma_t).
   - Single-asset notional cap: N_i <= 0.10 * Equity.
   - Pro-rata scaling when concurrent orders breach the 30% gross exposure ceiling.
3. Maker-Passive fee accounting (4.0 bps maker fee per leg = 8.0 bps round-trip friction, 0.0 bps slippage).
4. Immediate Emergency Kill-Switch execution (cancels orders, liquidates positions, locks account).
"""

import asyncio
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple

import aiosqlite
from pydantic import BaseModel, ConfigDict, Field

DEFAULT_DB_PATH = Path("artifacts/phase_6/quantum_paper_trade.db")

PRAGMAS: List[str] = [
    "PRAGMA journal_mode = WAL;",
    "PRAGMA synchronous = NORMAL;",
    "PRAGMA foreign_keys = ON;",
    "PRAGMA busy_timeout = 5000;",
]

SCHEMA_STATEMENTS: List[str] = [
    """
    CREATE TABLE IF NOT EXISTS account_state (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp_ms INTEGER NOT NULL,
        equity REAL NOT NULL,
        cash REAL NOT NULL,
        unrealized_pnl REAL NOT NULL,
        realized_pnl REAL NOT NULL,
        peak_equity REAL NOT NULL,
        max_drawdown_pct REAL NOT NULL,
        gross_exposure REAL NOT NULL,
        gross_exposure_pct REAL NOT NULL,
        is_kill_switch_active INTEGER NOT NULL DEFAULT 0
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS positions (
        position_id TEXT PRIMARY KEY,
        symbol TEXT NOT NULL,
        side TEXT NOT NULL,
        quantity REAL NOT NULL,
        entry_price REAL NOT NULL,
        mark_price REAL NOT NULL,
        current_sl REAL NOT NULL,
        current_tp REAL NOT NULL,
        entry_time_ms INTEGER NOT NULL,
        bars_held INTEGER NOT NULL DEFAULT 1,
        volatility_sigma REAL NOT NULL,
        notional REAL NOT NULL,
        unrealized_pnl REAL NOT NULL,
        updated_at_ms INTEGER NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS pending_orders (
        order_id TEXT PRIMARY KEY,
        symbol TEXT NOT NULL,
        side TEXT NOT NULL,
        quantity REAL NOT NULL,
        limit_price REAL NOT NULL,
        tp_price REAL NOT NULL,
        sl_price REAL NOT NULL,
        created_at_ms INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING',
        volatility_sigma REAL NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS trades (
        trade_id TEXT PRIMARY KEY,
        symbol TEXT NOT NULL,
        side TEXT NOT NULL,
        quantity REAL NOT NULL,
        entry_price REAL NOT NULL,
        exit_price REAL NOT NULL,
        entry_time_ms INTEGER NOT NULL,
        exit_time_ms INTEGER NOT NULL,
        exit_reason TEXT NOT NULL,
        gross_pnl REAL NOT NULL,
        fee REAL NOT NULL,
        slippage REAL NOT NULL,
        net_pnl REAL NOT NULL,
        net_return_bps REAL NOT NULL,
        bars_held INTEGER NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS telemetry_snapshots (
        timestamp_ms INTEGER PRIMARY KEY,
        data_json TEXT NOT NULL
    );
    """
]


class AccountState(BaseModel):
    """Snapshot of paper account equity, cash, exposure, and risk state."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    timestamp_ms: int
    equity: float
    cash: float
    unrealized_pnl: float
    realized_pnl: float
    peak_equity: float
    max_drawdown_pct: float
    gross_exposure: float
    gross_exposure_pct: float
    is_kill_switch_active: bool


class PositionRecord(BaseModel):
    """Active open position in paper trading."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    position_id: str
    symbol: str
    side: str
    quantity: float
    entry_price: float
    mark_price: float
    current_sl: float
    current_tp: float
    entry_time_ms: int
    bars_held: int
    volatility_sigma: float
    notional: float
    unrealized_pnl: float
    updated_at_ms: int


class PendingOrderRecord(BaseModel):
    """Pending maker limit order waiting for execution fill."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    order_id: str
    symbol: str
    side: str
    quantity: float
    limit_price: float
    tp_price: float
    sl_price: float
    created_at_ms: int
    status: str
    volatility_sigma: float


class TradeRecord(BaseModel):
    """Realized closed paper trade ledger entry."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    trade_id: str
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: float
    entry_time_ms: int
    exit_time_ms: int
    exit_reason: str
    gross_pnl: float
    fee: float
    slippage: float
    net_pnl: float
    net_return_bps: float
    bars_held: int


class PaperLedgerManager:
    """Manages SQLite WAL paper trading ledger and DEC_05 Option 3 portfolio risk envelope."""

    def __init__(
        self,
        db_path: Optional[Path] = None,
        initial_equity: float = 10_000.0,
        maker_fee_bps: float = 4.0,
        slippage_bps: float = 0.0,
        gross_exposure_cap_pct: float = 0.30,
        single_asset_cap_pct: float = 0.10,
        risk_budget_bps: float = 30.0,
    ) -> None:
        self.db_path = Path(db_path or DEFAULT_DB_PATH).resolve()
        self.initial_equity = initial_equity
        self.maker_fee_bps = maker_fee_bps
        self.slippage_bps = slippage_bps
        self.gross_exposure_cap_pct = gross_exposure_cap_pct
        self.single_asset_cap_pct = single_asset_cap_pct
        self.risk_budget_factor = risk_budget_bps / 10_000.0  # 30 bps = 0.003
        self._connection: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()
        self._initialized = False

    async def connect(self) -> aiosqlite.Connection:
        """Connect to SQLite database and apply WAL pragmas."""
        async with self._lock:
            if self._connection is None:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
                self._connection = await aiosqlite.connect(str(self.db_path))
                self._connection.row_factory = aiosqlite.Row
                for pragma in PRAGMAS:
                    await self._connection.execute(pragma)
                await self._connection.commit()
            return self._connection

    async def initialize(self) -> None:
        """Create tables and initialize starting account balance if empty."""
        if self._initialized:
            return
        conn = await self.connect()
        async with self._lock:
            for stmt in SCHEMA_STATEMENTS:
                await conn.execute(stmt)
            await conn.commit()

            # Check if account state exists
            async with conn.execute("SELECT COUNT(*) AS cnt FROM account_state") as cursor:
                row = await cursor.fetchone()
                cnt = row["cnt"] if row else 0

            if cnt == 0:
                now_ms = int(time.time() * 1000)
                await conn.execute(
                    """
                    INSERT INTO account_state (
                        timestamp_ms, equity, cash, unrealized_pnl, realized_pnl,
                        peak_equity, max_drawdown_pct, gross_exposure, gross_exposure_pct,
                        is_kill_switch_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        now_ms,
                        self.initial_equity,
                        self.initial_equity,
                        0.0,
                        0.0,
                        self.initial_equity,
                        0.0,
                        0.0,
                        0.0,
                        0,
                    ),
                )
                await conn.commit()
            self._initialized = True

    async def close(self) -> None:
        """Close database connection."""
        async with self._lock:
            if self._connection is not None:
                await self._connection.close()
                self._connection = None
                self._initialized = False

    async def get_latest_account_state(self) -> AccountState:
        """Fetch current paper account state from SQLite."""
        await self.initialize()
        conn = await self.connect()
        async with conn.execute(
            "SELECT * FROM account_state ORDER BY id DESC LIMIT 1"
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise RuntimeError("Account state missing from database")
            return AccountState(
                timestamp_ms=row["timestamp_ms"],
                equity=row["equity"],
                cash=row["cash"],
                unrealized_pnl=row["unrealized_pnl"],
                realized_pnl=row["realized_pnl"],
                peak_equity=row["peak_equity"],
                max_drawdown_pct=row["max_drawdown_pct"],
                gross_exposure=row["gross_exposure"],
                gross_exposure_pct=row["gross_exposure_pct"],
                is_kill_switch_active=bool(row["is_kill_switch_active"]),
            )

    async def get_active_positions(self) -> List[PositionRecord]:
        """Fetch all currently open paper positions."""
        await self.initialize()
        conn = await self.connect()
        async with conn.execute("SELECT * FROM positions ORDER BY entry_time_ms ASC") as cursor:
            rows = await cursor.fetchall()
            return [
                PositionRecord(
                    position_id=r["position_id"],
                    symbol=r["symbol"],
                    side=r["side"],
                    quantity=r["quantity"],
                    entry_price=r["entry_price"],
                    mark_price=r["mark_price"],
                    current_sl=r["current_sl"],
                    current_tp=r["current_tp"],
                    entry_time_ms=r["entry_time_ms"],
                    bars_held=r["bars_held"],
                    volatility_sigma=r["volatility_sigma"],
                    notional=r["notional"],
                    unrealized_pnl=r["unrealized_pnl"],
                    updated_at_ms=r["updated_at_ms"],
                )
                for r in rows
            ]

    async def get_pending_orders(self) -> List[PendingOrderRecord]:
        """Fetch all active pending maker limit orders."""
        await self.initialize()
        conn = await self.connect()
        async with conn.execute("SELECT * FROM pending_orders WHERE status = 'PENDING'") as cursor:
            rows = await cursor.fetchall()
            return [
                PendingOrderRecord(
                    order_id=r["order_id"],
                    symbol=r["symbol"],
                    side=r["side"],
                    quantity=r["quantity"],
                    limit_price=r["limit_price"],
                    tp_price=r["tp_price"],
                    sl_price=r["sl_price"],
                    created_at_ms=r["created_at_ms"],
                    status=r["status"],
                    volatility_sigma=r["volatility_sigma"],
                )
                for r in rows
            ]

    async def get_recent_trades(self, limit: int = 50) -> List[TradeRecord]:
        """Fetch recently closed paper trades."""
        await self.initialize()
        conn = await self.connect()
        async with conn.execute(
            "SELECT * FROM trades ORDER BY exit_time_ms DESC LIMIT ?", (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                TradeRecord(
                    trade_id=r["trade_id"],
                    symbol=r["symbol"],
                    side=r["side"],
                    quantity=r["quantity"],
                    entry_price=r["entry_price"],
                    exit_price=r["exit_price"],
                    entry_time_ms=r["entry_time_ms"],
                    exit_time_ms=r["exit_time_ms"],
                    exit_reason=r["exit_reason"],
                    gross_pnl=r["gross_pnl"],
                    fee=r["fee"],
                    slippage=r["slippage"],
                    net_pnl=r["net_pnl"],
                    net_return_bps=r["net_return_bps"],
                    bars_held=r["bars_held"],
                )
                for r in rows
            ]

    async def check_and_allocate_order(
        self,
        symbol: str,
        side: str,
        limit_price: float,
        sigma_t: float,
        timestamp_ms: int,
    ) -> Optional[Tuple[float, float, float, float]]:
        """Evaluate DEC_05 Option 3 portfolio risk limits and allocate order sizing.

        Returns
        -------
        Optional[Tuple[float, float, float, float]]
            (allocated_quantity, allocated_notional, tp_price, sl_price) if approved,
            or None if blocked by exposure limits or kill switch.
        """
        acct = await self.get_latest_account_state()
        if acct.is_kill_switch_active:
            return None

        # Check existing active position in symbol
        positions = await self.get_active_positions()
        if any(p.symbol == symbol for p in positions):
            return None  # Single position per symbol

        # Check existing pending orders in symbol
        orders = await self.get_pending_orders()
        if any(o.symbol == symbol for o in orders):
            return None

        current_equity = max(100.0, acct.equity)
        max_gross_exposure = self.gross_exposure_cap_pct * current_equity

        # Existing allocated exposure = open positions notional + pending orders notional
        active_pos_exposure = sum(p.notional for p in positions)
        pending_order_exposure = sum(o.quantity * o.limit_price for o in orders)
        current_committed = active_pos_exposure + pending_order_exposure

        available_capacity = max(0.0, max_gross_exposure - current_committed)
        if available_capacity < 10.0:  # Minimum notional threshold $10
            return None

        # Sizing target: N_i = R_budget * Equity / (1.0 * sigma_t)
        sigma = max(1e-4, sigma_t)
        target_notional = (self.risk_budget_factor * current_equity) / (1.0 * sigma)
        
        # Single-asset cap: 10% of equity
        single_cap = self.single_asset_cap_pct * current_equity
        target_notional = min(target_notional, single_cap)

        # Pro-rata / Capacity constraint
        allocated_notional = min(target_notional, available_capacity)
        if allocated_notional < 10.0:
            return None

        qty = allocated_notional / limit_price

        # Asymmetric Barriers: TP = +2.5 * sigma, SL = -1.0 * sigma
        if side == "LONG":
            tp = limit_price * (1.0 + 2.5 * sigma)
            sl = limit_price * (1.0 - 1.0 * sigma)
        else:
            tp = limit_price * (1.0 - 2.5 * sigma)
            sl = limit_price * (1.0 + 1.0 * sigma)

        return qty, allocated_notional, tp, sl

    async def place_maker_order(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: float,
        limit_price: float,
        tp_price: float,
        sl_price: float,
        sigma_t: float,
        timestamp_ms: int,
    ) -> bool:
        """Record pending maker limit order in ledger."""
        conn = await self.connect()
        async with self._lock:
            await conn.execute(
                """
                INSERT INTO pending_orders (
                    order_id, symbol, side, quantity, limit_price,
                    tp_price, sl_price, created_at_ms, status, volatility_sigma
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?)
                """,
                (
                    order_id,
                    symbol,
                    side,
                    quantity,
                    limit_price,
                    tp_price,
                    sl_price,
                    timestamp_ms,
                    sigma_t,
                ),
            )
            await conn.commit()
            return True

    async def cancel_order(self, order_id: str, timestamp_ms: int) -> bool:
        """Cancel a pending maker order."""
        conn = await self.connect()
        async with self._lock:
            await conn.execute(
                "UPDATE pending_orders SET status = 'CANCELLED' WHERE order_id = ?",
                (order_id,),
            )
            await conn.commit()
            return True

    async def record_fill(
        self,
        order_id: str,
        fill_price: float,
        timestamp_ms: int,
    ) -> Optional[PositionRecord]:
        """Convert pending maker limit order into an active open position."""
        conn = await self.connect()
        async with self._lock:
            async with conn.execute(
                "SELECT * FROM pending_orders WHERE order_id = ? AND status = 'PENDING'",
                (order_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None

            # Mark order FILLED
            await conn.execute(
                "UPDATE pending_orders SET status = 'FILLED' WHERE order_id = ?",
                (order_id,),
            )

            # Insert Position
            pos_id = f"pos_{order_id}"
            notional = row["quantity"] * fill_price
            await conn.execute(
                """
                INSERT INTO positions (
                    position_id, symbol, side, quantity, entry_price, mark_price,
                    current_sl, current_tp, entry_time_ms, bars_held, volatility_sigma,
                    notional, unrealized_pnl, updated_at_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 0.0, ?)
                """,
                (
                    pos_id,
                    row["symbol"],
                    row["side"],
                    row["quantity"],
                    fill_price,
                    fill_price,
                    row["tp_price"] if row["side"] == "SHORT" else row["sl_price"],
                    row["tp_price"] if row["side"] == "LONG" else row["tp_price"],
                    timestamp_ms,
                    row["volatility_sigma"],
                    notional,
                    timestamp_ms,
                ),
            )
            await conn.commit()

        # Recalculate portfolio state
        await self._sync_account_state(timestamp_ms)
        positions = await self.get_active_positions()
        for p in positions:
            if p.position_id == pos_id:
                return p
        return None

    async def update_mark_prices(
        self,
        symbol_price_map: Dict[str, float],
        timestamp_ms: int,
    ) -> AccountState:
        """Update mark prices for open positions and sync portfolio equity curve."""
        conn = await self.connect()
        async with self._lock:
            for sym, mark_px in symbol_price_map.items():
                async with conn.execute(
                    "SELECT * FROM positions WHERE symbol = ?", (sym,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    for r in rows:
                        side = r["side"]
                        qty = r["quantity"]
                        entry_px = r["entry_price"]
                        d = 1.0 if side == "LONG" else -1.0
                        unrealized = d * (mark_px - entry_px) * qty
                        notional = qty * mark_px

                        await conn.execute(
                            """
                            UPDATE positions
                            SET mark_price = ?,
                                notional = ?,
                                unrealized_pnl = ?,
                                bars_held = bars_held + 1,
                                updated_at_ms = ?
                            WHERE position_id = ?
                            """,
                            (mark_px, notional, unrealized, timestamp_ms, r["position_id"]),
                        )
            await conn.commit()

        return await self._sync_account_state(timestamp_ms)

    async def close_position(
        self,
        position_id: str,
        exit_price: float,
        exit_reason: str,
        timestamp_ms: int,
    ) -> Optional[TradeRecord]:
        """Close active position, compute Maker-Passive fee accounting, and record trade."""
        conn = await self.connect()
        trade_rec: Optional[TradeRecord] = None

        async with self._lock:
            async with conn.execute(
                "SELECT * FROM positions WHERE position_id = ?", (position_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None

            sym = row["symbol"]
            side = row["side"]
            qty = row["quantity"]
            entry_px = row["entry_price"]
            entry_ts = row["entry_time_ms"]
            bars = row["bars_held"]

            d = 1.0 if side == "LONG" else -1.0
            n_entry = qty * entry_px
            n_exit = qty * exit_price

            # Price Return and Gross PnL
            gross_ret = d * (exit_price - entry_px) / entry_px
            gross_pnl = n_entry * gross_ret

            # Maker-Passive Fee Accounting: 4.0 bps maker fee per leg, 0.0 bps slippage
            c_maker = self.maker_fee_bps / 10_000.0
            total_fee = (n_entry + n_exit) * c_maker
            total_slip = 0.0

            net_pnl = gross_pnl - total_fee - total_slip
            net_bps = (net_pnl / n_entry) * 10_000.0

            t_id = f"tr_{position_id}_{timestamp_ms}"
            trade_rec = TradeRecord(
                trade_id=t_id,
                symbol=sym,
                side=side,
                quantity=qty,
                entry_price=entry_px,
                exit_price=exit_price,
                entry_time_ms=entry_ts,
                exit_time_ms=timestamp_ms,
                exit_reason=exit_reason,
                gross_pnl=round(gross_pnl, 4),
                fee=round(total_fee, 4),
                slippage=round(total_slip, 4),
                net_pnl=round(net_pnl, 4),
                net_return_bps=round(net_bps, 2),
                bars_held=bars,
            )

            # Insert Trade
            await conn.execute(
                """
                INSERT INTO trades (
                    trade_id, symbol, side, quantity, entry_price, exit_price,
                    entry_time_ms, exit_time_ms, exit_reason, gross_pnl, fee,
                    slippage, net_pnl, net_return_bps, bars_held
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trade_rec.trade_id,
                    trade_rec.symbol,
                    trade_rec.side,
                    trade_rec.quantity,
                    trade_rec.entry_price,
                    trade_rec.exit_price,
                    trade_rec.entry_time_ms,
                    trade_rec.exit_time_ms,
                    trade_rec.exit_reason,
                    trade_rec.gross_pnl,
                    trade_rec.fee,
                    trade_rec.slippage,
                    trade_rec.net_pnl,
                    trade_rec.net_return_bps,
                    trade_rec.bars_held,
                ),
            )

            # Remove Position
            await conn.execute("DELETE FROM positions WHERE position_id = ?", (position_id,))
            await conn.commit()

        # Update cash and equity
        await self._sync_account_state(timestamp_ms, realized_delta=trade_rec.net_pnl)
        return trade_rec

    async def emergency_kill_switch(self, timestamp_ms: int) -> AccountState:
        """Cancel all pending orders, liquidate all positions, and lock account."""
        positions = await self.get_active_positions()
        for p in positions:
            await self.close_position(
                position_id=p.position_id,
                exit_price=p.mark_price,
                exit_reason="EMERGENCY_KILL_SWITCH",
                timestamp_ms=timestamp_ms,
            )

        orders = await self.get_pending_orders()
        for o in orders:
            await self.cancel_order(o.order_id, timestamp_ms)

        conn = await self.connect()
        async with self._lock:
            await conn.execute(
                """
                UPDATE account_state
                SET is_kill_switch_active = 1,
                    timestamp_ms = ?
                WHERE id = (SELECT MAX(id) FROM account_state)
                """,
                (timestamp_ms,),
            )
            await conn.commit()

        return await self.get_latest_account_state()

    async def reset_account(self, timestamp_ms: int) -> AccountState:
        """Reset account back to clean initial state."""
        conn = await self.connect()
        async with self._lock:
            await conn.execute("DELETE FROM positions")
            await conn.execute("DELETE FROM pending_orders")
            await conn.execute("DELETE FROM trades")
            await conn.execute("DELETE FROM account_state")
            await conn.execute(
                """
                INSERT INTO account_state (
                    timestamp_ms, equity, cash, unrealized_pnl, realized_pnl,
                    peak_equity, max_drawdown_pct, gross_exposure, gross_exposure_pct,
                    is_kill_switch_active
                ) VALUES (?, ?, ?, 0.0, 0.0, ?, 0.0, 0.0, 0.0, 0)
                """,
                (timestamp_ms, self.initial_equity, self.initial_equity, self.initial_equity),
            )
            await conn.commit()
        return await self.get_latest_account_state()

    async def record_telemetry(self, timestamp_ms: int, payload: Dict[str, Any]) -> None:
        """Persist 1Hz telemetry snapshot in SQLite."""
        conn = await self.connect()
        data_str = json.dumps(payload)
        async with self._lock:
            await conn.execute(
                """
                INSERT OR REPLACE INTO telemetry_snapshots (timestamp_ms, data_json)
                VALUES (?, ?)
                """,
                (timestamp_ms, data_str),
            )
            await conn.commit()

    async def _sync_account_state(
        self,
        timestamp_ms: int,
        realized_delta: float = 0.0,
    ) -> AccountState:
        """Internal helper to calculate and persist latest account equity, drawdown, and exposure."""
        conn = await self.connect()
        async with self._lock:
            async with conn.execute(
                "SELECT * FROM account_state ORDER BY id DESC LIMIT 1"
            ) as cursor:
                prev = await cursor.fetchone()
                prev_cash = prev["cash"] if prev else self.initial_equity
                prev_realized = prev["realized_pnl"] if prev else 0.0
                prev_peak = prev["peak_equity"] if prev else self.initial_equity
                is_locked = prev["is_kill_switch_active"] if prev else 0

            # Compute current active positions totals
            async with conn.execute(
                "SELECT SUM(unrealized_pnl) AS tot_unreal, SUM(notional) AS tot_notional FROM positions"
            ) as cursor:
                p_row = await cursor.fetchone()
                tot_unreal = p_row["tot_unreal"] if p_row and p_row["tot_unreal"] else 0.0
                tot_exposure = p_row["tot_notional"] if p_row and p_row["tot_notional"] else 0.0

            cur_cash = prev_cash + realized_delta
            cur_realized = prev_realized + realized_delta
            cur_equity = cur_cash + tot_unreal

            cur_peak = max(prev_peak, cur_equity)
            dd_pct = ((cur_peak - cur_equity) / cur_peak) * 100.0 if cur_peak > 0 else 0.0
            exposure_pct = (tot_exposure / cur_equity) * 100.0 if cur_equity > 0 else 0.0

            await conn.execute(
                """
                INSERT INTO account_state (
                    timestamp_ms, equity, cash, unrealized_pnl, realized_pnl,
                    peak_equity, max_drawdown_pct, gross_exposure, gross_exposure_pct,
                    is_kill_switch_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp_ms,
                    round(cur_equity, 2),
                    round(cur_cash, 2),
                    round(tot_unreal, 2),
                    round(cur_realized, 2),
                    round(cur_peak, 2),
                    round(dd_pct, 2),
                    round(tot_exposure, 2),
                    round(exposure_pct, 2),
                    is_locked,
                ),
            )
            await conn.commit()

        return await self.get_latest_account_state()
