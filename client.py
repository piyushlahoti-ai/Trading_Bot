"""
client.py — Binance Futures Testnet API client factory.

Provides a single ``get_client()`` function that returns a fully
configured ``binance.Client`` instance pointing at the Testnet endpoints.
Also exposes ``validate_credentials()`` to verify the keys are valid
before placing orders.
"""

from __future__ import annotations

import logging
from typing import Any

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

from bot.config import settings

logger = logging.getLogger("trading_bot")


def get_client() -> Client:
    """
    Build and return a Binance ``Client`` configured for the USDT-M Futures Testnet.

    The client uses ``testnet=True`` so that python-binance automatically
    routes requests to the Testnet endpoints.

    Returns
    -------
    Client
        Authenticated Binance client targeting the Futures Testnet.
    """
    futures_url = settings.futures_base_url  # resolved at call time

    client = Client(
        api_key=settings.api_key,
        api_secret=settings.api_secret,
        testnet=True,
        requests_params={"timeout": settings.request_timeout},
    )

    # Override the futures base URL to the official Testnet address
    client.FUTURES_URL = f"{futures_url}/fapi"

    logger.debug(
        "Binance Futures Testnet client created — base URL: %s",
        futures_url,
    )
    return client


def redact_sensitive_info(data: Any) -> Any:
    """
    Recursively redact sensitive fields from dictionary-like structures.
    """
    if isinstance(data, dict):
        return {
            k: "[REDACTED]" if any(s in k.lower() for s in ("key", "secret", "signature", "token", "password", "auth", "credential"))
            else redact_sensitive_info(v)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [redact_sensitive_info(item) for item in data]
    return data


def validate_credentials(client: Client) -> None:
    """
    Verify that the API keys work by calling the Futures account endpoint.

    Parameters
    ----------
    client:
        An authenticated Binance client.

    Raises
    ------
    BinanceAPIException
        If the credentials are invalid or the account is not enabled for Futures.
    ConnectionError
        If the Testnet is unreachable.
    """
    logger.debug("Validating API credentials against Binance Futures Testnet…")
    try:
        account = client.futures_account()
        
        # Log the raw API response only after redacting sensitive information.
        redacted = redact_sensitive_info(account)
        logger.debug("Raw Binance Futures account response: %s", redacted)

        total_balance = "N/A"
        if isinstance(account, dict):
            assets = account.get("assets")
            if isinstance(assets, list):
                for a in assets:
                    if isinstance(a, dict) and a.get("asset") == "USDT":
                        total_balance = a.get("walletBalance") or a.get("balance") or "N/A"
                        break

        logger.info(
            "Credentials valid  |  USDT Futures balance: %s", total_balance
        )
    except BinanceAPIException as exc:
        logger.error(
            "Credential validation failed — Binance error %s: %s",
            exc.status_code,
            exc.message,
        )
        raise
    except BinanceRequestException as exc:
        logger.error("Network error during credential validation: %s", exc)
        raise ConnectionError(f"Could not reach Binance Testnet: {exc}") from exc
    except Exception as exc:
        logger.exception("Unexpected error during credential validation")
        raise RuntimeError(f"Unexpected error: {exc}") from exc
