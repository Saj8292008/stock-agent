"""
Mock Alpaca API responses for testing.

This module contains realistic mock responses for all Alpaca API endpoints
to enable testing without actual broker connections.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone


def mock_account_response(
    cash: float = 100000.0,
    buying_power: float = 100000.0,
    portfolio_value: float = 100000.0
) -> Dict[str, Any]:
    """
    Mock Alpaca account response.

    Args:
        cash: Available cash
        buying_power: Total buying power
        portfolio_value: Total portfolio value

    Returns:
        Mock account data dictionary
    """
    return {
        "id": "test-account-id",
        "account_number": "TEST123456",
        "status": "ACTIVE",
        "currency": "USD",
        "cash": str(cash),
        "buying_power": str(buying_power),
        "portfolio_value": str(portfolio_value),
        "pattern_day_trader": False,
        "trading_blocked": False,
        "transfers_blocked": False,
        "account_blocked": False,
        "created_at": "2024-01-01T00:00:00Z",
        "trade_suspended_by_user": False,
        "multiplier": "1",
        "shorting_enabled": False,
        "equity": str(portfolio_value),
        "last_equity": str(portfolio_value),
        "long_market_value": str(portfolio_value - cash),
        "short_market_value": "0",
        "initial_margin": "0",
        "maintenance_margin": "0",
        "last_maintenance_margin": "0",
        "sma": "0",
        "daytrade_count": 0
    }


def mock_order_response(
    order_id: str = "test-order-123",
    symbol: str = "AAPL",
    qty: float = 10,
    side: str = "buy",
    order_type: str = "market",
    status: str = "filled",
    filled_avg_price: float = 150.0,
    limit_price: float = None,
    stop_price: float = None
) -> Dict[str, Any]:
    """
    Mock Alpaca order response.

    Args:
        order_id: Order ID
        symbol: Stock symbol
        qty: Order quantity
        side: Order side (buy/sell)
        order_type: Order type (market/limit/stop)
        status: Order status
        filled_avg_price: Average fill price
        limit_price: Limit price (for limit orders)
        stop_price: Stop price (for stop orders)

    Returns:
        Mock order data dictionary
    """
    now = datetime.now(timezone.utc).isoformat()

    order = {
        "id": order_id,
        "client_order_id": f"client-{order_id}",
        "created_at": now,
        "updated_at": now,
        "submitted_at": now,
        "filled_at": now if status == "filled" else None,
        "expired_at": None,
        "canceled_at": None if status != "canceled" else now,
        "failed_at": None if status != "rejected" else now,
        "replaced_at": None,
        "replaced_by": None,
        "replaces": None,
        "asset_id": "test-asset-id",
        "symbol": symbol,
        "asset_class": "us_equity",
        "notional": None,
        "qty": str(qty),
        "filled_qty": str(qty) if status == "filled" else "0",
        "filled_avg_price": str(filled_avg_price) if status == "filled" else None,
        "order_class": "",
        "order_type": order_type,
        "type": order_type,
        "side": side,
        "time_in_force": "day",
        "limit_price": str(limit_price) if limit_price else None,
        "stop_price": str(stop_price) if stop_price else None,
        "status": status,
        "extended_hours": False,
        "legs": None,
        "trail_percent": None,
        "trail_price": None,
        "hwm": None
    }

    return order


def mock_position_response(
    symbol: str = "AAPL",
    qty: float = 10,
    avg_entry_price: float = 150.0,
    current_price: float = 155.0
) -> Dict[str, Any]:
    """
    Mock Alpaca position response.

    Args:
        symbol: Stock symbol
        qty: Position quantity
        avg_entry_price: Average entry price
        current_price: Current market price

    Returns:
        Mock position data dictionary
    """
    market_value = qty * current_price
    cost_basis = qty * avg_entry_price
    unrealized_pl = market_value - cost_basis
    unrealized_plpc = (unrealized_pl / cost_basis) if cost_basis > 0 else 0.0

    return {
        "asset_id": "test-asset-id",
        "symbol": symbol,
        "exchange": "NASDAQ",
        "asset_class": "us_equity",
        "avg_entry_price": str(avg_entry_price),
        "qty": str(qty),
        "side": "long",
        "market_value": str(market_value),
        "cost_basis": str(cost_basis),
        "unrealized_pl": str(unrealized_pl),
        "unrealized_plpc": str(unrealized_plpc),
        "unrealized_intraday_pl": str(unrealized_pl),
        "unrealized_intraday_plpc": str(unrealized_plpc),
        "current_price": str(current_price),
        "lastday_price": str(current_price * 0.99),
        "change_today": str(unrealized_plpc)
    }


def mock_quote_response(
    symbol: str = "AAPL",
    bid_price: float = 149.95,
    ask_price: float = 150.05,
    last_price: float = 150.0
) -> Dict[str, Any]:
    """
    Mock Alpaca quote response.

    Args:
        symbol: Stock symbol
        bid_price: Bid price
        ask_price: Ask price
        last_price: Last trade price

    Returns:
        Mock quote data dictionary
    """
    now = datetime.now(timezone.utc).isoformat()

    return {
        "symbol": symbol,
        "bid_price": bid_price,
        "bid_size": 100,
        "ask_price": ask_price,
        "ask_size": 100,
        "last_price": last_price,
        "last_size": 100,
        "timestamp": now
    }


def mock_bars_response(
    symbol: str = "AAPL",
    num_bars: int = 5,
    start_price: float = 150.0
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Mock Alpaca historical bars response.

    Args:
        symbol: Stock symbol
        num_bars: Number of bars to generate
        start_price: Starting price

    Returns:
        Mock bars data dictionary
    """
    bars = []
    price = start_price

    for i in range(num_bars):
        # Simulate price movement
        price = price * (1 + (i % 3 - 1) * 0.01)

        bar = {
            "t": datetime.now(timezone.utc).isoformat(),
            "o": price,
            "h": price * 1.01,
            "l": price * 0.99,
            "c": price,
            "v": 1000000,
            "n": 1000,
            "vw": price
        }
        bars.append(bar)

    return {
        "bars": {
            symbol: bars
        }
    }


def mock_error_response(
    code: int = 40010000,
    message: str = "Invalid request"
) -> Dict[str, Any]:
    """
    Mock Alpaca error response.

    Args:
        code: Error code
        message: Error message

    Returns:
        Mock error data dictionary
    """
    return {
        "code": code,
        "message": message
    }


# Common error scenarios
RATE_LIMIT_ERROR = mock_error_response(
    code=42910000,
    message="Rate limit exceeded"
)

INVALID_SYMBOL_ERROR = mock_error_response(
    code=40010001,
    message="Invalid symbol"
)

INSUFFICIENT_FUNDS_ERROR = mock_error_response(
    code=40310000,
    message="Insufficient buying power"
)

MARKET_CLOSED_ERROR = mock_error_response(
    code=40310001,
    message="Market is closed"
)
