"""Autonomous Paper Execution Engine for Phase 6A.

Implements:
1. Two clock modes:
   - HISTORICAL_REPLAY_STREAM: High-speed or 1x streaming replay over historical Parquet data
     (strictly enforcing sealed prospective holdout boundary < 1793491200000 ms).
   - LIVE_WEBSOCKET_PAPER: Real-time 5m candle ingestion via public market REST/WebSocket polling.
2. Tiered Asset Allocation Policy:
   - Tier 1: Active Alpha Core (LINK, AVAX, SOL, ADA, BNB) - Enabled by default.
   - Tier 2: Macro Expansion Core (BTC, ETH) - Enabled with adaptive thresholds.
   - Tier 3: Shadow / Monitor-Only (XRP, DOGE, LTC, XMR) - Telemetry active, execution blocked.
3. Asymmetric Barrier Tracking (TP = +2.5 * sigma, SL = -1.0 * sigma, 24-bar horizon).
4. Maker-Passive fee accounting (4.0 bps maker fee per leg, 0.0 bps slippage).
5. 1Hz Telemetry snapshot generation and broadcasting for C# Avalonia UI.
"""

import asyncio
from datetime import datetime, timezone
from enum import Enum
import json
import math
from pathlib import Path
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Tuple

import httpx
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from pydantic import BaseModel, ConfigDict, Field

from quantum.backtesting.adapters import (
    PRIMARY_RESEARCH_UNIVERSE,
    PROSPECTIVE_HOLDOUT_START_MS,
    STRUCTURAL_BREAK_SUBGROUP,
    OOFProbabilityAdapter,
)
from quantum.backtesting.resources import BACKTEST_MAX_THREADS, enforce_backtest_thread_limits
from quantum.daemon.paper_ledger import (
    AccountState,
    PaperLedgerManager,
    PendingOrderRecord,
    PositionRecord,
    TradeRecord,
)

CANDLE_BASE_DIR = Path("data/historical/canonical/exchange=ASTER")
OOF_DIR = Path("artifacts/phase_5_4/materialized_oof")


class ClockMode(str, Enum):
    HISTORICAL_REPLAY_STREAM = "HISTORICAL_REPLAY_STREAM"
    LIVE_WEBSOCKET_PAPER = "LIVE_WEBSOCKET_PAPER"


class GateStatus(str, Enum):
    OPEN = "OPEN"
    FILTERED_VOLATILITY = "FILTERED_VOLATILITY"
    FILTERED_MARGIN = "FILTERED_MARGIN"
    TIER_BLOCKED = "TIER_BLOCKED"
    POSITION_ACTIVE = "POSITION_ACTIVE"


class SpecialistTierConfig(BaseModel):
    """Configuration for an asset's allocation tier and execution gates."""
    model_config = ConfigDict(validate_assignment=True)

    symbol: str
    tier: int = Field(ge=1, le=3)
    tier_name: str
    vol_threshold_bps: float
    prob_margin: float
    expected_profit_factor: float
    is_enabled: bool = True
    tp_multiplier: float = 2.5
    sl_multiplier: float = 1.0
    horizon_bars: int = 24


DEFAULT_TIER_CONFIGS: Dict[str, SpecialistTierConfig] = {
    # Tier 1 (Active Alpha Core - Enabled by default)
    "LINKUSDT": SpecialistTierConfig(
        symbol="LINKUSDT", tier=1, tier_name="Active Alpha Core",
        vol_threshold_bps=160.0, prob_margin=0.20, expected_profit_factor=4.702, is_enabled=True,
    ),
    "AVAXUSDT": SpecialistTierConfig(
        symbol="AVAXUSDT", tier=1, tier_name="Active Alpha Core",
        vol_threshold_bps=160.0, prob_margin=0.20, expected_profit_factor=1.931, is_enabled=True,
    ),
    "SOLUSDT": SpecialistTierConfig(
        symbol="SOLUSDT", tier=1, tier_name="Active Alpha Core",
        vol_threshold_bps=120.0, prob_margin=0.30, expected_profit_factor=1.458, is_enabled=True,
    ),
    "ADAUSDT": SpecialistTierConfig(
        symbol="ADAUSDT", tier=1, tier_name="Active Alpha Core",
        vol_threshold_bps=120.0, prob_margin=0.30, expected_profit_factor=1.075, is_enabled=True,
    ),
    "BNBUSDT": SpecialistTierConfig(
        symbol="BNBUSDT", tier=1, tier_name="Active Alpha Core",
        vol_threshold_bps=160.0, prob_margin=0.20, expected_profit_factor=1.071, is_enabled=True,
    ),
    # Tier 2 (Macro Expansion Core - Enabled with adaptive thresholds)
    "BTCUSDT": SpecialistTierConfig(
        symbol="BTCUSDT", tier=2, tier_name="Macro Expansion Core",
        vol_threshold_bps=80.0, prob_margin=0.30, expected_profit_factor=1.182, is_enabled=True,
    ),
    "ETHUSDT": SpecialistTierConfig(
        symbol="ETHUSDT", tier=2, tier_name="Macro Expansion Core",
        vol_threshold_bps=120.0, prob_margin=0.30, expected_profit_factor=1.104, is_enabled=True,
    ),
    # Tier 3 (Shadow / Monitor-Only - Paper execution blocked by default)
    "XRPUSDT": SpecialistTierConfig(
        symbol="XRPUSDT", tier=3, tier_name="Shadow Monitor-Only",
        vol_threshold_bps=120.0, prob_margin=0.30, expected_profit_factor=0.980, is_enabled=False,
    ),
    "DOGEUSDT": SpecialistTierConfig(
        symbol="DOGEUSDT", tier=3, tier_name="Shadow Monitor-Only",
        vol_threshold_bps=120.0, prob_margin=0.30, expected_profit_factor=0.637, is_enabled=False,
    ),
    "LTCUSDT": SpecialistTierConfig(
        symbol="LTCUSDT", tier=3, tier_name="Shadow Monitor-Only",
        vol_threshold_bps=120.0, prob_margin=0.30, expected_profit_factor=0.671, is_enabled=False,
    ),
    "XMRUSDT": SpecialistTierConfig(
        symbol="XMRUSDT", tier=3, tier_name="Shadow Monitor-Only",
        vol_threshold_bps=120.0, prob_margin=0.30, expected_profit_factor=0.000, is_enabled=False,
    ),
}


class SpecialistState(BaseModel):
    """Live state of an individual specialist model."""
    symbol: str
    tier: int
    is_enabled: bool
    prob_long: float = 0.33
    prob_short: float = 0.33
    prob_neutral: float = 0.34
    margin: float = 0.0
    prob_margin_threshold: float
    sigma_bps: float = 0.0
    vol_threshold_bps: float
    gate_status: GateStatus = GateStatus.FILTERED_VOLATILITY
    last_price: float = 0.0
    has_active_position: bool = False
    has_pending_order: bool = False


class TelemetrySnapshot(BaseModel):
    """Broadcast payload for WebSocket IPC to C# Avalonia client."""
    timestamp_ms: int
    clock_mode: str
    is_paused: bool
    is_kill_switch_active: bool
    account: AccountState
    active_positions_count: int
    pending_orders_count: int
    specialists: Dict[str, SpecialistState]
    recent_events: List[str] = Field(default_factory=list)


class PaperExecutionEngine:
    """Core autonomous paper execution and telemetry engine."""

    def __init__(
        self,
        ledger: PaperLedgerManager,
        tier_configs: Optional[Dict[str, SpecialistTierConfig]] = None,
        clock_mode: ClockMode = ClockMode.HISTORICAL_REPLAY_STREAM,
    ) -> None:
        enforce_backtest_thread_limits(BACKTEST_MAX_THREADS)
        self.ledger = ledger
        self.tier_configs = tier_configs or {k: v.model_copy() for k, v in DEFAULT_TIER_CONFIGS.items()}
        self.clock_mode = clock_mode
        self.is_paused = True
        self.current_timestamp_ms = int(time.time() * 1000)

        # Specialist States
        self.specialist_states: Dict[str, SpecialistState] = {
            sym: SpecialistState(
                symbol=sym,
                tier=cfg.tier,
                is_enabled=cfg.is_enabled,
                prob_margin_threshold=cfg.prob_margin,
                vol_threshold_bps=cfg.vol_threshold_bps,
            )
            for sym, cfg in self.tier_configs.items()
        }

        # Rolling candle buffers for volatility (symbol -> list of close prices)
        self.close_buffers: Dict[str, List[float]] = {sym: [] for sym in self.tier_configs}
        self.telemetry_subscribers: Set[asyncio.Queue] = set()
        self.recent_event_log: List[str] = []
        self._replay_task: Optional[asyncio.Task] = None
        self._live_task: Optional[asyncio.Task] = None

    def subscribe_telemetry(self) -> asyncio.Queue:
        """Subscribe to 1Hz telemetry broadcast queue."""
        q = asyncio.Queue(maxsize=100)
        self.telemetry_subscribers.add(q)
        return q

    def unsubscribe_telemetry(self, q: asyncio.Queue) -> None:
        """Unsubscribe from telemetry queue."""
        self.telemetry_subscribers.discard(q)

    async def broadcast_telemetry(self, snapshot: TelemetrySnapshot) -> None:
        """Broadcast telemetry snapshot to all connected WebSocket clients."""
        dead_queues = []
        for q in self.telemetry_subscribers:
            try:
                if q.full():
                    try:
                        q.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                q.put_nowait(snapshot)
            except Exception:
                dead_queues.append(q)
        for dq in dead_queues:
            self.telemetry_subscribers.discard(dq)

    def log_event(self, msg: str) -> None:
        """Append to recent event log for UI display."""
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        self.recent_event_log.append(entry)
        if len(self.recent_event_log) > 20:
            self.recent_event_log.pop(0)

    async def update_bar(
        self,
        symbol: str,
        open_px: float,
        high_px: float,
        low_px: float,
        close_px: float,
        timestamp_ms: int,
        p_long: float,
        p_short: float,
        p_neutral: float,
    ) -> None:
        """Execute causal step for an incoming 5m candle across an individual asset."""
        self.current_timestamp_ms = timestamp_ms
        cfg = self.tier_configs.get(symbol)
        if not cfg:
            return

        # 1. Update Volatility Buffer
        buf = self.close_buffers[symbol]
        buf.append(close_px)
        if len(buf) > 30:
            buf.pop(0)

        sigma_t = 0.0010  # default 10 bps
        if len(buf) >= 20:
            pct_changes = np.diff(buf[-21:]) / buf[-21:-1]
            sigma_t = float(np.std(pct_changes, ddof=1)) if len(pct_changes) > 1 else 0.0010
            sigma_t = max(1e-4, sigma_t)
        sigma_bps = 1.5 * sigma_t * 10_000.0

        # 2. Update Specialist State
        margin = max(p_long, p_short) - p_neutral
        spec = self.specialist_states[symbol]
        spec.prob_long = p_long
        spec.prob_short = p_short
        spec.prob_neutral = p_neutral
        spec.margin = round(margin, 4)
        spec.sigma_bps = round(sigma_bps, 2)
        spec.last_price = close_px

        # 3. Check and Update Active Positions for this Symbol
        positions = await self.ledger.get_active_positions()
        pos = next((p for p in positions if p.symbol == symbol), None)
        spec.has_active_position = (pos is not None)

        if pos:
            # Check Exits: Gap, Intrabar Touch, or Expiration
            side = pos.side
            entry_px = pos.entry_price
            sl_px = pos.current_sl
            tp_px = pos.current_tp
            bars = pos.bars_held + 1
            exit_trig = False
            exit_px = 0.0
            reason = ""

            # Opening gap check
            if side == "LONG":
                if open_px <= sl_px:
                    exit_px = open_px; reason = "STOP_LOSS"; exit_trig = True
                elif open_px >= tp_px:
                    exit_px = open_px; reason = "TAKE_PROFIT"; exit_trig = True
            else:
                if open_px >= sl_px:
                    exit_px = open_px; reason = "STOP_LOSS"; exit_trig = True
                elif open_px <= tp_px:
                    exit_px = open_px; reason = "TAKE_PROFIT"; exit_trig = True

            # Intrabar touches
            if not exit_trig:
                upper_touch = (high_px >= max(tp_px, sl_px) if side == "SHORT" else high_px >= tp_px)
                lower_touch = (low_px <= min(tp_px, sl_px) if side == "SHORT" else low_px <= sl_px)

                if upper_touch and lower_touch:
                    exit_px = sl_px; reason = "STOP_LOSS"; exit_trig = True
                elif (side == "LONG" and upper_touch) or (side == "SHORT" and lower_touch):
                    exit_px = tp_px; reason = "TAKE_PROFIT"; exit_trig = True
                elif (side == "LONG" and lower_touch) or (side == "SHORT" and upper_touch):
                    exit_px = sl_px; reason = "STOP_LOSS"; exit_trig = True
                elif bars >= cfg.horizon_bars:
                    exit_px = close_px; reason = "TIME_EXPIRATION"; exit_trig = True

            if exit_trig:
                closed_tr = await self.ledger.close_position(
                    position_id=pos.position_id,
                    exit_price=exit_px,
                    exit_reason=reason,
                    timestamp_ms=timestamp_ms,
                )
                if closed_tr:
                    self.log_event(
                        f"CLOSE {symbol} {side} at {exit_px:.2f} ({reason}) | PnL: ${closed_tr.net_pnl:.2f} ({closed_tr.net_return_bps:+.1f} bps)"
                    )
                spec.has_active_position = False
            else:
                # Update mark price
                await self.ledger.update_mark_prices({symbol: close_px}, timestamp_ms)

        # 4. Check Pending Maker Orders for Fill
        pending_orders = await self.ledger.get_pending_orders()
        ord_rec = next((o for o in pending_orders if o.symbol == symbol), None)
        spec.has_pending_order = (ord_rec is not None)

        if ord_rec:
            # Check if price touched limit
            filled = False
            if ord_rec.side == "LONG" and low_px <= ord_rec.limit_price:
                filled = True
            elif ord_rec.side == "SHORT" and high_px >= ord_rec.limit_price:
                filled = True

            if filled:
                pos_filled = await self.ledger.record_fill(ord_rec.order_id, ord_rec.limit_price, timestamp_ms)
                if pos_filled:
                    self.log_event(
                        f"FILL {symbol} {ord_rec.side} Maker Limit at {ord_rec.limit_price:.2f} (Qty: {pos_filled.quantity:.4f})"
                    )
                spec.has_pending_order = False
                spec.has_active_position = True

        # 5. Evaluate Gates for New Order Placement
        if spec.has_active_position or spec.has_pending_order:
            spec.gate_status = GateStatus.POSITION_ACTIVE
            return

        if not cfg.is_enabled:
            spec.gate_status = GateStatus.TIER_BLOCKED
            return

        if sigma_bps < cfg.vol_threshold_bps:
            spec.gate_status = GateStatus.FILTERED_VOLATILITY
            return

        if margin < cfg.prob_margin:
            spec.gate_status = GateStatus.FILTERED_MARGIN
            return

        # Passed all gates
        spec.gate_status = GateStatus.OPEN
        if self.is_paused:
            return

        side_signal = "LONG" if p_long > p_short else "SHORT"
        limit_px = close_px  # Post maker order at current close

        alloc = await self.ledger.check_and_allocate_order(
            symbol=symbol,
            side=side_signal,
            limit_price=limit_px,
            sigma_t=sigma_t,
            timestamp_ms=timestamp_ms,
        )
        if alloc:
            qty, notional, tp, sl = alloc
            o_id = f"ord_{symbol}_{timestamp_ms}"
            placed = await self.ledger.place_maker_order(
                order_id=o_id,
                symbol=symbol,
                side=side_signal,
                quantity=qty,
                limit_price=limit_px,
                tp_price=tp,
                sl_price=sl,
                sigma_t=sigma_t,
                timestamp_ms=timestamp_ms,
            )
            if placed:
                spec.has_pending_order = True
                self.log_event(
                    f"ORDER {symbol} {side_signal} Qty: {qty:.4f} @ {limit_px:.2f} (TP: {tp:.2f}, SL: {sl:.2f})"
                )

    async def generate_telemetry_snapshot(self) -> TelemetrySnapshot:
        """Create consolidated real-time telemetry snapshot."""
        acct = await self.ledger.get_latest_account_state()
        positions = await self.ledger.get_active_positions()
        orders = await self.ledger.get_pending_orders()

        snapshot = TelemetrySnapshot(
            timestamp_ms=self.current_timestamp_ms,
            clock_mode=self.clock_mode.value,
            is_paused=self.is_paused,
            is_kill_switch_active=acct.is_kill_switch_active,
            account=acct,
            active_positions_count=len(positions),
            pending_orders_count=len(orders),
            specialists={sym: st.model_copy() for sym, st in self.specialist_states.items()},
            recent_events=list(self.recent_event_log),
        )
        return snapshot

    async def start_historical_replay(
        self,
        symbols: Optional[List[str]] = None,
        max_bars: Optional[int] = None,
        delay_seconds: float = 0.0,
    ) -> None:
        """Run high-speed streaming replay over historical Parquet candles and OOF signals."""
        target_symbols = symbols or list(PRIMARY_RESEARCH_UNIVERSE)
        print(f"[REPLAY] Initializing historical stream over {len(target_symbols)} symbols...")
        self.clock_mode = ClockMode.HISTORICAL_REPLAY_STREAM
        self.is_paused = False

        # Load candle and OOF series
        candle_data: Dict[str, pd.DataFrame] = {}
        oof_signals: Dict[str, Dict[int, Tuple[float, float, float]]] = {}
        adapter = OOFProbabilityAdapter(oof_dir=OOF_DIR)

        for sym in target_symbols:
            c_dir = CANDLE_BASE_DIR / f"symbol={sym}" / "timeframe=5m"
            files = sorted(c_dir.glob("*.parquet"))
            dfs = [pq.ParquetFile(f).read(["open_time_ms", "open", "high", "low", "close"]).to_pandas() for f in files]
            df_c = pd.concat(dfs, ignore_index=True).sort_values("open_time_ms").drop_duplicates("open_time_ms").reset_index(drop=True)
            candle_data[sym] = df_c

            # Load OOF
            oof_df = adapter.load_oof_dataset(sym, fold=None)
            sig_dict = {}
            for r in oof_df.itertuples():
                sig_dict[int(r.open_time_ms)] = (float(r.raw_prob_m1), float(r.raw_prob_0), float(r.raw_prob_p1))
            oof_signals[sym] = sig_dict

        # Collect unique timestamps across symbols (strictly before holdout)
        all_ts_set = set()
        for df in candle_data.values():
            all_ts_set.update(df["open_time_ms"].tolist())

        sorted_ts = sorted(ts for ts in all_ts_set if ts < PROSPECTIVE_HOLDOUT_START_MS)
        if max_bars:
            sorted_ts = sorted_ts[:max_bars]

        print(f"[REPLAY] Stepping through {len(sorted_ts)} sequential 5m bars...")

        # Indexed candle lookups
        candle_maps = {sym: df.set_index("open_time_ms").to_dict(orient="index") for sym, df in candle_data.items()}

        step_count = 0
        for ts in sorted_ts:
            if self.is_paused:
                break

            for sym in target_symbols:
                c_map = candle_maps[sym]
                if ts in c_map:
                    row = c_map[ts]
                    o = float(row["open"])
                    h = float(row["high"])
                    l = float(row["low"])
                    c = float(row["close"])

                    sig = oof_signals[sym].get(ts, (0.33, 0.34, 0.33))
                    pm1, p0, pp1 = sig

                    await self.update_bar(
                        symbol=sym,
                        open_px=o,
                        high_px=h,
                        low_px=l,
                        close_px=c,
                        timestamp_ms=ts,
                        p_long=pp1,
                        p_short=pm1,
                        p_neutral=p0,
                    )

            step_count += 1
            if step_count % 10 == 0 or delay_seconds > 0:
                snap = await self.generate_telemetry_snapshot()
                await self.broadcast_telemetry(snap)
                if delay_seconds > 0:
                    await asyncio.sleep(delay_seconds)

        print(f"[REPLAY] Completed {step_count} bars.")
        final_snap = await self.generate_telemetry_snapshot()
        await self.broadcast_telemetry(final_snap)
        self.is_paused = True

    async def start_live_paper_poll(
        self,
        symbols: Optional[List[str]] = None,
        poll_interval_seconds: float = 5.0,
    ) -> None:
        """Poll public exchange endpoints for live 5m candles and update paper engine."""
        target_symbols = symbols or list(PRIMARY_RESEARCH_UNIVERSE)
        self.clock_mode = ClockMode.LIVE_WEBSOCKET_PAPER
        self.is_paused = False
        print(f"[LIVE] Starting Live Paper Trading Poll across {len(target_symbols)} symbols...")

        async with httpx.AsyncClient(timeout=10.0) as client:
            while not self.is_paused:
                try:
                    for sym in target_symbols:
                        # Binance public futures kline endpoint (AsterDEX proxy)
                        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval=5m&limit=25"
                        resp = await client.get(url)
                        if resp.status_code == 200:
                            data = resp.json()
                            if data:
                                latest = data[-1]
                                ts = int(latest[0])
                                o = float(latest[1])
                                h = float(latest[2])
                                l = float(latest[3])
                                c = float(latest[4])

                                # For live mode, generate balanced fallback prediction if no local model inference hook
                                p_l = 0.35 if c > o else 0.30
                                p_s = 0.35 if c < o else 0.30
                                p_n = 1.0 - (p_l + p_s)

                                await self.update_bar(
                                    symbol=sym,
                                    open_px=o,
                                    high_px=h,
                                    low_px=l,
                                    close_px=c,
                                    timestamp_ms=ts,
                                    p_long=p_l,
                                    p_short=p_s,
                                    p_neutral=p_n,
                                )

                    snap = await self.generate_telemetry_snapshot()
                    await self.broadcast_telemetry(snap)
                    await self.ledger.record_telemetry(snap.timestamp_ms, snap.model_dump())
                except Exception as e:
                    self.log_event(f"Live poll error: {e}")

                await asyncio.sleep(poll_interval_seconds)

    def pause(self) -> None:
        """Pause execution loop."""
        self.is_paused = True
        self.log_event("ENGINE_PAUSED")

    def resume(self) -> None:
        """Resume execution loop."""
        self.is_paused = False
        self.log_event("ENGINE_RESUMED")

    async def emergency_kill_switch(self) -> AccountState:
        """Trigger emergency kill switch."""
        self.is_paused = True
        now_ms = int(time.time() * 1000)
        state = await self.ledger.emergency_kill_switch(now_ms)
        self.log_event("EMERGENCY KILL SWITCH ACTIVATED: ALL POSITIONS LIQUIDATED, ACCOUNT LOCKED")
        snap = await self.generate_telemetry_snapshot()
        await self.broadcast_telemetry(snap)
        return state
