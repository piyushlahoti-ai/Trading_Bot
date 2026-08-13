"""
config.py — Environment & application settings loader.

Reads all required configuration from environment variables (via .env)
and exposes them as a typed Settings dataclass.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env from project root (works regardless of cwd)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    """Immutable application-wide settings derived from environment variables."""

    api_key: str
    api_secret: str

    # Binance Futures Testnet base URLs
    futures_base_url: str = "https://demo-fapi.binance.com"
    wss_base_url: str = "wss://demo-fstream.binance.com"

    # Log file location
    log_file: Path = field(
        default_factory=lambda: _PROJECT_ROOT / "logs" / "trading.log"
    )

    # Request timeouts (seconds)
    request_timeout: int = 15

    @classmethod
    def from_env(cls) -> "Settings":
        """
        Factory that reads credentials from environment variables and returns
        a validated Settings instance.

        Raises:
            EnvironmentError: If any required variable is missing or empty.
        """
        api_key = os.getenv("BINANCE_API_KEY", "").strip()
        api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

        missing: list[str] = []
        if not api_key:
            missing.append("BINANCE_API_KEY")
        if not api_secret:
            missing.append("BINANCE_API_SECRET")

        if missing:
            raise EnvironmentError(
                f"Missing required environment variable(s): {', '.join(missing)}\n"
                "Please copy .env.example to .env and fill in your Testnet API keys."
            )

        return cls(api_key=api_key, api_secret=api_secret)


# ---------------------------------------------------------------------------
# Lazy module-level singleton — resolves on first attribute access.
# This ensures that importing config.py does NOT crash when .env is absent
# (e.g. when running `python main.py --help`).
# ---------------------------------------------------------------------------


class _LazySettings:
    """Proxy that defers Settings.from_env() until the first attribute access."""

    _instance: Settings | None = None

    def _get(self) -> Settings:
        if self._instance is None:
            self._instance = Settings.from_env()
        return self._instance

    def __getattr__(self, name: str):  # noqa: ANN001
        return getattr(self._get(), name)


settings: Settings = _LazySettings()  # type: ignore[assignment]
