"""QUANTUM Phase 6B — Master One-Click Desktop & Daemon Orchestrator.

Starts the Python FastAPI + WebSocket paper-trading daemon in the background
(if not already running) and launches the C# Avalonia Desktop UI application.

Usage:
    python run_quantum_desktop.py [--host 127.0.0.1] [--port 8000] [--no-daemon]
"""

import argparse
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
PROJECT_FILE = ROOT_DIR / "desktop" / "QuantumDesktop" / "QuantumDesktop.csproj"
DAEMON_SCRIPT = ROOT_DIR / "scripts" / "run_paper_daemon.py"


def is_daemon_healthy(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if the daemon is responding on /api/v1/health."""
    url = f"http://{host}:{port}/api/v1/health"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantumLauncher/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def wait_for_daemon(host: str, port: int, max_wait_seconds: float = 10.0) -> bool:
    """Poll /api/v1/health until healthy or timeout."""
    start = time.time()
    while time.time() - start < max_wait_seconds:
        if is_daemon_healthy(host, port):
            return True
        time.sleep(0.5)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="QUANTUM Desktop & Daemon Launcher")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Daemon host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Daemon port (default: 8000)")
    parser.add_argument("--no-daemon", action="store_true", help="Skip starting daemon (use external running daemon)")
    parser.add_argument("--build", action="store_true", help="Force dotnet build before launch")
    args = parser.parse_args()

    print("=" * 80)
    print("  QUANTUM AUTONOMOUS TRADING & GOVERNANCE DESKTOP (PHASE 6B)")
    print("=" * 80)

    daemon_proc = None

    # 1. Start Daemon if requested and not running
    if not args.no_daemon:
        if is_daemon_healthy(args.host, args.port):
            print(f"[LAUNCHER] Daemon is already active at http://{args.host}:{args.port}")
        else:
            print(f"[LAUNCHER] Starting Python Paper-Trading Daemon on http://{args.host}:{args.port}...")
            daemon_cmd = [sys.executable, str(DAEMON_SCRIPT), "--host", args.host, "--port", str(args.port)]
            daemon_proc = subprocess.Popen(
                daemon_cmd,
                cwd=str(ROOT_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print("[LAUNCHER] Waiting for daemon IPC interface to initialize...")
            if wait_for_daemon(args.host, args.port, max_wait_seconds=12.0):
                print(f"[LAUNCHER] Daemon healthy and listening at http://{args.host}:{args.port}")
            else:
                print("[LAUNCHER] WARNING: Daemon did not respond in 12s, proceeding with UI launch...")

    # 2. Build desktop project if requested
    if args.build:
        print("[LAUNCHER] Compiling C# Avalonia Desktop project...")
        build_res = subprocess.run(["dotnet", "build", str(PROJECT_FILE), "-c", "Release"])
        if build_res.returncode != 0:
            print("[LAUNCHER] ERROR: Desktop build failed.")
            if daemon_proc:
                daemon_proc.terminate()
            sys.exit(build_res.returncode)

    # 3. Launch Avalonia Desktop
    print("[LAUNCHER] Launching C# Avalonia Control Center window...")
    desktop_cmd = ["dotnet", "run", "--project", str(PROJECT_FILE), "-c", "Release", "--no-build"]

    try:
        ui_res = subprocess.run(desktop_cmd, cwd=str(ROOT_DIR))
        print(f"[LAUNCHER] Desktop window closed (exit code: {ui_res.returncode})")
    except KeyboardInterrupt:
        print("\n[LAUNCHER] Interrupted by operator.")
    finally:
        if daemon_proc and daemon_proc.poll() is None:
            print("[LAUNCHER] Stopping background paper-trading daemon...")
            daemon_proc.terminate()
            try:
                daemon_proc.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                daemon_proc.kill()
            print("[LAUNCHER] Daemon stopped cleanly.")

    print("[LAUNCHER] QUANTUM Desktop session completed.")


if __name__ == "__main__":
    main()
