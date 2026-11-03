"""FastAPI and WebSocket IPC Telemetry Server for C# Avalonia Desktop Client.

Implements:
1. GET /api/v1/health: Daemon health, clock mode, and kill switch status.
2. GET /api/v1/research/summary: Serves consolidated JSON from Phase 5.5 and Phase 5.6 artifacts.
3. GET /api/v1/paper/portfolio: Real-time paper portfolio equity, drawdown, exposure, and trades from SQLite.
4. GET /api/v1/paper/tiers: Tiered asset allocation policy (Active Alpha Core, Macro Expansion, Shadow).
5. POST /api/v1/paper/control: Commands (START_REPLAY, START_LIVE_PAPER, PAUSE, RESUME, EMERGENCY_KILL_SWITCH, UPDATE_TIER_CONFIG).
6. WS /ws/v1/telemetry: 1Hz streaming broadcast of specialist model probabilities, barrier widths, gate status, and PnL.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import Body, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from quantum.backtesting.resources import BACKTEST_MAX_THREADS, enforce_backtest_thread_limits
from quantum.daemon.paper_engine import (
    ClockMode,
    PaperExecutionEngine,
    SpecialistTierConfig,
    TelemetrySnapshot,
)
from quantum.daemon.paper_ledger import (
    DEFAULT_DB_PATH,
    AccountState,
    PaperLedgerManager,
    PositionRecord,
    TradeRecord,
)

PHASE55_CONCLUSION_PATH = Path("artifacts/phase_5_5/phase_5_5_final_conclusion.json")
PHASE55_PORTFOLIO_PATH = Path("artifacts/phase_5_5/portfolio_evaluation.json")
PHASE56_OVERLAY_PATH = Path("artifacts/phase_5_6/overlay_validation_report.json")


class ControlCommandRequest(BaseModel):
    """Payload for POST /api/v1/paper/control."""
    command: str = Field(description="START_REPLAY, START_LIVE_PAPER, PAUSE, RESUME, EMERGENCY_KILL_SWITCH, RESET_ACCOUNT, UPDATE_TIER_CONFIG")
    params: Dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    clock_mode: str
    is_paused: bool
    is_kill_switch_active: bool
    current_timestamp_ms: int
    active_positions_count: int
    pending_orders_count: int
    active_subscribers_count: int


def create_app(
    ledger: Optional[PaperLedgerManager] = None,
    engine: Optional[PaperExecutionEngine] = None,
) -> FastAPI:
    """Create and configure FastAPI application for daemon and IPC telemetry."""
    enforce_backtest_thread_limits(BACKTEST_MAX_THREADS)

    app_ledger = ledger or PaperLedgerManager(db_path=DEFAULT_DB_PATH)
    app_engine = engine or PaperExecutionEngine(ledger=app_ledger)

    @asynccontextmanager
    async def lifespan(app_instance: FastAPI) -> AsyncGenerator[None, None]:
        await app_ledger.initialize()
        yield
        app_engine.pause()
        await app_ledger.close()

    app = FastAPI(
        title="QUANTUM Phase 6A Paper-Trading & IPC Telemetry Daemon",
        version="6.0.0",
        description="High-performance IPC bridge for C# Avalonia Desktop Trading Desk Client",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/v1/health", response_model=HealthResponse)
    async def get_health() -> HealthResponse:
        """Health check endpoint."""
        acct = await app_ledger.get_latest_account_state()
        positions = await app_ledger.get_active_positions()
        orders = await app_ledger.get_pending_orders()
        return HealthResponse(
            status="ok",
            clock_mode=app_engine.clock_mode.value,
            is_paused=app_engine.is_paused,
            is_kill_switch_active=acct.is_kill_switch_active,
            current_timestamp_ms=app_engine.current_timestamp_ms,
            active_positions_count=len(positions),
            pending_orders_count=len(orders),
            active_subscribers_count=len(app_engine.telemetry_subscribers),
        )

    @app.get("/api/v1/research/summary")
    async def get_research_summary() -> Dict[str, Any]:
        """Serve consolidated JSON summaries from Phase 5.5 and Phase 5.6 artifacts."""
        p55_conclusion = {}
        p55_portfolio = {}
        p56_overlay = {}

        if PHASE55_CONCLUSION_PATH.exists():
            with open(PHASE55_CONCLUSION_PATH, encoding="utf-8") as f:
                p55_conclusion = json.load(f)

        if PHASE55_PORTFOLIO_PATH.exists():
            with open(PHASE55_PORTFOLIO_PATH, encoding="utf-8") as f:
                p55_portfolio = json.load(f)

        if PHASE56_OVERLAY_PATH.exists():
            with open(PHASE56_OVERLAY_PATH, encoding="utf-8") as f:
                p56_overlay = json.load(f)

        return {
            "phase_5_5_conclusion": p55_conclusion,
            "phase_5_5_portfolio": p55_portfolio,
            "phase_5_6_overlay_optimal": p56_overlay.get("optimal_configuration"),
            "phase_5_6_grid_summary": {
                k: {
                    "trades": v["combined_primary_metrics"]["trade_count"],
                    "gross_exp_bps": v["combined_primary_metrics"]["gross_expectancy_bps"],
                    "maker_passive_net_bps": v["combined_primary_metrics"]["maker_passive"]["net_expectancy_bps"],
                    "maker_passive_pf": v["combined_primary_metrics"]["maker_passive"]["profit_factor"],
                    "portfolio_net_return_pct": v["portfolio_maker_passive"]["net_return_pct"],
                    "portfolio_max_dd_pct": v["portfolio_maker_passive"]["max_drawdown_pct"],
                }
                for k, v in p56_overlay.get("full_grid_results", {}).items()
            },
        }

    @app.get("/api/v1/paper/portfolio")
    async def get_paper_portfolio() -> Dict[str, Any]:
        """Fetch current portfolio state, active positions, pending orders, and recent trades."""
        acct = await app_ledger.get_latest_account_state()
        positions = await app_ledger.get_active_positions()
        orders = await app_ledger.get_pending_orders()
        trades = await app_ledger.get_recent_trades(limit=50)

        return {
            "account": acct.model_dump(),
            "active_positions": [p.model_dump() for p in positions],
            "pending_orders": [o.model_dump() for o in orders],
            "recent_trades": [t.model_dump() for t in trades],
        }

    @app.get("/api/v1/paper/tiers")
    async def get_tiered_policy() -> Dict[str, Any]:
        """Return the tiered asset allocation policy and thresholds."""
        return {
            "tiers": {
                sym: cfg.model_dump() for sym, cfg in app_engine.tier_configs.items()
            },
            "summary": {
                "tier_1_active_core": ["LINKUSDT", "AVAXUSDT", "SOLUSDT", "ADAUSDT", "BNBUSDT"],
                "tier_2_macro_core": ["BTCUSDT", "ETHUSDT"],
                "tier_3_shadow_monitor": ["XRPUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"],
            },
        }

    @app.post("/api/v1/paper/control")
    async def post_control_command(req: ControlCommandRequest = Body(...)) -> Dict[str, Any]:
        """Process operator commands: START_REPLAY, START_LIVE_PAPER, PAUSE, RESUME, EMERGENCY_KILL_SWITCH."""
        cmd = req.command.upper()
        params = req.params

        if cmd == "PAUSE":
            app_engine.pause()
            return {"command": "PAUSE", "status": "acknowledged", "is_paused": True}

        elif cmd == "RESUME":
            app_engine.resume()
            return {"command": "RESUME", "status": "acknowledged", "is_paused": False}

        elif cmd == "EMERGENCY_KILL_SWITCH":
            state = await app_engine.emergency_kill_switch()
            return {
                "command": "EMERGENCY_KILL_SWITCH",
                "status": "EXECUTED",
                "message": "All positions liquidated, orders cancelled, account locked.",
                "account": state.model_dump(),
            }

        elif cmd == "RESET_ACCOUNT":
            now_ms = int(time.time() * 1000)
            state = await app_ledger.reset_account(now_ms)
            app_engine.resume()
            return {
                "command": "RESET_ACCOUNT",
                "status": "EXECUTED",
                "account": state.model_dump(),
            }

        elif cmd == "UPDATE_TIER_CONFIG":
            sym = params.get("symbol")
            if not sym or sym not in app_engine.tier_configs:
                raise HTTPException(status_code=400, detail=f"Invalid or missing symbol: {sym}")
            cfg = app_engine.tier_configs[sym]
            if "is_enabled" in params:
                cfg.is_enabled = bool(params["is_enabled"])
            if "vol_threshold_bps" in params:
                cfg.vol_threshold_bps = float(params["vol_threshold_bps"])
            if "prob_margin" in params:
                cfg.prob_margin = float(params["prob_margin"])
            if "tier" in params:
                cfg.tier = int(params["tier"])

            # Sync specialist state
            app_engine.specialist_states[sym].is_enabled = cfg.is_enabled
            app_engine.specialist_states[sym].vol_threshold_bps = cfg.vol_threshold_bps
            app_engine.specialist_states[sym].prob_margin_threshold = cfg.prob_margin
            app_engine.log_event(f"UPDATE_CONFIG for {sym}: enabled={cfg.is_enabled}, vol={cfg.vol_threshold_bps}bps")
            return {"command": "UPDATE_TIER_CONFIG", "status": "updated", "config": cfg.model_dump()}

        elif cmd == "START_REPLAY":
            symbols = params.get("symbols")
            max_bars = params.get("max_bars", 500)
            delay = float(params.get("delay_seconds", 0.0))

            if app_engine._replay_task and not app_engine._replay_task.done():
                app_engine._replay_task.cancel()

            app_engine._replay_task = asyncio.create_task(
                app_engine.start_historical_replay(
                    symbols=symbols, max_bars=max_bars, delay_seconds=delay
                )
            )
            return {
                "command": "START_REPLAY",
                "status": "LAUNCHED",
                "mode": ClockMode.HISTORICAL_REPLAY_STREAM.value,
                "max_bars": max_bars,
            }

        elif cmd == "START_LIVE_PAPER":
            symbols = params.get("symbols")
            poll_int = float(params.get("poll_interval_seconds", 5.0))

            if app_engine._live_task and not app_engine._live_task.done():
                app_engine._live_task.cancel()

            app_engine._live_task = asyncio.create_task(
                app_engine.start_live_paper_poll(symbols=symbols, poll_interval_seconds=poll_int)
            )
            return {
                "command": "START_LIVE_PAPER",
                "status": "LAUNCHED",
                "mode": ClockMode.LIVE_WEBSOCKET_PAPER.value,
                "poll_interval_seconds": poll_int,
            }

        else:
            raise HTTPException(status_code=400, detail=f"Unknown command: {cmd}")

    @app.websocket("/ws/v1/telemetry")
    async def websocket_telemetry_endpoint(websocket: WebSocket) -> None:
        """Stream real-time 1Hz telemetry snapshots for the C# Avalonia desktop UI client."""
        await websocket.accept()
        q = app_engine.subscribe_telemetry()
        try:
            # Send initial state snapshot immediately
            init_snap = await app_engine.generate_telemetry_snapshot()
            await websocket.send_text(init_snap.model_dump_json())

            while True:
                # Wait for next snapshot from queue
                snap: TelemetrySnapshot = await q.get()
                await websocket.send_text(snap.model_dump_json())
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass
        finally:
            app_engine.unsubscribe_telemetry(q)

    return app


# Module-level default FastAPI app for uvicorn
app = create_app()
