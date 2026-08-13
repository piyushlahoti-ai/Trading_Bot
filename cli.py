"""
cli.py — Typer-based CLI commands and the interactive Rich menu.

Commands
--------
  market   Place a MARKET buy/sell order.
  limit    Place a LIMIT  buy/sell order.
  menu     Launch the interactive numbered menu (bonus feature).

All output is rendered via Rich for beautiful, consistent formatting.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from bot.client import get_client, validate_credentials
from bot.orders import OrderResult, place_limit_order, place_market_order
from bot.validators import validate_price, validate_quantity, validate_side, validate_symbol

# ---------------------------------------------------------------------------
# Typer app + Rich console
# ---------------------------------------------------------------------------
app = typer.Typer(
    name="trading-bot",
    help="Binance Futures Testnet Trading Bot — place MARKET and LIMIT orders.",
    add_completion=False,
    no_args_is_help=False,  # we handle the default in main.py
)

console = Console()
logger = logging.getLogger("trading_bot")


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------


def _banner() -> None:
    """Print the application banner."""
    console.print(
        Panel.fit(
            "[bold cyan]Binance Futures Testnet[/bold cyan]\n"
            "[bold white]          Trading Bot[/bold white]",
            border_style="bright_cyan",
            padding=(1, 4),
        )
    )


def _print_order_result(result: OrderResult) -> None:
    """Render a coloured order summary table from an OrderResult."""

    if result.success:
        status_text = Text("SUCCESS", style="bold green")
        header_style = "bold green"
    else:
        status_text = Text("FAILED", style="bold red")
        header_style = "bold red"

    table = Table(
        title="[bold white]Order Summary[/bold white]",
        box=box.ROUNDED,
        show_header=False,
        border_style=header_style,
        padding=(0, 2),
        min_width=46,
    )
    table.add_column("Field", style="dim white", no_wrap=True)
    table.add_column("Value", style="bright_white")

    if result.success:
        table.add_row("Symbol", result.symbol or "—")
        table.add_row("Side", result.side or "—")
        table.add_row("Type", result.order_type or "—")
        table.add_row("Quantity", result.quantity or "—")
        if result.price and result.price != "0":
            table.add_row("Limit Price", result.price)
        table.add_row("─" * 18, "─" * 22)
        table.add_row("Status", result.status or "—")
        table.add_row("Order ID", result.order_id or "—")
        table.add_row("Client Order ID", result.client_order_id or "—")
        table.add_row("Executed Qty", result.executed_qty or "—")
        table.add_row("Average Price", result.avg_price or "—")
    else:
        table.add_row("Error", f"[red]{result.error_message}[/red]")

    console.print()
    console.print(table)
    console.print()
    console.print(
        Panel(status_text, border_style=header_style, expand=False)
    )
    console.print()


def _abort(message: str) -> None:
    """Print a red error panel and exit with code 1."""
    console.print(
        Panel(
            f"[bold red]Error:[/bold red] {message}",
            border_style="red",
            title="[red]Aborted[/red]",
        )
    )
    logger.error("Aborted: %s", message)
    raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------


@app.command("market")
def market_order(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading pair, e.g. BTCUSDT"),
    side: str = typer.Option(..., "--side", help="BUY or SELL"),
    quantity: float = typer.Option(..., "--quantity", "-q", help="Number of contracts"),
) -> None:
    """
    Place a MARKET futures order on the Binance Testnet.

    Example:

        python main.py market --symbol BTCUSDT --side BUY --quantity 0.01
    """
    _banner()

    # --- Validate inputs ---
    try:
        symbol = validate_symbol(symbol)
        side = validate_side(side)
        quantity = validate_quantity(quantity)
        validate_price(None, "MARKET")  # ensures no price required
    except typer.BadParameter as exc:
        _abort(str(exc))

    # --- Build client & validate credentials ---
    try:
        client = get_client()
        validate_credentials(client)
    except EnvironmentError as exc:
        _abort(str(exc))
    except (BinanceError := Exception):  # noqa: F841 — catch-all for connection issues
        _abort(f"Could not connect to Binance Testnet: {BinanceError}")

    # --- Place order ---
    console.print(
        f"[dim]Placing MARKET {side} order for [bold]{quantity}[/bold] "
        f"[bold cyan]{symbol}[/bold cyan]…[/dim]"
    )
    logger.info("CLI → MARKET %s %s qty=%s", side, symbol, quantity)

    result = place_market_order(client, symbol, side, quantity)
    _print_order_result(result)

    if not result.success:
        raise typer.Exit(code=1)


@app.command("limit")
def limit_order(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading pair, e.g. BTCUSDT"),
    side: str = typer.Option(..., "--side", help="BUY or SELL"),
    quantity: float = typer.Option(..., "--quantity", "-q", help="Number of contracts"),
    price: float = typer.Option(..., "--price", "-p", help="Limit price"),
) -> None:
    """
    Place a LIMIT futures order on the Binance Testnet.

    Example:

        python main.py limit --symbol BTCUSDT --side SELL --quantity 0.01 --price 120000
    """
    _banner()

    # --- Validate inputs ---
    try:
        symbol = validate_symbol(symbol)
        side = validate_side(side)
        quantity = validate_quantity(quantity)
        validated_price = validate_price(price, "LIMIT")
    except typer.BadParameter as exc:
        _abort(str(exc))
        return  # unreachable; satisfies type-checkers

    # --- Build client & validate credentials ---
    try:
        client = get_client()
        validate_credentials(client)
    except EnvironmentError as exc:
        _abort(str(exc))
    except Exception as exc:
        _abort(f"Could not connect to Binance Testnet: {exc}")

    # --- Place order ---
    console.print(
        f"[dim]Placing LIMIT {side} order for [bold]{quantity}[/bold] "
        f"[bold cyan]{symbol}[/bold cyan] @ [bold yellow]{validated_price}[/bold yellow]…[/dim]"
    )
    logger.info("CLI → LIMIT %s %s qty=%s price=%s", side, symbol, quantity, validated_price)

    result = place_limit_order(client, symbol, side, quantity, validated_price)  # type: ignore[arg-type]
    _print_order_result(result)

    if not result.success:
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# Interactive menu (bonus feature)
# ---------------------------------------------------------------------------

_MENU_OPTIONS: dict[str, str] = {
    "1": "Market Buy",
    "2": "Market Sell",
    "3": "Limit Buy",
    "4": "Limit Sell",
    "5": "Exit",
}


def _render_menu() -> None:
    """Render the interactive menu table."""
    table = Table(
        title="[bold cyan]Interactive Menu[/bold cyan]",
        box=box.SIMPLE_HEAVY,
        border_style="cyan",
        min_width=32,
    )
    table.add_column("Key", style="bold yellow", justify="center")
    table.add_column("Action", style="bright_white")

    for key, label in _MENU_OPTIONS.items():
        table.add_row(key, label)

    console.print(table)


def _prompt_order_params(order_type: str, side: str) -> tuple[str, float, Optional[float]]:
    """Interactively prompt for symbol, quantity (and price for LIMIT)."""
    console.print()
    symbol_raw = Prompt.ask("[cyan]  Symbol[/cyan]  (e.g. BTCUSDT)", default="BTCUSDT")
    qty_raw = Prompt.ask("[cyan]  Quantity[/cyan]", default="0.01")

    price_val: Optional[float] = None
    if order_type == "LIMIT":
        price_raw = Prompt.ask("[cyan]  Limit Price[/cyan]")
        try:
            price_val = float(price_raw)
        except ValueError:
            _abort(f"Invalid price: '{price_raw}'")

    try:
        symbol = validate_symbol(symbol_raw)
        quantity = validate_quantity(float(qty_raw))
        if price_val is not None:
            price_val = validate_price(price_val, "LIMIT")  # type: ignore[assignment]
    except typer.BadParameter as exc:
        _abort(str(exc))

    return symbol, quantity, price_val


def _execute_menu_choice(choice: str, client: object) -> None:
    """Route the menu selection to the appropriate order function."""
    from binance.client import Client as _Client  # local import to avoid circularity

    assert isinstance(client, _Client)

    mapping: dict[str, tuple[str, str]] = {
        "1": ("MARKET", "BUY"),
        "2": ("MARKET", "SELL"),
        "3": ("LIMIT", "BUY"),
        "4": ("LIMIT", "SELL"),
    }
    order_type, side = mapping[choice]

    symbol, quantity, price = _prompt_order_params(order_type, side)

    console.print()
    console.rule("[dim]Executing order…[/dim]")

    if order_type == "MARKET":
        result = place_market_order(client, symbol, side, quantity)
    else:
        result = place_limit_order(client, symbol, side, quantity, price)  # type: ignore[arg-type]

    _print_order_result(result)


@app.command("menu")
def interactive_menu() -> None:
    """
    Launch the interactive numbered trading menu.

    Select an order type, enter parameters, and execute — all without
    memorising CLI flags.
    """
    _banner()

    # Build client once for the session
    try:
        client = get_client()
        validate_credentials(client)
    except EnvironmentError as exc:
        _abort(str(exc))
        return
    except Exception as exc:
        _abort(f"Connection failed: {exc}")
        return

    console.print(
        "[green]Connected to Binance Futures Testnet[/green]\n"
    )

    while True:
        _render_menu()
        choice = Prompt.ask(
            "[bold yellow]Select an option[/bold yellow]",
            choices=list(_MENU_OPTIONS.keys()),
            show_choices=False,
        )

        if choice == "5":
            console.print(
                Panel("[bold cyan]Goodbye! Happy trading 👋[/bold cyan]", border_style="cyan")
            )
            raise typer.Exit(code=0)

        try:
            _execute_menu_choice(choice, client)
        except typer.Exit:
            pass  # allow the loop to continue after an order failure
        except Exception as exc:
            logger.exception("Unexpected error in menu: %s", exc)
            console.print(f"[red]Unexpected error:[/red] {exc}")

        console.print()
