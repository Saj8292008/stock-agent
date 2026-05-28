"""
Pytest configuration and shared fixtures.

This module provides reusable fixtures for all tests including:
- Test database setup/teardown
- Mock broker clients
- Sample data
- FastAPI test client
"""

import os
import sqlite3
import tempfile
from datetime import datetime
from typing import Dict, Any, Generator
from unittest.mock import MagicMock, Mock
import pytest
from fastapi.testclient import TestClient

# Import fixtures
from tests.fixtures.mock_broker_responses import (
    mock_account_response,
    mock_order_response,
    mock_position_response,
    mock_quote_response
)
from tests.fixtures.sample_signals import valid_buy_signal, valid_sell_signal


@pytest.fixture
def test_db_path() -> Generator[str, None, None]:
    """
    Create a temporary test database.

    Yields:
        Path to temporary test database

    Cleanup:
        Removes temporary database file after test
    """
    # Create temporary file
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    yield path

    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def test_db(test_db_path: str) -> Generator[sqlite3.Connection, None, None]:
    """
    Create and initialize a test database with schema.

    Args:
        test_db_path: Path to test database

    Yields:
        Database connection

    Cleanup:
        Closes connection after test
    """
    # Set environment variable for backend modules
    os.environ['DB_PATH'] = test_db_path

    # Create connection
    conn = sqlite3.connect(test_db_path)
    conn.row_factory = sqlite3.Row

    # Initialize schema
    _initialize_test_schema(conn)

    yield conn

    conn.close()


def _initialize_test_schema(conn: sqlite3.Connection) -> None:
    """
    Initialize test database schema.

    Args:
        conn: Database connection
    """
    cursor = conn.cursor()

    # Portfolio table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY,
            cash REAL NOT NULL,
            updated_at TEXT NOT NULL,
            buying_power REAL,
            margin_used REAL DEFAULT 0,
            account_value REAL,
            last_synced_at TEXT
        )
    """)

    # Positions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            symbol TEXT PRIMARY KEY,
            shares REAL NOT NULL,
            avg_cost REAL NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # Trades table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            shares REAL NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL,
            reason TEXT,
            timestamp TEXT NOT NULL,
            order_id INTEGER,
            commission REAL DEFAULT 0,
            slippage REAL DEFAULT 0,
            pnl REAL,
            strategy_name TEXT
        )
    """)

    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            broker_order_id TEXT UNIQUE,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            order_type TEXT NOT NULL,
            quantity REAL NOT NULL,
            limit_price REAL,
            stop_price REAL,
            status TEXT NOT NULL,
            filled_qty REAL DEFAULT 0,
            avg_fill_price REAL,
            commission REAL DEFAULT 0,
            submitted_at TEXT NOT NULL,
            filled_at TEXT,
            canceled_at TEXT,
            error_message TEXT,
            strategy_name TEXT,
            signal_id INTEGER
        )
    """)

    # TradingView signals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tradingview_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            strategy TEXT,
            price REAL,
            quantity REAL,
            stop_loss REAL,
            take_profit REAL,
            raw_payload TEXT,
            received_at TEXT NOT NULL,
            processed_at TEXT,
            order_id INTEGER,
            status TEXT NOT NULL,
            rejection_reason TEXT
        )
    """)

    # Audit log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            symbol TEXT,
            user_action TEXT,
            data TEXT,
            result TEXT,
            message TEXT,
            timestamp TEXT NOT NULL
        )
    """)

    # Risk limits table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_limits (
            id INTEGER PRIMARY KEY,
            max_position_size REAL NOT NULL,
            max_daily_loss REAL NOT NULL,
            max_total_exposure REAL NOT NULL,
            max_orders_per_day INTEGER NOT NULL,
            max_concentration REAL NOT NULL,
            enabled INTEGER DEFAULT 1,
            updated_at TEXT NOT NULL
        )
    """)

    # Daily metrics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            starting_value REAL NOT NULL,
            ending_value REAL NOT NULL,
            daily_pnl REAL NOT NULL,
            daily_return_pct REAL NOT NULL,
            trades_count INTEGER DEFAULT 0,
            winners_count INTEGER DEFAULT 0,
            losers_count INTEGER DEFAULT 0,
            largest_win REAL DEFAULT 0,
            largest_loss REAL DEFAULT 0,
            updated_at TEXT NOT NULL
        )
    """)

    # Schema version table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY
        )
    """)

    # Insert default data
    cursor.execute(
        "INSERT INTO portfolio (id, cash, updated_at, buying_power, account_value) VALUES (?, ?, ?, ?, ?)",
        (1, 100000.0, datetime.now().isoformat(), 100000.0, 100000.0)
    )

    cursor.execute(
        """INSERT INTO risk_limits
        (id, max_position_size, max_daily_loss, max_total_exposure, max_orders_per_day, max_concentration, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (1, 0.10, -0.02, 0.80, 100, 0.25, datetime.now().isoformat())
    )

    cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (1,))

    conn.commit()


@pytest.fixture
def mock_broker_client() -> MagicMock:
    """
    Create a mock Alpaca broker client.

    Returns:
        Mock broker client with common methods
    """
    mock_client = MagicMock()

    # Mock account method
    mock_client.get_account.return_value = mock_account_response()

    # Mock order submission
    mock_client.submit_market_order.return_value = mock_order_response()
    mock_client.submit_limit_order.return_value = mock_order_response(order_type="limit")
    mock_client.submit_stop_order.return_value = mock_order_response(order_type="stop")

    # Mock order status
    mock_client.get_order_status.return_value = mock_order_response(status="filled")
    mock_client.wait_for_order_fill.return_value = mock_order_response(status="filled")

    # Mock positions
    mock_client.get_positions.return_value = []
    mock_client.get_position.return_value = None

    # Mock quotes
    mock_client.get_latest_quote.return_value = mock_quote_response()

    # Mock cancel
    mock_client.cancel_order.return_value = True

    return mock_client


@pytest.fixture
def test_portfolio(test_db: sqlite3.Connection) -> Dict[str, Any]:
    """
    Create a test portfolio with sample data.

    Args:
        test_db: Test database connection

    Returns:
        Portfolio data dictionary
    """
    cursor = test_db.cursor()

    # Add sample positions
    positions = [
        ("AAPL", 10, 150.0),
        ("GOOGL", 5, 140.0),
        ("MSFT", 8, 380.0)
    ]

    for symbol, shares, avg_cost in positions:
        cursor.execute(
            "INSERT INTO positions (symbol, shares, avg_cost, updated_at) VALUES (?, ?, ?, ?)",
            (symbol, shares, avg_cost, datetime.now().isoformat())
        )

    # Add sample trades
    trades = [
        ("AAPL", "buy", 10, 150.0, -1500.0, "Initial purchase"),
        ("GOOGL", "buy", 5, 140.0, -700.0, "Initial purchase"),
        ("MSFT", "buy", 8, 380.0, -3040.0, "Initial purchase")
    ]

    for symbol, action, shares, price, total, reason in trades:
        cursor.execute(
            """INSERT INTO trades (symbol, action, shares, price, total, reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (symbol, action, shares, price, total, reason, datetime.now().isoformat())
        )

    test_db.commit()

    return {
        "cash": 94760.0,  # 100000 - 1500 - 700 - 3040
        "positions": positions,
        "trades": trades
    }


@pytest.fixture
def sample_buy_signal() -> Dict[str, Any]:
    """
    Get a sample buy signal from TradingView.

    Returns:
        Buy signal payload
    """
    return valid_buy_signal()


@pytest.fixture
def sample_sell_signal() -> Dict[str, Any]:
    """
    Get a sample sell signal from TradingView.

    Returns:
        Sell signal payload
    """
    return valid_sell_signal()


@pytest.fixture
def test_app(test_db_path: str, monkeypatch) -> TestClient:
    """
    Create a FastAPI test client.

    Args:
        test_db_path: Path to test database
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        FastAPI TestClient
    """
    # Set environment variables
    monkeypatch.setenv('DB_PATH', test_db_path)
    monkeypatch.setenv('BROKER_ENABLED', 'false')
    monkeypatch.setenv('TRADINGVIEW_ENABLED', 'true')
    monkeypatch.setenv('TRADINGVIEW_PASSPHRASE', 'test_passphrase')
    monkeypatch.setenv('ENABLE_RISK_MANAGER', 'true')

    # Import app after setting env vars
    from backend.api import app

    return TestClient(app)


@pytest.fixture
def mock_yfinance(monkeypatch) -> Mock:
    """
    Mock yfinance for price data.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        Mock yfinance module
    """
    mock_ticker = Mock()
    mock_ticker.info = {
        'regularMarketPrice': 150.0,
        'previousClose': 148.0
    }
    mock_ticker.history.return_value = Mock(
        empty=False,
        iloc=[-1]
    )

    mock_yf = Mock()
    mock_yf.Ticker.return_value = mock_ticker

    monkeypatch.setattr('yfinance.Ticker', mock_yf.Ticker)

    return mock_yf


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """
    Reset environment variables before each test.

    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    # Set default test environment
    monkeypatch.setenv('BROKER_ENABLED', 'false')
    monkeypatch.setenv('TRADINGVIEW_ENABLED', 'false')
    monkeypatch.setenv('ENABLE_RISK_MANAGER', 'true')
    monkeypatch.setenv('EMERGENCY_STOP_FILE', '/tmp/test_emergency_stop')

    # Clean up emergency stop file
    if os.path.exists('/tmp/test_emergency_stop'):
        os.remove('/tmp/test_emergency_stop')
