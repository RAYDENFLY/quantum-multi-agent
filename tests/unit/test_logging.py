"""Unit tests for the rotating logging subsystem."""

import logging
from pathlib import Path
from quantum.core.logging import get_logger, setup_logging


def test_logging_initialization(tmp_path: Path) -> None:
    """Verify log file creation, format, and level configuration."""
    log_file = tmp_path / "logs" / "test_quantum.log"
    logger = setup_logging(log_path=log_file, level="DEBUG", enable_console=False)

    assert logger.level == logging.DEBUG
    assert log_file.exists()

    test_msg = "Diagnostic test log entry for Phase 1 verification"
    logger.debug(test_msg)

    # Flush handlers
    for handler in logger.handlers:
        handler.flush()

    content = log_file.read_text(encoding="utf-8")
    assert test_msg in content
    assert "DEBUG" in content
    assert "quantum" in content


def test_get_logger_namespacing() -> None:
    """Verify get_logger properly prefixes namespace."""
    sub_logger = get_logger("test_module")
    assert sub_logger.name == "quantum.test_module"

    root_sub = get_logger("quantum.sub")
    assert root_sub.name == "quantum.sub"
