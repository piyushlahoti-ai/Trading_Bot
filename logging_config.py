"""
logging_config.py — Centralized logging setup.

Sets up:
  • A rotating file handler that writes structured logs to logs/trading.log
  • A console handler (INFO level, coloured via colorama)
  • A single root logger "trading_bot" used throughout the project
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


# ---------------------------------------------------------------------------
# Coloured formatter (uses colorama if available, degrades gracefully)
# ---------------------------------------------------------------------------
try:
    from colorama import Fore, Style, init as colorama_init

    colorama_init(autoreset=True)

    _LEVEL_COLOURS: dict[int, str] = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
    }

    class _ColouredFormatter(logging.Formatter):
        """A logging.Formatter that prepends ANSI colour codes to the level name."""

        def format(self, record: logging.LogRecord) -> str:
            colour = _LEVEL_COLOURS.get(record.levelno, "")
            record.levelname = f"{colour}{record.levelname}{Style.RESET_ALL}"
            return super().format(record)

    _console_formatter_cls = _ColouredFormatter

except ImportError:  # colorama not installed
    _console_formatter_cls = logging.Formatter  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
LOGGER_NAME = "trading_bot"

_CONSOLE_FMT = "%(asctime)s [%(levelname)s] %(message)s"
_FILE_FMT = "%(asctime)s [%(levelname)-8s] %(name)s — %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"

# Max 5 MB per log file, keep last 3 backups
_MAX_BYTES = 5 * 1024 * 1024
_BACKUP_COUNT = 3


def setup_logging(log_file: Path, level: int = logging.DEBUG) -> logging.Logger:
    """
    Configure and return the application-wide logger.

    Parameters
    ----------
    log_file:
        Absolute path to the rotating log file.
    level:
        Minimum log level for the *file* handler (default: DEBUG).
        The *console* handler is always INFO.

    Returns
    -------
    logging.Logger
        The configured ``trading_bot`` logger.
    """
    logger = logging.getLogger(LOGGER_NAME)

    # Avoid adding duplicate handlers on repeated calls (e.g. during tests)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)  # capture everything; handlers filter

    # ------------------------------------------------------------------
    # File handler — DEBUG and above, rotating
    # ------------------------------------------------------------------
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(_FILE_FMT, datefmt=_DATE_FMT))
    logger.addHandler(file_handler)

    # ------------------------------------------------------------------
    # Console handler — INFO and above, coloured
    # ------------------------------------------------------------------
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        _console_formatter_cls(_CONSOLE_FMT, datefmt=_DATE_FMT)
    )
    logger.addHandler(console_handler)

    return logger


def get_logger() -> logging.Logger:
    """Return the pre-configured application logger (must call setup_logging first)."""
    return logging.getLogger(LOGGER_NAME)
