"""
Market-hours scheduler.

Starts at 9:30 AM ET, runs a trade cycle every POLL_INTERVAL seconds
until 4:00 PM ET, then sleeps until the next trading day.
Skips weekends automatically.
"""

import logging
import signal
import sys
import time
from datetime import datetime, time as dtime, timezone, timedelta

import zoneinfo

from .config import POLL_INTERVAL, STOCKS
from .data_feed import get_current_prices
from .trading_engine import run_cycle
from . import portfolio as port

logger = logging.getLogger(__name__)

ET = zoneinfo.ZoneInfo("America/New_York")
MARKET_OPEN  = dtime(9, 30)
MARKET_CLOSE = dtime(16, 0)


def _now_et() -> datetime:
    return datetime.now(tz=ET)


def _is_market_open() -> bool:
    now = _now_et()
    if now.weekday() >= 5:          # Saturday=5, Sunday=6
        return False
    return MARKET_OPEN <= now.time() < MARKET_CLOSE


def _seconds_until_open() -> float:
    """Return seconds until the next market open (9:30 ET, Mon-Fri)."""
    now = _now_et()
    # Try today first
    candidate = now.replace(hour=9, minute=30, second=0, microsecond=0)
    if candidate <= now or now.weekday() >= 5:
        # Roll forward to next weekday
        candidate += timedelta(days=1)
        while candidate.weekday() >= 5:
            candidate += timedelta(days=1)
        candidate = candidate.replace(hour=9, minute=30, second=0, microsecond=0)
    return max((candidate - now).total_seconds(), 0)


def _seconds_until_close() -> float:
    now = _now_et()
    close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return max((close - now).total_seconds(), 0)


def run_scheduler() -> None:
    port.init_db()

    def _shutdown(sig, _frame):
        logger.info("Scheduler shutting down.")
        sys.exit(0)

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    symbols = list(STOCKS.keys())
    logger.info("Stock Agent scheduler started.")

    while True:
        if not _is_market_open():
            wait = _seconds_until_open()
            open_at = _now_et() + timedelta(seconds=wait)
            logger.info(
                f"Market closed. Next open: {open_at.strftime('%A %Y-%m-%d %H:%M ET')} "
                f"({wait/3600:.1f} h away)"
            )
            time.sleep(min(wait, 3600))   # wake up at least hourly to re-check
            continue

        # ── market is open ─────────────────────────────────────────────────
        logger.info("Market is open — beginning trading session.")

        while _is_market_open():
            try:
                prices  = get_current_prices(symbols)
                p_str   = "  ".join(f"{s}=${v:.2f}" for s, v in prices.items())
                logger.info(f"Prices — {p_str}")
                actions = run_cycle(prices)
                for a in actions:
                    logger.info(f"  TRADE {a}")
            except Exception as exc:
                logger.error(f"Cycle error: {exc}")

            # Sleep until next cycle (or market close, whichever is sooner)
            sleep_for = min(POLL_INTERVAL, _seconds_until_close())
            if sleep_for > 0:
                time.sleep(sleep_for)

        logger.info("Market closed for the day.")
