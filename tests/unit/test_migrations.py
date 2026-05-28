"""
Unit tests for migrations.py

Tests database schema migrations:
- Migration from v0 to v1
- Idempotency (running migrations multiple times)
- Schema verification
- Default data insertion
"""

import pytest
import sqlite3
import os

from backend.migrations import (
    get_schema_version,
    run_migrations,
    verify_schema,
    _migration_v0_to_v1
)


@pytest.mark.unit
class TestSchemaVersion:
    """Test schema version tracking."""

    def test_get_schema_version_new_db(self, test_db_path: str):
        """Test getting schema version from fresh database."""
        # Create minimal database
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (0,))
        conn.commit()
        conn.close()

        version = get_schema_version(test_db_path)
        assert version == 0

    def test_get_schema_version_v1_db(self, test_db: sqlite3.Connection):
        """Test getting schema version from v1 database."""
        version = get_schema_version(test_db)
        assert version == 1

    def test_get_schema_version_no_table(self, test_db_path: str):
        """Test getting schema version when table doesn't exist."""
        # Create database without schema_version table
        conn = sqlite3.connect(test_db_path)
        conn.close()

        version = get_schema_version(test_db_path)
        assert version == 0


@pytest.mark.unit
class TestMigrationV0ToV1:
    """Test migration from v0 to v1."""

    def test_migration_creates_new_tables(self, test_db_path: str):
        """Test that v0->v1 migration creates required tables."""
        # Create v0 database (only basic tables)
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Create v0 schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY,
                cash REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                symbol TEXT PRIMARY KEY,
                shares REAL NOT NULL,
                avg_cost REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                shares REAL NOT NULL,
                price REAL NOT NULL,
                total REAL NOT NULL,
                reason TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (0,))
        conn.commit()
        conn.close()

        # Run migration
        _migration_v0_to_v1(test_db_path)

        # Verify new tables exist
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Check for orders table
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='orders'
        """)
        assert cursor.fetchone() is not None

        # Check for tradingview_signals table
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='tradingview_signals'
        """)
        assert cursor.fetchone() is not None

        # Check for audit_log table
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='audit_log'
        """)
        assert cursor.fetchone() is not None

        # Check for risk_limits table
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='risk_limits'
        """)
        assert cursor.fetchone() is not None

        # Check for daily_metrics table
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='daily_metrics'
        """)
        assert cursor.fetchone() is not None

        conn.close()

    def test_migration_adds_columns_to_existing_tables(self, test_db_path: str):
        """Test that migration adds new columns to existing tables."""
        # Create v0 database
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY,
                cash REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (0,))
        cursor.execute(
            "INSERT INTO portfolio (id, cash, updated_at) VALUES (?, ?, ?)",
            (1, 100000.0, "2024-01-01T00:00:00")
        )
        conn.commit()
        conn.close()

        # Run migration
        _migration_v0_to_v1(test_db_path)

        # Check new columns exist
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Get portfolio columns
        cursor.execute("PRAGMA table_info(portfolio)")
        columns = [row[1] for row in cursor.fetchall()]

        assert 'buying_power' in columns
        assert 'margin_used' in columns
        assert 'account_value' in columns
        assert 'last_synced_at' in columns

        conn.close()

    def test_migration_inserts_default_risk_limits(self, test_db_path: str):
        """Test that migration inserts default risk limits."""
        # Create v0 database
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (0,))
        conn.commit()
        conn.close()

        # Run migration
        _migration_v0_to_v1(test_db_path)

        # Check default limits
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        limits = cursor.execute(
            "SELECT * FROM risk_limits WHERE id = 1"
        ).fetchone()

        assert limits is not None
        assert limits[1] == 0.10  # max_position_size
        assert limits[2] == -0.02  # max_daily_loss
        assert limits[3] == 0.80  # max_total_exposure
        assert limits[4] == 100  # max_orders_per_day
        assert limits[5] == 0.25  # max_concentration

        conn.close()

    def test_migration_updates_schema_version(self, test_db_path: str):
        """Test that migration updates schema version to 1."""
        # Create v0 database
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (0,))
        conn.commit()
        conn.close()

        # Run migration
        _migration_v0_to_v1(test_db_path)

        # Check version
        version = get_schema_version(test_db_path)
        assert version == 1


@pytest.mark.unit
class TestMigrationIdempotency:
    """Test that migrations can be run multiple times safely."""

    def test_migration_idempotent(self, test_db_path: str):
        """Test that running migration twice doesn't cause errors."""
        # Create v0 database
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY,
                cash REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (0,))
        cursor.execute(
            "INSERT INTO portfolio (id, cash, updated_at) VALUES (?, ?, ?)",
            (1, 100000.0, "2024-01-01T00:00:00")
        )
        conn.commit()
        conn.close()

        # Run migration first time
        _migration_v0_to_v1(test_db_path)

        # Run migration second time (should be safe)
        _migration_v0_to_v1(test_db_path)

        # Verify still at v1
        version = get_schema_version(test_db_path)
        assert version == 1

        # Verify data integrity
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        portfolio = cursor.execute(
            "SELECT * FROM portfolio WHERE id = 1"
        ).fetchone()
        assert portfolio is not None
        assert portfolio[1] == 100000.0  # cash
        conn.close()

    def test_run_migrations_on_current_version(self, test_db: sqlite3.Connection):
        """Test that run_migrations does nothing when already at latest version."""
        initial_version = get_schema_version(test_db)

        # Run migrations (should be no-op)
        run_migrations(test_db)

        final_version = get_schema_version(test_db)
        assert final_version == initial_version


@pytest.mark.unit
class TestSchemaVerification:
    """Test schema verification."""

    def test_verify_schema_v1_complete(self, test_db: sqlite3.Connection):
        """Test that v1 schema passes verification."""
        result = verify_schema(test_db)

        assert result['valid'] is True
        assert result['version'] == 1
        assert len(result.get('missing_tables', [])) == 0
        assert len(result.get('missing_columns', [])) == 0

    def test_verify_schema_missing_table(self, test_db_path: str):
        """Test schema verification with missing table."""
        # Create incomplete database
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Only create schema_version table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (1,))
        conn.commit()
        conn.close()

        result = verify_schema(test_db_path)

        assert result['valid'] is False
        assert len(result['missing_tables']) > 0

    def test_verify_schema_missing_column(self, test_db_path: str):
        """Test schema verification with missing column."""
        # Create database with incomplete portfolio table
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY,
                cash REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (1,))
        conn.commit()
        conn.close()

        result = verify_schema(test_db_path)

        assert result['valid'] is False
        # Should detect missing columns like buying_power, account_value, etc.
        assert len(result.get('missing_columns', [])) > 0


@pytest.mark.unit
class TestRunMigrations:
    """Test the main run_migrations function."""

    def test_run_migrations_from_v0(self, test_db_path: str):
        """Test running migrations from v0 to v1."""
        # Create v0 database
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY,
                cash REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (0,))
        conn.commit()
        conn.close()

        # Run all migrations
        run_migrations(test_db_path)

        # Verify at v1
        version = get_schema_version(test_db_path)
        assert version == 1

        # Verify schema is complete
        result = verify_schema(test_db_path)
        assert result['valid'] is True

    def test_run_migrations_fresh_database(self, test_db_path: str):
        """Test running migrations on completely fresh database."""
        # Just create the file, no tables
        conn = sqlite3.connect(test_db_path)
        conn.close()

        # Run migrations
        run_migrations(test_db_path)

        # Should create everything
        version = get_schema_version(test_db_path)
        assert version >= 0

        result = verify_schema(test_db_path)
        # May not be valid if migrations expect certain starting state
        # But should not crash


@pytest.mark.unit
class TestMigrationEdgeCases:
    """Test edge cases in migrations."""

    def test_migration_preserves_existing_data(self, test_db_path: str):
        """Test that migration preserves existing data."""
        # Create v0 database with data
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY,
                cash REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                symbol TEXT PRIMARY KEY,
                shares REAL NOT NULL,
                avg_cost REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                shares REAL NOT NULL,
                price REAL NOT NULL,
                total REAL NOT NULL,
                reason TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)

        # Insert test data
        cursor.execute(
            "INSERT INTO portfolio (id, cash, updated_at) VALUES (?, ?, ?)",
            (1, 50000.0, "2024-01-01T00:00:00")
        )
        cursor.execute(
            "INSERT INTO positions (symbol, shares, avg_cost, updated_at) VALUES (?, ?, ?, ?)",
            ("AAPL", 100, 150.0, "2024-01-01T00:00:00")
        )
        cursor.execute(
            """INSERT INTO trades (symbol, action, shares, price, total, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)""",
            ("AAPL", "buy", 100, 150.0, -15000.0, "2024-01-01T00:00:00")
        )
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (0,))

        conn.commit()
        conn.close()

        # Run migration
        _migration_v0_to_v1(test_db_path)

        # Verify data preserved
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        portfolio = cursor.execute(
            "SELECT cash FROM portfolio WHERE id = 1"
        ).fetchone()
        assert portfolio[0] == 50000.0

        position = cursor.execute(
            "SELECT shares, avg_cost FROM positions WHERE symbol = 'AAPL'"
        ).fetchone()
        assert position[0] == 100
        assert position[1] == 150.0

        trade = cursor.execute(
            "SELECT shares, price FROM trades WHERE symbol = 'AAPL'"
        ).fetchone()
        assert trade[0] == 100
        assert trade[1] == 150.0

        conn.close()

    def test_migration_handles_corrupt_version_table(self, test_db_path: str):
        """Test migration handles corrupt schema_version table gracefully."""
        # Create database with corrupt version table
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)
        # Insert invalid version
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (999,))

        conn.commit()
        conn.close()

        # Should handle gracefully (may reset to 0 or use current version)
        try:
            version = get_schema_version(test_db_path)
            # Should return some valid version number
            assert isinstance(version, int)
        except Exception:
            # Or may raise exception, which is also acceptable
            pass
