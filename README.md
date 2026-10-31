# QUANTUM: Multi-Agent Trading Desk

Desktop-native, local-first cryptocurrency perpetual futures quantitative research and paper trading system for Bybit and AsterDEX.

## Architecture & Specifications

Authoritative engineering specifications are located in the `docs/` directory:

* `docs/ARCHITECTURE.md`: Master system architecture and technical blueprints.
* `docs/SYSTEM_DESIGN.md`: Concurrency, IPC, and hardware resource boundaries.
* `docs/DATABASE_SCHEMA.md`: Complete SQLite WAL persistence schema (18 tables).
* `docs/UI_SPECIFICATION.md`: PySide6 desktop interface and 7 workspace layouts.
* `docs/UI_DESIGN_SYSTEM.md`: Dark terminal design tokens, typography, and contrast rules.
* `docs/IMPLEMENTATION_ROADMAP.md`: Sequential eight-phase engineering plan.

## Phase 1: Desktop Foundation

Phase 1 establishes the native PySide6 desktop foundation:
* `qasync` asyncio and Qt event loop integration.
* SQLite WAL database initialization with automated schema migrations.
* Application configuration management with JSON and SQLite persistence.
* Rotating structured logging system.
* High-density obsidian dark terminal design system.
* Seven responsive workspace shells with informative empty states.
* Global keyboard shortcuts (`Alt+1` through `Alt+7`, `Ctrl+F`, `Escape`, `Ctrl+Shift+P`).
* Real-time system telemetry and memory monitoring.

## Getting Started

### Prerequisites
* Python 3.11+ (Windows x64 recommended)
* 4-core CPU, 12 GB RAM

### Installation
```bash
pip install -r requirements.txt
```

### Launch Desktop Application
```bash
python -m quantum.main
```

### Run Tests
```bash
pytest tests/ -v
```
