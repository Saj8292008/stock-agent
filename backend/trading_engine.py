import logging
from typing import Dict

from .config import (
    ALLOCATION_PER_STOCK,
    BUY_DIP_THRESHOLD,
    STOCKS,
    STOP_LOSS,
    TAKE_PROFIT,
)
from . import portfolio as port

logger = logging.getLogger(__name__)


def run_cycle(prices: Dict[str, float]) -> list:
    """Evaluate all tracked stocks and execute paper trades. Returns list of actions taken."""
    positions  = port.get_positions()
    cash       = port.get_cash()
    total_val  = cash + sum(
        pos["shares"] * prices.get(sym, pos["avg_cost"])
        for sym, pos in positions.items()
    )

    actions = []

    for symbol in STOCKS:
        price = prices.get(symbol)
        if not price:
            continue

        ref_price = port.get_ref_price(symbol)
        if ref_price is None:
            port.set_ref_price(symbol, price)
            ref_price = price

        position = positions.get(symbol)

        if position:
            pct = (price - position["avg_cost"]) / position["avg_cost"]

            if pct >= TAKE_PROFIT:
                action = _sell(symbol, position, price, f"Take profit {pct:+.1%}")
                actions.append(action)
            elif pct <= STOP_LOSS:
                action = _sell(symbol, position, price, f"Stop loss {pct:+.1%}")
                actions.append(action)

        else:
            pct_from_ref = (price - ref_price) / ref_price

            if pct_from_ref <= BUY_DIP_THRESHOLD:
                alloc  = total_val * ALLOCATION_PER_STOCK
                shares = alloc / price
                cost   = shares * price
                cash   = port.get_cash()

                if cash >= cost:
                    port.set_cash(cash - cost)
                    port.set_position(symbol, shares, price)
                    port.log_trade(symbol, "BUY", shares, price, f"Dip {pct_from_ref:+.1%} from ref")
                    port.set_ref_price(symbol, price)
                    logger.info(f"BUY  {shares:.4f} {symbol} @ ${price:.2f}")
                    actions.append({"action": "BUY", "symbol": symbol, "shares": shares, "price": price})
            else:
                # Ratchet reference price up as stock climbs
                if price > ref_price:
                    port.set_ref_price(symbol, price)

    return actions


def _sell(symbol: str, position: dict, price: float, reason: str) -> dict:
    shares   = position["shares"]
    proceeds = shares * price
    port.set_cash(port.get_cash() + proceeds)
    port.set_position(symbol, 0, 0)
    port.log_trade(symbol, "SELL", shares, price, reason)
    port.set_ref_price(symbol, price)
    logger.info(f"SELL {shares:.4f} {symbol} @ ${price:.2f} — {reason}")
    return {"action": "SELL", "symbol": symbol, "shares": shares, "price": price, "reason": reason}
