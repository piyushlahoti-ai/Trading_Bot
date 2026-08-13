"""
validators.py — Input validation helpers.

All validation logic lives here so that CLI and interactive menu share
identical rules.  Every validator raises ``typer.BadParameter`` (which
Typer renders as a friendly error) or ``ValueError`` when used outside
the CLI context.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

import typer

# ---------------------------------------------------------------------------
# Allowed values
# ---------------------------------------------------------------------------
VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}


# ---------------------------------------------------------------------------
# Individual validators
# ---------------------------------------------------------------------------


def validate_symbol(symbol: str) -> str:
    """
    Ensure the trading pair symbol is a non-empty uppercase string.

    Parameters
    ----------
    symbol:
        Raw symbol string from the user (e.g. "btcusdt").

    Returns
    -------
    str
        Normalised upper-case symbol (e.g. "BTCUSDT").

    Raises
    ------
    typer.BadParameter
        If the symbol is blank.
    """
    normalised = symbol.strip().upper()
    if not normalised:
        raise typer.BadParameter("Symbol must not be empty (e.g. BTCUSDT).")
    return normalised


def validate_side(side: str) -> str:
    """
    Ensure the order side is either BUY or SELL (case-insensitive).

    Parameters
    ----------
    side:
        Raw side string from the user.

    Returns
    -------
    str
        Normalised upper-case side ("BUY" or "SELL").

    Raises
    ------
    typer.BadParameter
        If the side is not recognised.
    """
    normalised = side.strip().upper()
    if normalised not in VALID_SIDES:
        raise typer.BadParameter(
            f"Side must be one of {sorted(VALID_SIDES)} — got '{side}'."
        )
    return normalised


def validate_quantity(quantity: float) -> float:
    """
    Ensure the order quantity is a finite positive number.

    Parameters
    ----------
    quantity:
        Raw quantity value from the user.

    Returns
    -------
    float
        Validated quantity.

    Raises
    ------
    typer.BadParameter
        If quantity is zero, negative, or not a valid number.
    """
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise typer.BadParameter(f"Quantity '{quantity}' is not a valid number.")

    if qty <= 0:
        raise typer.BadParameter(
            f"Quantity must be greater than 0 — got {quantity}."
        )
    return float(qty)


def validate_price(price: Optional[float], order_type: str) -> Optional[float]:
    """
    Validate the price parameter according to the order type.

    Rules
    -----
    - MARKET orders: price must be None (not supplied).
    - LIMIT  orders: price must be a finite positive number.

    Parameters
    ----------
    price:
        Raw price value from the user (may be None for market orders).
    order_type:
        Normalised order type string ("MARKET" or "LIMIT").

    Returns
    -------
    Optional[float]
        Validated price, or None for market orders.

    Raises
    ------
    typer.BadParameter
        If the price rule is violated.
    """
    order_type = order_type.upper()

    if order_type == "MARKET":
        if price is not None:
            raise typer.BadParameter(
                "Price must NOT be specified for MARKET orders."
            )
        return None

    # LIMIT order — price is mandatory and must be positive
    if price is None:
        raise typer.BadParameter(
            "Price is required for LIMIT orders (use --price <value>)."
        )

    try:
        p = Decimal(str(price))
    except InvalidOperation:
        raise typer.BadParameter(f"Price '{price}' is not a valid number.")

    if p <= 0:
        raise typer.BadParameter(
            f"Price must be greater than 0 — got {price}."
        )
    return float(p)


def validate_order_type(order_type: str) -> str:
    """
    Ensure the order type is either MARKET or LIMIT (case-insensitive).

    Parameters
    ----------
    order_type:
        Raw order type string.

    Returns
    -------
    str
        Normalised upper-case order type.

    Raises
    ------
    typer.BadParameter
        If the order type is not recognised.
    """
    normalised = order_type.strip().upper()
    if normalised not in VALID_ORDER_TYPES:
        raise typer.BadParameter(
            f"Order type must be one of {sorted(VALID_ORDER_TYPES)} — got '{order_type}'."
        )
    return normalised
