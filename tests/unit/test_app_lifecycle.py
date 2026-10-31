"""Integration test for full application startup and graceful shutdown lifecycle."""

import asyncio
from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication

from quantum.config.settings import Settings
from quantum.main import run_desktop_app
from quantum.ui.theme import generate_qss


@pytest.mark.asyncio
async def test_full_application_startup_and_graceful_shutdown(tmp_path: Path) -> None:
    """Verify end-to-end async application launch, database setup, and clean teardown."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(["quantum_test", "-platform", "offscreen"])
        app.setStyleSheet(generate_qss())

    settings = Settings(data_dir_path=str(tmp_path))

    # Schedule clean close after 200ms
    async def schedule_close() -> None:
        await asyncio.sleep(0.2)
        top_windows = QApplication.topLevelWidgets()
        for win in top_windows:
            if hasattr(win, "close"):
                win.close()

    asyncio.create_task(schedule_close())

    exit_code = await run_desktop_app(app, settings)
    assert exit_code == 0
    assert settings.db_path.exists()
