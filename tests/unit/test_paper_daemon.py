"""Unit and Integration Qualification for Phase 6A Paper-Trading Daemon & Telemetry Server.

Tests:
1. SQLite Ledger persistence, schema integrity, and initial equity state.
2. DEC_05 Option 3 risk envelope: 30% gross exposure cap & volatility risk-budget sizing.
3. Position lifecycle and Maker-Passive fee accounting (4.0 bps maker fee per leg).
4. Emergency Kill-Switch behavior (cancels orders, closes positions, locks account).
5. Paper Execution Engine gate evaluation (Tier blocking, Volatility filter, Probability margin).
6. REST API endpoints (/health, /research/summary, /paper/portfolio, /paper/tiers, /paper/control).
7. WebSocket streaming telemetry endpoint (/ws/v1/telemetry) schema and broadcast.
8. Historical Replay holdout seal verification (< 1793491200000 ms).
"""

import asyncio
import json
from pathlib import Path
import tempfile
import time
from typing import Any, Dict, Generator, List

from fastapi.testclient import TestClient
import numpy as np
import pytest

from quantum.backtesting.adapters import PROSPECTIVE_HOLDOUT_START_MS
from quantum.backtesting.resources import BACKTEST_MAX_THREADS, enforce_backtest_thread_limits
from quantum.daemon.paper_engine import (
    ClockMode,
    DEFAULT_TIER_CONFIGS,
    GateStatus,
    PaperExecutionEngine,
    SpecialistState,
    SpecialistTierConfig,
    TelemetrySnapshot,
)
from quantum.daemon.paper_ledger import (
    AccountState,
    PaperLedgerManager,
    PendingOrderRecord,
    PositionRecord,
    TradeRecord,
)
from quantum.daemon.server import create_app


@pytest.fixture(autouse=True)
def enforce_threads() -> None:
    enforce_backtest_thread_limits(BACKTEST_MAX_THREADS)


@pytest.fixture
def temp_db_path() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        yield Path(tmp_dir) / "test_paper.db"


@pytest.mark.asyncio
async def test_ledger_initialization_and_initial_equity(temp_db_path: Path) -> None:
    """Verify SQLite ledger creates schema and sets $10,000 initial equity."""
    ledger = PaperLedgerManager(db_path=temp_db_path, initial_equity=10_000.0)
    await ledger.initialize()

    acct = await ledger.get_latest_account_state()
    assert acct.equity == 10_000.0
    assert acct.cash == 10_000.0
    assert acct.unrealized_pnl == 0.0
    assert acct.realized_pnl == 0.0
    assert acct.gross_exposure == 0.0
    assert acct.gross_exposure_pct == 0.0
    assert acct.max_drawdown_pct == 0.0
    assert not acct.is_kill_switch_active

    await ledger.close()


@pytest.mark.asyncio
async def test_ledger_dec05_exposure_cap_and_sizing(temp_db_path: Path) -> None:
    """Verify DEC_05 Option 3 30% gross exposure ceiling and volatility risk budgeting."""
    ledger = PaperLedgerManager(
        db_path=temp_db_path,
        initial_equity=10_000.0,
        gross_exposure_cap_pct=0.30,  # 30% cap = $3,000 max exposure
        single_asset_cap_pct=0.10,     # 10% single asset cap = $1,000 max notional
        risk_budget_bps=30.0,          # 30 bps risk budget
    )
    await ledger.initialize()

    # Asset 1: Sizing = (0.003 * 10,000) / (1.0 * 0.05) = 30 / 0.05 = $600 notional
    now_ms = 1750000000000
    res1 = await ledger.check_and_allocate_order("SOLUSDT", "LONG", 150.0, 0.05, now_ms)
    assert res1 is not None
    qty1, notional1, tp1, sl1 = res1
    assert abs(notional1 - 600.0) < 1.0
    assert tp1 > 150.0  # Asymmetric TP
    assert sl1 < 150.0  # Asymmetric SL

    await ledger.place_maker_order("ord_sol_1", "SOLUSDT", "LONG", qty1, 150.0, tp1, sl1, 0.05, now_ms)
    await ledger.record_fill("ord_sol_1", 150.0, now_ms)

    # Check exposure
    acct = await ledger.get_latest_account_state()
    assert abs(acct.gross_exposure - 600.0) < 1.0
    assert abs(acct.gross_exposure_pct - 6.0) < 0.2

    # Place orders until approaching the $3,000 ceiling (30% cap)
    # Asset 2: Target notional $1,000 (capped by 10% single asset cap)
    res2 = await ledger.check_and_allocate_order("AVAXUSDT", "LONG", 30.0, 0.02, now_ms)
    assert res2 is not None
    qty2, notional2, tp2, sl2 = res2
    assert abs(notional2 - 1000.0) < 1.0
    await ledger.place_maker_order("ord_avax_1", "AVAXUSDT", "LONG", qty2, 30.0, tp2, sl2, 0.02, now_ms)
    await ledger.record_fill("ord_avax_1", 30.0, now_ms)

    # Asset 3: Target notional $1,000
    res3 = await ledger.check_and_allocate_order("LINKUSDT", "LONG", 20.0, 0.02, now_ms)
    assert res3 is not None
    qty3, notional3, tp3, sl3 = res3
    assert abs(notional3 - 1000.0) < 1.0
    await ledger.place_maker_order("ord_link_1", "LINKUSDT", "LONG", qty3, 20.0, tp3, sl3, 0.02, now_ms)
    await ledger.record_fill("ord_link_1", 20.0, now_ms)

    # Current exposure: 600 + 1000 + 1000 = $2600. Remaining capacity = $400.
    # Asset 4: Target notional $1,000, but only $400 capacity available
    res4 = await ledger.check_and_allocate_order("ADAUSDT", "LONG", 0.50, 0.02, now_ms)
    assert res4 is not None
    qty4, notional4, tp4, sl4 = res4
    assert abs(notional4 - 400.0) < 1.0  # Scaled down to remaining capacity

    await ledger.place_maker_order("ord_ada_1", "ADAUSDT", "LONG", qty4, 0.50, tp4, sl4, 0.02, now_ms)
    await ledger.record_fill("ord_ada_1", 0.50, now_ms)

    # Now total exposure is $3,000 (30.0% cap reached). Next order must be rejected!
    res5 = await ledger.check_and_allocate_order("BNBUSDT", "LONG", 500.0, 0.02, now_ms)
    assert res5 is None  # Blocked by DEC_05 30% gross exposure ceiling

    await ledger.close()


@pytest.mark.asyncio
async def test_ledger_maker_passive_fee_and_trade_close(temp_db_path: Path) -> None:
    """Verify Maker-Passive fee accounting (4.0 bps maker fee per leg, 0.0 bps slippage)."""
    ledger = PaperLedgerManager(
        db_path=temp_db_path,
        initial_equity=10_000.0,
        maker_fee_bps=4.0,
        slippage_bps=0.0,
    )
    await ledger.initialize()

    now_ms = 1750000000000
    res = await ledger.check_and_allocate_order("SOLUSDT", "LONG", 100.0, 0.02, now_ms)
    assert res is not None
    qty, notional, tp, sl = res

    await ledger.place_maker_order("ord_sol", "SOLUSDT", "LONG", qty, 100.0, tp, sl, 0.02, now_ms)
    pos = await ledger.record_fill("ord_sol", 100.0, now_ms)
    assert pos is not None

    # Simulate price moving to TP (+5% = 105.0)
    exit_px = 105.0
    exit_ms = now_ms + 300_000 * 5  # 5 bars later
    closed_tr = await ledger.close_position(pos.position_id, exit_px, "TAKE_PROFIT", exit_ms)
    assert closed_tr is not None
    assert closed_tr.symbol == "SOLUSDT"
    assert closed_tr.exit_reason == "TAKE_PROFIT"
    assert closed_tr.exit_price == 105.0

    # Expected gross pnl = qty * (105 - 100) = qty * 5
    # Expected fee = (qty * 100 + qty * 105) * 0.0004
    entry_notional = qty * 100.0
    exit_notional = qty * 105.0
    expected_gross = exit_notional - entry_notional
    expected_fee = (entry_notional + exit_notional) * 0.0004
    expected_net = expected_gross - expected_fee

    assert abs(closed_tr.gross_pnl - expected_gross) < 0.01
    assert abs(closed_tr.fee - expected_fee) < 0.01
    assert abs(closed_tr.net_pnl - expected_net) < 0.01
    assert closed_tr.slippage == 0.0  # Zero slippage on maker limit order

    # Verify account state
    acct = await ledger.get_latest_account_state()
    assert abs(acct.equity - (10_000.0 + expected_net)) < 0.02
    assert acct.gross_exposure == 0.0  # Position closed

    await ledger.close()


@pytest.mark.asyncio
async def test_emergency_kill_switch(temp_db_path: Path) -> None:
    """Verify Kill-Switch immediately cancels pending orders, liquidates positions, and locks account."""
    ledger = PaperLedgerManager(db_path=temp_db_path, initial_equity=10_000.0)
    await ledger.initialize()

    now_ms = 1750000000000
    res = await ledger.check_and_allocate_order("AVAXUSDT", "LONG", 30.0, 0.03, now_ms)
    assert res is not None
    qty, notional, tp, sl = res

    await ledger.place_maker_order("ord_avax_fill", "AVAXUSDT", "LONG", qty, 30.0, tp, sl, 0.03, now_ms)
    await ledger.record_fill("ord_avax_fill", 30.0, now_ms)

    # Place a pending order that is unfilled
    await ledger.place_maker_order("ord_link_pend", "LINKUSDT", "LONG", 10.0, 15.0, 18.0, 14.0, 0.03, now_ms)

    # Verify active state
    positions_before = await ledger.get_active_positions()
    orders_before = await ledger.get_pending_orders()
    assert len(positions_before) == 1
    assert len(orders_before) == 1

    # Trigger Emergency Kill Switch
    acct_locked = await ledger.emergency_kill_switch(now_ms + 60_000)
    assert acct_locked.is_kill_switch_active

    # Check that positions are liquidated and pending orders cancelled
    positions_after = await ledger.get_active_positions()
    orders_after = await ledger.get_pending_orders()
    assert len(positions_after) == 0
    assert len(orders_after) == 0

    # Verify order placement is blocked while kill switch is active
    res_blocked = await ledger.check_and_allocate_order("SOLUSDT", "LONG", 150.0, 0.02, now_ms + 120_000)
    assert res_blocked is None

    await ledger.close()


@pytest.mark.asyncio
async def test_engine_tiered_gate_evaluation(temp_db_path: Path) -> None:
    """Verify Tier 1, Tier 2, and Tier 3 gate evaluation (volatility, margin, tier block)."""
    ledger = PaperLedgerManager(db_path=temp_db_path, initial_equity=10_000.0)
    await ledger.initialize()

    engine = PaperExecutionEngine(ledger=ledger, tier_configs=DEFAULT_TIER_CONFIGS)
    engine.is_paused = False

    now_ms = 1750000000000

    # 1. Tier 3 Shadow Asset (XRPUSDT) -> Must be blocked by TIER_BLOCKED
    await engine.update_bar(
        symbol="XRPUSDT",
        open_px=0.50, high_px=0.52, low_px=0.49, close_px=0.51,
        timestamp_ms=now_ms,
        p_long=0.60, p_short=0.10, p_neutral=0.30,  # Margin = 0.30
    )
    assert engine.specialist_states["XRPUSDT"].gate_status == GateStatus.TIER_BLOCKED

    # 2. Tier 1 Asset (SOLUSDT, threshold 120 bps, margin 0.30)
    # Case A: Low volatility (sigma = 0.0005 -> 1.5 * sigma = 7.5 bps < 120 bps) -> FILTERED_VOLATILITY
    for _ in range(25):
        engine.close_buffers["SOLUSDT"].append(150.0)  # zero return volatility

    await engine.update_bar(
        symbol="SOLUSDT",
        open_px=150.0, high_px=150.1, low_px=149.9, close_px=150.0,
        timestamp_ms=now_ms,
        p_long=0.65, p_short=0.10, p_neutral=0.25,  # Margin = 0.40 >= 0.30
    )
    assert engine.specialist_states["SOLUSDT"].gate_status == GateStatus.FILTERED_VOLATILITY

    # Case B: High volatility (simulate fluctuating prices to raise sigma >= 120 bps)
    engine.close_buffers["SOLUSDT"].clear()
    px = 150.0
    for idx in range(25):
        px = px * (1.02 if idx % 2 == 0 else 0.98)  # 2% return swings
        engine.close_buffers["SOLUSDT"].append(px)

    # But with low probability margin (0.35 - 0.34 = 0.01 < 0.30) -> FILTERED_MARGIN
    await engine.update_bar(
        symbol="SOLUSDT",
        open_px=150.0, high_px=152.0, low_px=148.0, close_px=150.0,
        timestamp_ms=now_ms + 300_000,
        p_long=0.35, p_short=0.31, p_neutral=0.34,
    )
    assert engine.specialist_states["SOLUSDT"].gate_status == GateStatus.FILTERED_MARGIN

    # Case C: High volatility AND high margin (0.65 - 0.25 = 0.40 >= 0.30) -> OPEN
    await engine.update_bar(
        symbol="SOLUSDT",
        open_px=150.0, high_px=152.0, low_px=148.0, close_px=150.0,
        timestamp_ms=now_ms + 600_000,
        p_long=0.65, p_short=0.10, p_neutral=0.25,
    )
    assert engine.specialist_states["SOLUSDT"].gate_status == GateStatus.OPEN
    # Pending order should have been created
    orders = await ledger.get_pending_orders()
    assert any(o.symbol == "SOLUSDT" for o in orders)

    await ledger.close()


def test_fastapi_rest_endpoints(temp_db_path: Path) -> None:
    """Test REST API endpoints using FastAPI TestClient."""
    ledger = PaperLedgerManager(db_path=temp_db_path, initial_equity=10_000.0)
    engine = PaperExecutionEngine(ledger=ledger, tier_configs=DEFAULT_TIER_CONFIGS)
    app = create_app(ledger=ledger, engine=engine)

    with TestClient(app) as client:
        # 1. Health check
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "clock_mode" in data

        # 2. Research summary
        resp_res = client.get("/api/v1/research/summary")
        assert resp_res.status_code == 200
        summary = resp_res.json()
        assert "phase_5_5_conclusion" in summary
        assert "phase_5_6_grid_summary" in summary

        # 3. Portfolio
        resp_port = client.get("/api/v1/paper/portfolio")
        assert resp_port.status_code == 200
        p_data = resp_port.json()
        assert p_data["account"]["equity"] == 10_000.0
        assert isinstance(p_data["active_positions"], list)

        # 4. Tiers policy
        resp_tiers = client.get("/api/v1/paper/tiers")
        assert resp_tiers.status_code == 200
        t_data = resp_tiers.json()
        assert "LINKUSDT" in t_data["tiers"]
        assert t_data["tiers"]["LINKUSDT"]["tier"] == 1
        assert t_data["tiers"]["BTCUSDT"]["tier"] == 2
        assert not t_data["tiers"]["XRPUSDT"]["is_enabled"]  # Tier 3 disabled

        # 5. Control commands: PAUSE & RESUME
        resp_pause = client.post("/api/v1/paper/control", json={"command": "PAUSE"})
        assert resp_pause.status_code == 200
        assert resp_pause.json()["is_paused"] is True

        resp_resume = client.post("/api/v1/paper/control", json={"command": "RESUME"})
        assert resp_resume.status_code == 200
        assert resp_resume.json()["is_paused"] is False

        # 6. Control command: UPDATE_TIER_CONFIG
        resp_upd = client.post(
            "/api/v1/paper/control",
            json={"command": "UPDATE_TIER_CONFIG", "params": {"symbol": "BTCUSDT", "vol_threshold_bps": 95.0}},
        )
        assert resp_upd.status_code == 200
        assert resp_upd.json()["config"]["vol_threshold_bps"] == 95.0

        # 7. Control command: EMERGENCY_KILL_SWITCH
        resp_kill = client.post("/api/v1/paper/control", json={"command": "EMERGENCY_KILL_SWITCH"})
        assert resp_kill.status_code == 200
        assert resp_kill.json()["status"] == "EXECUTED"
        assert resp_kill.json()["account"]["is_kill_switch_active"] is True


def test_websocket_telemetry_stream(temp_db_path: Path) -> None:
    """Test WebSocket telemetry endpoint delivers valid 1Hz snapshot schema."""
    ledger = PaperLedgerManager(db_path=temp_db_path, initial_equity=10_000.0)
    engine = PaperExecutionEngine(ledger=ledger, tier_configs=DEFAULT_TIER_CONFIGS)
    app = create_app(ledger=ledger, engine=engine)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/v1/telemetry") as websocket:
            # First message is initial state snapshot
            raw_msg = websocket.receive_text()
            msg = json.loads(raw_msg)
            assert "timestamp_ms" in msg
            assert "account" in msg
            assert msg["account"]["equity"] == 10_000.0
            assert "specialists" in msg
            assert "LINKUSDT" in msg["specialists"]
            assert msg["specialists"]["LINKUSDT"]["tier"] == 1
            assert "BTCUSDT" in msg["specialists"]
            assert "gate_status" in msg["specialists"]["LINKUSDT"]


@pytest.mark.asyncio
async def test_replay_holdout_boundary_protection(temp_db_path: Path) -> None:
    """Verify Replay mode halts before holdout boundary (< 1793491200000 ms)."""
    ledger = PaperLedgerManager(db_path=temp_db_path, initial_equity=10_000.0)
    await ledger.initialize()

    engine = PaperExecutionEngine(ledger=ledger, tier_configs=DEFAULT_TIER_CONFIGS)
    # Test small 10-bar replay over BTCUSDT
    await engine.start_historical_replay(symbols=["BTCUSDT"], max_bars=10)

    assert engine.current_timestamp_ms < PROSPECTIVE_HOLDOUT_START_MS
    assert engine.is_paused is True

    await ledger.close()
