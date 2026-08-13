"""
orders.py — Order placement logic for Binance Futures Testnet.

Provides two public functions:
  - place_market_order()
  - place_limit_order()

Both functions return a structured ``OrderResult`` dataclass and log all
relevant details (request, response, errors).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

logger = logging.getLogger("trading_bot")


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------


@dataclass
class OrderResult:
    """Structured representation of an order response from Binance."""

    success: bool
    order_id: Optional[str] = None
    symbol: Optional[str] = None
    side: Optional[str] = None
    order_type: Optional[str] = None
    quantity: Optional[str] = None
    price: Optional[str] = None
    executed_qty: Optional[str] = None
    avg_price: Optional[str] = None
    status: Optional[str] = None
    client_order_id: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_response(cls, response: dict[str, Any]) -> "OrderResult":
        """Build an OrderResult from a raw Binance API response dict."""
        return cls(
            success=True,
            order_id=str(response.get("orderId", "")),
            symbol=response.get("symbol"),
            side=response.get("side"),
            order_type=response.get("type"),
            quantity=response.get("origQty"),
            price=response.get("price"),
            executed_qty=response.get("executedQty"),
            avg_price=response.get("avgPrice"),
            status=response.get("status"),
            client_order_id=response.get("clientOrderId"),
            raw_response=response,
        )

    @classmethod
    def from_error(cls, message: str) -> "OrderResult":
        """Build a failed OrderResult carrying only an error message."""
        return cls(success=False, error_message=message)


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


def _log_order_request(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
) -> None:
    """Log the outgoing order parameters at DEBUG level."""
    price_str = f"@ {price}" if price else "@ MARKET"
    logger.debug(
        "Placing %s %s order | symbol=%s | qty=%s | price=%s",
        side,
        order_type,
        symbol,
        quantity,
        price_str,
    )


def _handle_api_exception(exc: BinanceAPIException, context: str) -> OrderResult:
    """Log a BinanceAPIException and return a failure OrderResult."""
    msg = f"Binance API error [{exc.status_code}]: {exc.message}"
    logger.error("%s — %s", context, msg)
    return OrderResult.from_error(msg)


def _handle_request_exception(exc: BinanceRequestException, context: str) -> OrderResult:
    """Log a BinanceRequestException (network error) and return a failure OrderResult."""
    msg = f"Network / request error: {exc}"
    logger.error("%s — %s", context, msg)
    return OrderResult.from_error(msg)


def _handle_unexpected_exception(exc: Exception, context: str) -> OrderResult:
    """Log an unexpected exception with full traceback and return a failure OrderResult."""
    logger.exception("%s — unexpected error: %s", context, exc)
    return OrderResult.from_error(f"Unexpected error: {exc}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def place_market_order(
    client: Client,
    symbol: str,
    side: str,
    quantity: float,
) -> OrderResult:
    """
    Place a MARKET futures order on Binance Testnet.

    Parameters
    ----------
    client:
        Authenticated Binance client.
    symbol:
        Trading pair (e.g. "BTCUSDT").
    side:
        "BUY" or "SELL".
    quantity:
        Number of contracts/coins to trade.

    Returns
    -------
    OrderResult
        Populated with order details on success, or error message on failure.
    """
    context = f"MARKET {side} {symbol}"
    _log_order_request(symbol, side, "MARKET", quantity)

    try:
        response: dict[str, Any] = client.futures_create_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=quantity,
        )
        result = OrderResult.from_response(response)
        logger.info(
            "MARKET order SUCCESS | id=%s | symbol=%s | side=%s | "
            "qty=%s | executedQty=%s | avgPrice=%s | status=%s",
            result.order_id,
            result.symbol,
            result.side,
            result.quantity,
            result.executed_qty,
            result.avg_price,
            result.status,
        )
        logger.debug("Raw API response: %s", response)
        return result

    except BinanceAPIException as exc:
        return _handle_api_exception(exc, context)
    except BinanceRequestException as exc:
        return _handle_request_exception(exc, context)
    except Exception as exc:
        return _handle_unexpected_exception(exc, context)


def place_limit_order(
    client: Client,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    time_in_force: str = "GTC",
) -> OrderResult:
    """
    Place a LIMIT futures order on Binance Testnet.

    Parameters
    ----------
    client:
        Authenticated Binance client.
    symbol:
        Trading pair (e.g. "BTCUSDT").
    side:
        "BUY" or "SELL".
    quantity:
        Number of contracts/coins to trade.
    price:
        Limit price for the order.
    time_in_force:
        "GTC" (Good Till Cancelled), "IOC", or "FOK". Defaults to "GTC".

    Returns
    -------
    OrderResult
        Populated with order details on success, or error message on failure.
    """
    context = f"LIMIT {side} {symbol} @ {price}"
    _log_order_request(symbol, side, "LIMIT", quantity, price)

    try:
        response: dict[str, Any] = client.futures_create_order(
            symbol=symbol,
            side=side,
            type="LIMIT",
            quantity=quantity,
            price=price,
            timeInForce=time_in_force,
        )
        result = OrderResult.from_response(response)
        logger.info(
            "LIMIT order SUCCESS | id=%s | symbol=%s | side=%s | "
            "qty=%s | limitPrice=%s | status=%s",
            result.order_id,
            result.symbol,
            result.side,
            result.quantity,
            result.price,
            result.status,
        )
        logger.debug("Raw API response: %s", response)
        return result

    except BinanceAPIException as exc:
        return _handle_api_exception(exc, context)
    except BinanceRequestException as exc:
        return _handle_request_exception(exc, context)
    except Exception as exc:
        return _handle_unexpected_exception(exc, context)
