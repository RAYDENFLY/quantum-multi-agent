"""Unit tests for configuration loading, validation, and persistence."""

import json
from pathlib import Path
import pytest
from quantum.config.settings import Settings


def test_default_settings(tmp_path: Path) -> None:
    """Verify default settings initialization and directory properties."""
    settings = Settings(data_dir_path=str(tmp_path))
    assert settings.app.app_name == "QUANTUM Multi-Agent Trading Desk"
    assert settings.app.version == "0.1.0"
    assert settings.app.log_level == "INFO"
    assert settings.app.ui_refresh_hz == 4
    assert settings.risk.starting_paper_equity_usdt == 10_000.0
    assert settings.risk.max_concurrent_positions == 3
    assert settings.risk.min_net_reward_risk == 1.80
    assert settings.exchange.bybit_enabled is True
    assert settings.exchange.aster_enabled is True
    assert settings.db_path == tmp_path / "quantum_desk.db"
    assert settings.config_path == tmp_path / "config.json"
    assert settings.log_path == tmp_path / "logs" / "quantum.log"


def test_settings_save_and_load(tmp_path: Path) -> None:
    """Verify persistence to config.json and reload fidelity."""
    settings = Settings(data_dir_path=str(tmp_path))
    settings.app.log_level = "DEBUG"
    settings.risk.max_concurrent_positions = 5
    settings.risk.starting_paper_equity_usdt = 25_000.0
    settings.save()

    assert settings.config_path.exists()

    with open(settings.config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["app"]["log_level"] == "DEBUG"
    assert data["risk"]["max_concurrent_positions"] == 5
    assert data["risk"]["starting_paper_equity_usdt"] == 25_000.0

    # Reload from directory
    reloaded = Settings.load(custom_data_dir=tmp_path)
    assert reloaded.app.log_level == "DEBUG"
    assert reloaded.risk.max_concurrent_positions == 5
    assert reloaded.risk.starting_paper_equity_usdt == 25_000.0


def test_settings_validation_constraints(tmp_path: Path) -> None:
    """Verify pydantic validation constraints on bounds."""
    settings = Settings(data_dir_path=str(tmp_path))

    with pytest.raises(Exception):
        # UI refresh Hz must be between 1 and 10
        settings.app.ui_refresh_hz = 50

    with pytest.raises(Exception):
        # Max concurrent positions must be between 1 and 8
        settings.risk.max_concurrent_positions = 20
