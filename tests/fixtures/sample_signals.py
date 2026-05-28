"""
Sample TradingView signals for testing.

This module contains sample webhook payloads from TradingView
for testing signal processing and order execution.
"""

from typing import Dict, Any


def valid_buy_signal(
    symbol: str = "AAPL",
    price: float = 150.0,
    quantity: float = 10,
    passphrase: str = "test_passphrase"
) -> Dict[str, Any]:
    """
    Generate a valid buy signal from TradingView.

    Args:
        symbol: Stock symbol
        price: Current price
        quantity: Number of shares
        passphrase: Authentication passphrase

    Returns:
        TradingView webhook payload
    """
    return {
        "passphrase": passphrase,
        "ticker": symbol,
        "action": "buy",
        "strategy": "RSI Oversold",
        "price": price,
        "quantity": quantity
    }


def valid_sell_signal(
    symbol: str = "AAPL",
    price: float = 160.0,
    quantity: float = 10,
    passphrase: str = "test_passphrase"
) -> Dict[str, Any]:
    """
    Generate a valid sell signal from TradingView.

    Args:
        symbol: Stock symbol
        price: Current price
        quantity: Number of shares
        passphrase: Authentication passphrase

    Returns:
        TradingView webhook payload
    """
    return {
        "passphrase": passphrase,
        "ticker": symbol,
        "action": "sell",
        "strategy": "RSI Overbought",
        "price": price,
        "quantity": quantity
    }


def signal_with_stop_loss(
    symbol: str = "AAPL",
    price: float = 150.0,
    quantity: float = 10,
    stop_loss: float = 145.0,
    passphrase: str = "test_passphrase"
) -> Dict[str, Any]:
    """
    Generate a signal with stop loss.

    Args:
        symbol: Stock symbol
        price: Current price
        quantity: Number of shares
        stop_loss: Stop loss price
        passphrase: Authentication passphrase

    Returns:
        TradingView webhook payload with stop loss
    """
    return {
        "passphrase": passphrase,
        "ticker": symbol,
        "action": "buy",
        "strategy": "Breakout with Stop",
        "price": price,
        "quantity": quantity,
        "stop_loss": stop_loss
    }


def signal_with_take_profit(
    symbol: str = "AAPL",
    price: float = 150.0,
    quantity: float = 10,
    take_profit: float = 165.0,
    passphrase: str = "test_passphrase"
) -> Dict[str, Any]:
    """
    Generate a signal with take profit.

    Args:
        symbol: Stock symbol
        price: Current price
        quantity: Number of shares
        take_profit: Take profit price
        passphrase: Authentication passphrase

    Returns:
        TradingView webhook payload with take profit
    """
    return {
        "passphrase": passphrase,
        "ticker": symbol,
        "action": "buy",
        "strategy": "Support Bounce",
        "price": price,
        "quantity": quantity,
        "take_profit": take_profit
    }


def invalid_passphrase_signal(
    symbol: str = "AAPL",
    price: float = 150.0,
    passphrase: str = "wrong_passphrase"
) -> Dict[str, Any]:
    """
    Generate a signal with invalid passphrase.

    Args:
        symbol: Stock symbol
        price: Current price
        passphrase: Invalid passphrase

    Returns:
        TradingView webhook payload with invalid passphrase
    """
    return {
        "passphrase": passphrase,
        "ticker": symbol,
        "action": "buy",
        "strategy": "Test",
        "price": price,
        "quantity": 10
    }


def missing_required_fields_signal() -> Dict[str, Any]:
    """
    Generate a signal missing required fields.

    Returns:
        Incomplete TradingView webhook payload
    """
    return {
        "passphrase": "test_passphrase",
        # Missing ticker
        "action": "buy",
        "price": 150.0
    }


def invalid_action_signal(
    symbol: str = "AAPL",
    passphrase: str = "test_passphrase"
) -> Dict[str, Any]:
    """
    Generate a signal with invalid action.

    Args:
        symbol: Stock symbol
        passphrase: Authentication passphrase

    Returns:
        TradingView webhook payload with invalid action
    """
    return {
        "passphrase": passphrase,
        "ticker": symbol,
        "action": "hold",  # Invalid action
        "price": 150.0,
        "quantity": 10
    }


def signal_with_all_fields(
    symbol: str = "AAPL",
    price: float = 150.0,
    quantity: float = 10,
    stop_loss: float = 145.0,
    take_profit: float = 165.0,
    passphrase: str = "test_passphrase"
) -> Dict[str, Any]:
    """
    Generate a comprehensive signal with all optional fields.

    Args:
        symbol: Stock symbol
        price: Current price
        quantity: Number of shares
        stop_loss: Stop loss price
        take_profit: Take profit price
        passphrase: Authentication passphrase

    Returns:
        Complete TradingView webhook payload
    """
    return {
        "passphrase": passphrase,
        "ticker": symbol,
        "action": "buy",
        "strategy": "Complete Strategy",
        "price": price,
        "quantity": quantity,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "timeframe": "1h",
        "position_size": "full",
        "risk_level": "medium"
    }


# Sample batch of signals for multi-signal testing
SAMPLE_SIGNAL_BATCH = [
    valid_buy_signal("AAPL", 150.0, 10),
    valid_buy_signal("GOOGL", 140.0, 5),
    valid_sell_signal("MSFT", 380.0, 8),
    signal_with_stop_loss("NVDA", 500.0, 3, 480.0),
    signal_with_take_profit("TSLA", 180.0, 6, 200.0)
]
