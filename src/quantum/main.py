"""Application entrypoint for QUANTUM Multi-Agent Trading Desk."""

import asyncio
import signal
import sys
import time
from typing import Optional
from PySide6.QtWidgets import QApplication
import qasync

from quantum.config.settings import Settings, get_settings
from quantum.core.logging import get_logger, setup_logging
from quantum.storage.database import DatabaseManager
from quantum.ui.app_window import MainWindow
from quantum.ui.theme import generate_qss

logger = get_logger("main")


async def run_desktop_app(app: QApplication, settings: Settings) -> int:
    """Async desktop application lifecycle manager."""
    start_time = time.perf_counter()

    # 1. Initialize SQLite Database & Schema Migrations
    db = DatabaseManager(settings.db_path)
    db_init_start = time.perf_counter()
    await db.initialize()
    db_init_duration_ms = (time.perf_counter() - db_init_start) * 1000.0

    journal_mode = await db.get_journal_mode()
    tables = await db.get_table_names()
    logger.info(
        "SQLite initialized in %.2f ms (Journal Mode: %s, Tables: %d)",
        db_init_duration_ms,
        journal_mode,
        len(tables),
    )

    # 2. Instantiate and Configure MainWindow
    main_window = MainWindow(settings=settings)
    main_window.set_database_telemetry(len(tables), journal_mode == "WAL")
    main_window.show()

    total_startup_ms = (time.perf_counter() - start_time) * 1000.0
    logger.info("QUANTUM Desktop launched in %.2f ms", total_startup_ms)

    # 3. Create shutdown Future triggered by window close
    close_future = asyncio.get_running_loop().create_future()

    def on_window_closed() -> None:
        if not close_future.done():
            close_future.set_result(0)

    main_window.window_closed.connect(on_window_closed)

    # Handle OS termination signals
    def signal_handler() -> None:
        logger.info("Shutdown signal received")
        if not close_future.done():
            close_future.set_result(0)

    try:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, signal_handler)
            except (NotImplementedError, RuntimeError):
                # Signal handlers not fully supported on some Windows asyncio loops
                pass
    except Exception:
        pass

    try:
        exit_code = await close_future
    except asyncio.CancelledError:
        exit_code = 0
    finally:
        logger.info("Initiating graceful application teardown")
        await db.close()
        logger.info("QUANTUM shutdown complete")

    return exit_code


def main() -> int:
    """Synchronous launcher entrypoint."""
    settings = get_settings()
    setup_logging(
        log_path=settings.log_path,
        level=settings.app.log_level,
        enable_console=True,
    )
    logger.info("Starting %s v%s", settings.app.app_name, settings.app.version)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("QUANTUM")
    app.setOrganizationName("QUANTUM Desk")
    app.setStyleSheet(generate_qss())

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    with loop:
        try:
            return loop.run_until_complete(run_desktop_app(app, settings))
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received during startup")
            return 0
        except Exception as e:
            logger.critical("Fatal error during application execution: %s", e, exc_info=True)
            return 1


if __name__ == "__main__":
    sys.exit(main())
