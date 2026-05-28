"""
Database migrations for stock-agent.

This module handles upgrading the database schema from the basic paper trading
version to the full live trading version with TradingView integration, broker
connectivity, and risk management.
"""

import sqlite3
import logging
from typing import Optional
from datetime import datetime, timezone

from .config import DB_PATH

logger = logging.getLogger(__name__)


def _conn() -> sqlite3.Connection:
    """Create a database connection."""
    return sqlite3.connect(DB_PATH)


def _now() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def get_schema_version() -> int:
    """
    Get the current schema version.

    Returns:
        Schema version number (0 if no version table exists)
    """
    con = _conn()
    cur = con.cursor()

    try:
        # Check if schema_version table exists
        result = cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        ).fetchone()

        if not result:
            con.close()
            return 0

        # Get current version
        version_row = cur.execute("SELECT version FROM schema_version ORDER BY id DESC LIMIT 1").fetchone()
        con.close()
        return version_row[0] if version_row else 0
    except Exception as e:
        logger.error(f"Failed to get schema version: {e}")
        con.close()
        return 0


def set_schema_version(version: int) -> None:
    """
    Set the schema version.

    Args:
        version: Version number to set
    """
    con = _conn()
    cur = con.cursor()

    # Create schema_version table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version INTEGER NOT NULL,
            applied_at TEXT NOT NULL
        )
    """)

    # Insert new version
    cur.execute(
        "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
        (version, _now())
    )

    con.commit()
    con.close()
    logger.info(f"Schema version set to {version}")


def migrate_to_v1() -> None:
    """
    Migrate from v0 (paper trading) to v1 (live trading with broker integration).

    This migration adds:
    - orders table: Track broker order submissions and fills
    - tradingview_signals table: Store incoming webhook signals
    - audit_log table: Comprehensive audit trail
    - daily_metrics table: Daily performance tracking
    - risk_limits table: Configurable risk parameters
    - daily_pnl table: Daily profit/loss tracking
    - Extended trades table with broker-related fields
    - Extended portfolio table with broker account fields
    """
    con = _conn()
    cur = con.cursor()

    logger.info("Starting migration to v1...")

    # Create orders table
    cur.execute("""
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
            signal_id INTEGER,
            FOREIGN KEY (signal_id) REFERENCES tradingview_signals(id)
        )
    """)

    # Create tradingview_signals table
    cur.execute("""
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
            rejection_reason TEXT,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    """)

    # Create audit_log table
    cur.execute("""
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

    # Create daily_metrics table
    cur.execute("""
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

    # Create risk_limits table
    cur.execute("""
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

    # Create daily_pnl table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_pnl (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            realized_pnl REAL DEFAULT 0,
            unrealized_pnl REAL DEFAULT 0,
            total_pnl REAL DEFAULT 0,
            timestamp TEXT NOT NULL,
            UNIQUE(date, symbol)
        )
    """)

    # Check if trades table needs to be extended
    # Get existing columns
    existing_cols = [row[1] for row in cur.execute("PRAGMA table_info(trades)").fetchall()]

    # Add new columns if they don't exist
    new_trade_columns = {
        'order_id': 'INTEGER',
        'commission': 'REAL DEFAULT 0',
        'slippage': 'REAL DEFAULT 0',
        'pnl': 'REAL',
        'strategy_name': 'TEXT'
    }

    for col_name, col_type in new_trade_columns.items():
        if col_name not in existing_cols:
            try:
                cur.execute(f"ALTER TABLE trades ADD COLUMN {col_name} {col_type}")
                logger.info(f"Added column {col_name} to trades table")
            except sqlite3.OperationalError as e:
                logger.warning(f"Could not add column {col_name}: {e}")

    # Check if portfolio table needs to be extended
    existing_portfolio_cols = [row[1] for row in cur.execute("PRAGMA table_info(portfolio)").fetchall()]

    # Add new columns to portfolio
    new_portfolio_columns = {
        'buying_power': 'REAL',
        'margin_used': 'REAL DEFAULT 0',
        'account_value': 'REAL',
        'last_synced_at': 'TEXT',
        'emergency_stop': 'INTEGER DEFAULT 0'
    }

    for col_name, col_type in new_portfolio_columns.items():
        if col_name not in existing_portfolio_cols:
            try:
                cur.execute(f"ALTER TABLE portfolio ADD COLUMN {col_name} {col_type}")
                logger.info(f"Added column {col_name} to portfolio table")
            except sqlite3.OperationalError as e:
                logger.warning(f"Could not add column {col_name}: {e}")

    # Create indexes for performance
    indexes = [
        ("idx_orders_symbol", "orders", "symbol"),
        ("idx_orders_status", "orders", "status"),
        ("idx_orders_submitted_at", "orders", "submitted_at"),
        ("idx_signals_symbol", "tradingview_signals", "symbol"),
        ("idx_signals_received_at", "tradingview_signals", "received_at"),
        ("idx_signals_status", "tradingview_signals", "status"),
        ("idx_audit_timestamp", "audit_log", "timestamp"),
        ("idx_audit_event_type", "audit_log", "event_type"),
        ("idx_daily_metrics_date", "daily_metrics", "date"),
        ("idx_trades_timestamp", "trades", "timestamp"),
        ("idx_trades_symbol", "trades", "symbol"),
    ]

    for idx_name, table_name, column_name in indexes:
        try:
            cur.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({column_name})")
            logger.info(f"Created index {idx_name}")
        except Exception as e:
            logger.warning(f"Could not create index {idx_name}: {e}")

    # Insert default risk limits if not exists
    existing_limits = cur.execute("SELECT id FROM risk_limits WHERE id = 1").fetchone()
    if not existing_limits:
        cur.execute("""
            INSERT INTO risk_limits (
                id, max_position_size, max_daily_loss, max_total_exposure,
                max_orders_per_day, max_concentration, enabled, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            1,
            0.10,   # max 10% per position
            -0.02,  # max 2% daily loss
            0.80,   # max 80% exposure
            100,    # max 100 orders per day
            0.25,   # max 25% in single stock
            1,      # enabled
            _now()
        ))
        logger.info("Inserted default risk limits")

    con.commit()
    con.close()

    logger.info("Migration to v1 completed successfully")


def run_migrations() -> None:
    """
    Run all pending migrations to bring database to latest schema version.

    This function checks the current schema version and applies any necessary
    migrations in sequence.
    """
    current_version = get_schema_version()
    target_version = 1  # Latest schema version

    logger.info(f"Current schema version: {current_version}")
    logger.info(f"Target schema version: {target_version}")

    if current_version >= target_version:
        logger.info("Database is already up to date")
        return

    # Apply migrations in sequence
    if current_version < 1:
        migrate_to_v1()
        set_schema_version(1)

    logger.info(f"Database migrated to version {target_version}")


def verify_schema() -> dict:
    """
    Verify the current database schema and return status information.

    Returns:
        Dictionary with schema verification results
    """
    con = _conn()
    cur = con.cursor()

    tables_expected = [
        'portfolio',
        'positions',
        'trades',
        'price_refs',
        'orders',
        'tradingview_signals',
        'audit_log',
        'daily_metrics',
        'risk_limits',
        'daily_pnl',
        'schema_version'
    ]

    existing_tables = [
        row[0] for row in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    ]

    missing_tables = [t for t in tables_expected if t not in existing_tables]

    result = {
        'schema_version': get_schema_version(),
        'tables_expected': len(tables_expected),
        'tables_found': len(existing_tables),
        'missing_tables': missing_tables,
        'is_valid': len(missing_tables) == 0
    }

    con.close()
    return result
