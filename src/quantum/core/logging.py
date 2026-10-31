"""Structured rotating logging system for QUANTUM Trading Desk."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Maximum 5 rotating files of 10 MB each = 50 MB disk cap (AC-2.5)
MAX_LOG_BYTES = 10 * 1024 * 1024
BACKUP_COUNT = 5

LOG_FORMAT = "%(asctime)s.%(msecs)03d | %(levelname)-7s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_INITIALIZED = False


class PlainFormatter(logging.Formatter):
    """Standard formatter with millisecond precision."""

    def __init__(self) -> None:
        super().__init__(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)


def setup_logging(
    log_path: Optional[Path] = None,
    level: str = "INFO",
    enable_console: bool = True,
) -> logging.Logger:
    """Initialize root application logger with rotating file and console handlers."""
    global _INITIALIZED
    root_logger = logging.getLogger("quantum")
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # If already configured, update level and return
    if _INITIALIZED:
        root_logger.setLevel(numeric_level)
        return root_logger

    root_logger.handlers.clear()

    formatter = PlainFormatter()

    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=str(log_path),
            maxBytes=MAX_LOG_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    _INITIALIZED = True
    root_logger.info("QUANTUM logging initialized (Level: %s)", level)
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Obtain a logger instance namespaced under 'quantum'."""
    if not name.startswith("quantum"):
        return logging.getLogger(f"quantum.{name}")
    return logging.getLogger(name)
