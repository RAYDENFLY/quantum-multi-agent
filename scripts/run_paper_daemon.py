"""CLI Entrypoint for the QUANTUM Phase 6A Autonomous Paper-Trading Daemon.

Launches the FastAPI + WebSocket IPC Telemetry Server with Uvicorn.

Usage:
    python scripts/run_paper_daemon.py [--host 127.0.0.1] [--port 8000] [--initial-equity 10000.0]
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))

import uvicorn
from quantum.backtesting.resources import BACKTEST_MAX_THREADS, enforce_backtest_thread_limits
from quantum.daemon.server import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="QUANTUM Phase 6A Paper-Trading Daemon & IPC Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--initial-equity", type=float, default=10000.0, help="Initial paper cash in USD (default: 10000.0)")
    parser.add_argument("--db-path", type=str, default=None, help="Custom SQLite DB path (default: artifacts/phase_6/quantum_paper_trade.db)")
    args = parser.parse_args()

    # Enforce hardware budget
    enforce_backtest_thread_limits(BACKTEST_MAX_THREADS)

    print(f"[QUANTUM-DAEMON] Starting Autonomous Paper-Trading Daemon on http://{args.host}:{args.port}")
    print(f"[QUANTUM-DAEMON] Hardware threads: {BACKTEST_MAX_THREADS}")
    print(f"[QUANTUM-DAEMON] Initial Equity: ${args.initial_equity:,.2f} USD")
    print(f"[QUANTUM-DAEMON] Telemetry WebSocket: ws://{args.host}:{args.port}/ws/v1/telemetry")

    db_path = Path(args.db_path) if args.db_path else None
    app = create_app(db_path=db_path, initial_equity=args.initial_equity)

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
