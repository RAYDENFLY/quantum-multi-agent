"""UI tests for MainWindow shell, 7 workspace pages, navigation, and telemetry."""

from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication

from quantum.config.settings import Settings
from quantum.ui.app_window import MainWindow
from quantum.ui.theme import generate_qss


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    """Session-scoped QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(["quantum_test", "-platform", "offscreen"])
        app.setStyleSheet(generate_qss())
    return app


def test_main_window_initialization(qapp: QApplication, tmp_path: Path) -> None:
    """Verify MainWindow initializes all 7 workspace shells and primary controls."""
    settings = Settings(data_dir_path=str(tmp_path))
    win = MainWindow(settings=settings)

    assert "QUANTUM Multi-Agent Trading Desk" in win.windowTitle()
    assert win.top_bar is not None
    assert win.nav_rail is not None
    assert win.status_bar is not None
    assert win.stack.count() == 7

    # Verify initial active workspace is Overview (0)
    assert win.stack.currentIndex() == 0
    assert win.nav_rail.buttons[0].isChecked()

    win.close()


def test_workspace_navigation_all_seven_shells(qapp: QApplication, tmp_path: Path) -> None:
    """Verify clean switching across all seven workspaces and nav rail synchronization."""
    settings = Settings(data_dir_path=str(tmp_path))
    win = MainWindow(settings=settings)

    workspace_names = [
        "Overview",
        "Scanner",
        "Agents",
        "Market",
        "Positions",
        "Analytics",
        "Settings",
    ]

    for idx, name in enumerate(workspace_names):
        win.switch_workspace(idx)
        assert win.stack.currentIndex() == idx
        assert win.nav_rail.buttons[idx].isChecked()

    win.close()


def test_top_bar_pause_pipeline_toggle(qapp: QApplication, tmp_path: Path) -> None:
    """Verify top command bar pause/resume button state transitions."""
    settings = Settings(data_dir_path=str(tmp_path))
    win = MainWindow(settings=settings)

    assert win.top_bar.btn_pause.text() == "Pause Pipeline"

    # Toggle to paused
    win.top_bar.btn_pause.setChecked(True)
    assert win.top_bar.btn_pause.text() == "Resume Pipeline"

    # Toggle back to running
    win.top_bar.btn_pause.setChecked(False)
    assert win.top_bar.btn_pause.text() == "Pause Pipeline"

    win.close()


def test_settings_page_persistence(qapp: QApplication, tmp_path: Path) -> None:
    """Verify Settings page UI fields properly update and persist to config.json."""
    settings = Settings(data_dir_path=str(tmp_path))
    win = MainWindow(settings=settings)

    # Navigate to Settings (workspace index 6)
    win.switch_workspace(6)
    page = win.page_settings

    # Modify equity and refresh rate
    page.spin_equity.setValue(50_000.0)
    page.spin_refresh.setValue(6)
    page.cb_log_level.setCurrentText("DEBUG")

    # Click Save
    page.btn_save.click()

    assert "saved successfully" in page.lbl_status.text()
    assert settings.config_path.exists()

    # Verify reloaded settings match
    reloaded = Settings.load(custom_data_dir=tmp_path)
    assert reloaded.risk.starting_paper_equity_usdt == 50_000.0
    assert reloaded.app.ui_refresh_hz == 6
    assert reloaded.app.log_level == "DEBUG"

    # Test reset to defaults
    page.btn_reset.click()
    assert "Reset to conservative defaults" in page.lbl_status.text()
    assert page.spin_equity.value() == 10_000.0

    win.close()


def test_telemetry_bar_updates(qapp: QApplication, tmp_path: Path) -> None:
    """Verify bottom telemetry bar reflects SQLite status and process memory."""
    settings = Settings(data_dir_path=str(tmp_path))
    win = MainWindow(settings=settings)

    win.set_database_telemetry(18, True)
    assert "WAL Active (18 Tables)" in win.status_bar.lbl_db.text()

    win.set_database_telemetry(18, False)
    assert "Standard (18 Tables)" in win.status_bar.lbl_db.text()

    # Trigger manual memory telemetry update
    win.status_bar.refresh_telemetry()
    assert "RAM:" in win.status_bar.lbl_ram.text()

    win.close()
