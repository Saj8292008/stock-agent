"""Continuous paper-trading agent loop."""

import logging
import signal
import sys
import time

from backend.config import POLL_INTERVAL, STOCKS
from backend.data_feed import get_current_prices
from backend.trading_engine import run_cycle
from backend import portfolio as port

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    port.init_db()
    symbols = list(STOCKS.keys())
    logger.info(f"Agent started — tracking {', '.join(symbols)}")
    logger.info(f"Poll interval: {POLL_INTERVAL}s | Starting cash: ${port.get_cash():,.2f}")

    def _shutdown(sig, _frame):
        logger.info("Shutting down agent.")
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    while True:
        try:
            prices = get_current_prices(symbols)
            price_str = "  ".join(f"{s}=${v:.2f}" for s, v in prices.items())
            logger.info(f"Prices — {price_str}")
            actions = run_cycle(prices)
            if actions:
                for a in actions:
                    logger.info(f"  ACTION {a}")
        except Exception as exc:
            logger.error(f"Cycle error: {exc}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
