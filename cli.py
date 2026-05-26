#!/usr/bin/env python3
"""Stock Agent CLI — paper trading interface."""

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from backend.config import STARTING_CASH, STOCKS
from backend.data_feed import get_current_prices
from backend.trading_engine import run_cycle
from backend import portfolio as port

console = Console()


@click.group()
def cli():
    """Stock Agent — paper trading CLI."""
    port.init_db()


# ── status ────────────────────────────────────────────────────────────────────

@cli.command()
def status():
    """Show live portfolio status."""
    with console.status("Fetching prices…"):
        prices    = get_current_prices(list(STOCKS.keys()))
        positions = port.get_positions()
        cash      = port.get_cash()

    total_current  = sum(pos["shares"] * prices.get(sym, pos["avg_cost"]) for sym, pos in positions.items())
    total_invested = sum(pos["shares"] * pos["avg_cost"] for pos in positions.values())
    total_value    = cash + total_current
    total_pnl      = total_current - total_invested
    pnl_color      = "green" if total_pnl >= 0 else "red"

    console.print(Panel.fit(
        f"[bold]Total Value[/bold]   [green]${total_value:>12,.2f}[/green]\n"
        f"[bold]Cash[/bold]          [cyan]${cash:>12,.2f}[/cyan]\n"
        f"[bold]Invested[/bold]      [yellow]${total_current:>12,.2f}[/yellow]\n"
        f"[bold]Total P&L[/bold]     [{pnl_color}]${total_pnl:>+12,.2f}[/{pnl_color}]\n"
        f"[dim]Starting capital  ${STARTING_CASH:>12,.2f}[/dim]",
        title="[bold blue] Portfolio Summary [/bold blue]",
    ))

    # ── open positions ────────────────────────────────────────────────────────
    if positions:
        tbl = Table(title="Open Positions", box=box.ROUNDED, show_lines=True)
        for col, just in [("Symbol","left"),("Name","left"),("Shares","right"),
                          ("Avg Cost","right"),("Price","right"),
                          ("Value","right"),("P&L","right"),("P&L %","right")]:
            tbl.add_column(col, justify=just)

        for sym, pos in positions.items():
            price   = prices.get(sym, pos["avg_cost"])
            value   = pos["shares"] * price
            pnl     = value - pos["shares"] * pos["avg_cost"]
            pnl_pct = pnl / (pos["shares"] * pos["avg_cost"]) * 100
            c       = "green" if pnl >= 0 else "red"
            tbl.add_row(
                sym, STOCKS.get(sym, sym),
                f"{pos['shares']:.4f}", f"${pos['avg_cost']:.2f}",
                f"${price:.2f}", f"${value:,.2f}",
                f"[{c}]${pnl:+,.2f}[/{c}]",
                f"[{c}]{pnl_pct:+.2f}%[/{c}]",
            )
        console.print(tbl)
    else:
        console.print("[yellow]No open positions.[/yellow]\n")

    # ── price / signal grid ───────────────────────────────────────────────────
    tbl2 = Table(title="Tracked Stocks", box=box.SIMPLE_HEAVY)
    tbl2.add_column("Symbol", style="cyan bold")
    tbl2.add_column("Name")
    tbl2.add_column("Price", justify="right")
    tbl2.add_column("Ref Price", justify="right")
    tbl2.add_column("% from Ref", justify="right")
    tbl2.add_column("Signal", justify="center")
    tbl2.add_column("Targets")

    for sym, name in STOCKS.items():
        price     = prices.get(sym)
        ref       = port.get_ref_price(sym)
        pct       = ((price - ref) / ref * 100) if (price and ref) else None
        in_pos    = sym in positions
        price_str = f"${price:.2f}" if price else "[dim]—[/dim]"
        ref_str   = f"${ref:.2f}"   if ref   else "[dim]—[/dim]"

        pos = positions.get(sym)
        if in_pos and pos:
            tp  = pos["avg_cost"] * 1.10
            sl  = pos["avg_cost"] * 0.93
            target_str = f"[green]TP ${tp:.2f}[/green]  [red]SL ${sl:.2f}[/red]"
        elif ref:
            buy_at = ref * 0.95
            target_str = f"[yellow]Buy < ${buy_at:.2f}[/yellow]"
        else:
            target_str = "[dim]—[/dim]"

        if pct is None:
            pct_str = "[dim]—[/dim]"
            sig     = "[dim]—[/dim]"
        elif in_pos:
            pct_str = f"{pct:+.2f}%"
            sig     = "[cyan]HOLDING[/cyan]"
        elif pct <= -5:
            pct_str = f"[green]{pct:+.2f}%[/green]"
            sig     = "[green bold]BUY SIGNAL[/green bold]"
        else:
            pct_str = f"{pct:+.2f}%"
            sig     = "[dim]watching[/dim]"

        tbl2.add_row(sym, name, price_str, ref_str, pct_str, sig, target_str)

    console.print(tbl2)


# ── trades ────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--limit", default=20, show_default=True, help="Number of trades to show.")
def trades(limit: int):
    """Show trade history."""
    trade_list = port.get_trades(limit)

    if not trade_list:
        console.print("[yellow]No trades recorded yet.[/yellow]")
        return

    tbl = Table(title=f"Trade History (last {limit})", box=box.ROUNDED)
    tbl.add_column("Timestamp", style="dim")
    tbl.add_column("Action", justify="center")
    tbl.add_column("Symbol", style="cyan")
    tbl.add_column("Shares", justify="right")
    tbl.add_column("Price", justify="right")
    tbl.add_column("Total", justify="right")
    tbl.add_column("Reason")

    for t in trade_list:
        c = "green" if t["action"] == "BUY" else "red"
        tbl.add_row(
            t["timestamp"][:19],
            f"[{c}]{t['action']}[/{c}]",
            t["symbol"],
            f"{t['shares']:.4f}",
            f"${t['price']:.2f}",
            f"${t['total']:,.2f}",
            t["reason"] or "",
        )

    console.print(tbl)


# ── run-cycle ─────────────────────────────────────────────────────────────────

@cli.command("run-cycle")
def run_cycle_cmd():
    """Fetch prices and run one trading cycle."""
    with console.status("Running trading cycle…"):
        prices  = get_current_prices(list(STOCKS.keys()))
        actions = run_cycle(prices)

    if actions:
        console.print(f"[bold green]Cycle complete — {len(actions)} trade(s) executed:[/bold green]")
        for a in actions:
            c = "green" if a["action"] == "BUY" else "red"
            console.print(f"  [{c}]{a['action']}[/{c}] {a['symbol']}  "
                          f"{a['shares']:.4f} shares @ ${a['price']:.2f}")
    else:
        console.print("[bold]Cycle complete.[/bold] No trades triggered.")

    ctx = click.get_current_context()
    ctx.invoke(status)


# ── reset ─────────────────────────────────────────────────────────────────────

@cli.command()
def reset():
    """Reset paper portfolio to starting state."""
    import os
    from backend.config import DB_PATH

    if click.confirm("Reset portfolio to $100,000 starting cash? This cannot be undone."):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        port.init_db()
        console.print("[green]Portfolio reset.[/green]")


# ── auto (market-hours scheduler) ────────────────────────────────────────────

@cli.command()
def auto():
    """Run the agent automatically during NYSE market hours (9:30–4 PM ET, Mon–Fri)."""
    from backend.scheduler import _is_market_open, _seconds_until_open, _now_et
    from datetime import timedelta

    if _is_market_open():
        console.print("[green bold]Market is open — starting trading session now.[/green bold]")
    else:
        wait = _seconds_until_open()
        opens_at = _now_et() + timedelta(seconds=wait)
        console.print(
            f"[yellow]Market is currently closed.[/yellow]\n"
            f"Next open: [cyan]{opens_at.strftime('%A %Y-%m-%d %H:%M ET')}[/cyan] "
            f"([dim]{wait/3600:.1f} h[/dim])"
        )

    console.print("[dim]Press Ctrl+C to stop.[/dim]")
    from backend.scheduler import run_scheduler
    run_scheduler()


if __name__ == "__main__":
    cli()
