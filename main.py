#!/usr/bin/env python3
"""
main.py — Entry point for the Binance Futures Testnet Trading Bot.

Usage
-----
CLI mode:
    python main.py market --symbol BTCUSDT --side BUY --quantity 0.01
    python main.py limit  --symbol BTCUSDT --side SELL --quantity 0.01 --price 120000

Interactive menu:
    python main.py menu

No arguments (defaults to interactive menu):
    python main.py
"""

from __future__ import annotations

import sys

import typer
from rich.console import Console

# ---------------------------------------------------------------------------
# Bootstrap logging BEFORE importing any bot module that uses the logger.
# The config module is imported inside the try block so that a missing .env
# produces a friendly message rather than an unhandled exception at import.
# ---------------------------------------------------------------------------
console = Console()


def _bootstrap_logging() -> None:
    """Initialise logging early; suppress the error if .env is missing."""
    from pathlib import Path

    try:
        from bot.config import settings
        from bot.logging_config import setup_logging

        setup_logging(settings.log_file)
    except EnvironmentError as exc:
        # Logging cannot start without the log path from settings.
        # Fall back to a temporary path so the rest of the app can still log.
        from bot.logging_config import setup_logging

        setup_logging(Path("logs") / "trading.log")

        import logging

        logging.getLogger("trading_bot").warning(
            "Environment not fully configured: %s", exc
        )


def main() -> None:
    """Bootstrap and dispatch to the Typer CLI."""
    _bootstrap_logging()

    from bot.cli import app

    # If no subcommand was given, default to the interactive menu
    if len(sys.argv) == 1:
        sys.argv.append("menu")

    app()


if __name__ == "__main__":
    main()
