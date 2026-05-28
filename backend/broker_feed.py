"""
Broker data feed and synchronization utilities.

This module provides functions for fetching real-time prices from the broker
and synchronizing positions and account state between the broker and local database.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

from .broker_client import AlpacaBrokerClient
from . import portfolio as port

logger = logging.getLogger(__name__)


def _now() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def get_real_time_prices(broker_client: AlpacaBrokerClient, symbols: List[str]) -> Dict[str, float]:
    """
    Get real-time prices from Alpaca data feed.

    Args:
        broker_client: Initialized Alpaca broker client
        symbols: List of stock symbols

    Returns:
        Dictionary mapping symbols to current prices
    """
    prices = {}

    for symbol in symbols:
        try:
            # Try to get latest trade first (most accurate for current price)
            trade = broker_client.get_latest_trade(symbol)
            if trade and trade.get("price"):
                prices[symbol] = trade["price"]
                continue

            # Fallback to quote midpoint
            quote = broker_client.get_latest_quote(symbol)
            if quote:
                bid = quote.get("bid_price", 0)
                ask = quote.get("ask_price", 0)
                if bid > 0 and ask > 0:
                    prices[symbol] = (bid + ask) / 2
                elif ask > 0:
                    prices[symbol] = ask
                elif bid > 0:
                    prices[symbol] = bid

        except Exception as e:
            logger.warning(f"Failed to get real-time price for {symbol}: {e}")

    logger.info(f"Fetched real-time prices for {len(prices)}/{len(symbols)} symbols")
    return prices


def sync_positions_from_broker(broker_client: AlpacaBrokerClient) -> dict:
    """
    Synchronize positions from broker to local database.

    This reconciles the local position tracking with the actual broker positions,
    which is critical for ensuring accuracy when switching between paper and live
    trading or after manual trades.

    Args:
        broker_client: Initialized Alpaca broker client

    Returns:
        Dictionary with sync results including:
        - synced_count: Number of positions synchronized
        - added: List of symbols added
        - updated: List of symbols updated
        - removed: List of symbols removed
    """
    try:
        broker_positions = broker_client.get_positions()
    except Exception as e:
        logger.error(f"Failed to fetch positions from broker: {e}")
        return {"error": str(e), "synced_count": 0}

    local_positions = port.get_positions()

    added = []
    updated = []
    removed = []

    # Update local positions based on broker positions
    broker_symbols = set()

    for broker_pos in broker_positions:
        symbol = broker_pos["symbol"]
        shares = broker_pos["qty"]
        avg_cost = broker_pos["avg_entry_price"]

        broker_symbols.add(symbol)

        if symbol not in local_positions:
            # New position found in broker
            port.set_position(symbol, shares, avg_cost)
            added.append(symbol)
            logger.info(f"Added position from broker: {shares} shares of {symbol} @ ${avg_cost}")
        else:
            local_pos = local_positions[symbol]
            # Check if position differs
            if abs(local_pos["shares"] - shares) > 0.0001 or abs(local_pos["avg_cost"] - avg_cost) > 0.01:
                port.set_position(symbol, shares, avg_cost)
                updated.append(symbol)
                logger.info(f"Updated position from broker: {shares} shares of {symbol} @ ${avg_cost}")

    # Remove positions that exist locally but not in broker
    for symbol in local_positions:
        if symbol not in broker_symbols:
            port.set_position(symbol, 0, 0)
            removed.append(symbol)
            logger.info(f"Removed position (not in broker): {symbol}")

    result = {
        "synced_count": len(broker_positions),
        "added": added,
        "updated": updated,
        "removed": removed,
        "synced_at": _now()
    }

    logger.info(f"Position sync complete: {result['synced_count']} positions, "
                f"{len(added)} added, {len(updated)} updated, {len(removed)} removed")

    return result


def sync_account_from_broker(broker_client: AlpacaBrokerClient) -> Optional[dict]:
    """
    Synchronize account information from broker to local database.

    Updates the portfolio table with current cash, buying power, and account value
    from the broker.

    Args:
        broker_client: Initialized Alpaca broker client

    Returns:
        Dictionary with synced account info or None on failure
    """
    try:
        account = broker_client.get_account()
    except Exception as e:
        logger.error(f"Failed to fetch account from broker: {e}")
        return None

    if not account:
        logger.error("Broker returned no account data")
        return None

    # Update local portfolio with broker account data
    cash = account.get("cash", 0)
    buying_power = account.get("buying_power", 0)
    portfolio_value = account.get("portfolio_value", 0)

    # Update the portfolio table
    try:
        # Use the update_account function from portfolio module
        # (will be added in Phase 6)
        import sqlite3
        from .config import DB_PATH

        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()

        # Update portfolio table
        cur.execute("""
            UPDATE portfolio SET
                cash = ?,
                buying_power = ?,
                account_value = ?,
                last_synced_at = ?,
                updated_at = ?
            WHERE id = 1
        """, (cash, buying_power, portfolio_value, _now(), _now()))

        con.commit()
        con.close()

        logger.info(f"Synced account: cash=${cash:.2f}, buying_power=${buying_power:.2f}, "
                    f"portfolio_value=${portfolio_value:.2f}")

        return {
            "cash": cash,
            "buying_power": buying_power,
            "portfolio_value": portfolio_value,
            "synced_at": _now()
        }

    except Exception as e:
        logger.error(f"Failed to update local portfolio: {e}")
        return None


def get_current_market_prices(broker_client: AlpacaBrokerClient, symbols: List[str]) -> Dict[str, float]:
    """
    Get current market prices, preferring broker data feed over yfinance.

    This function attempts to use Alpaca's real-time data first, falling back
    to yfinance if broker data is unavailable.

    Args:
        broker_client: Initialized Alpaca broker client (or None for yfinance only)
        symbols: List of stock symbols

    Returns:
        Dictionary mapping symbols to current prices
    """
    if broker_client:
        # Try broker first
        prices = get_real_time_prices(broker_client, symbols)

        # If we got most prices, return them
        if len(prices) >= len(symbols) * 0.8:  # 80% success rate threshold
            return prices

        logger.info("Broker prices incomplete, falling back to yfinance")

    # Fallback to yfinance
    from .data_feed import get_current_prices
    return get_current_prices(symbols)
