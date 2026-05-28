"""
Unit tests for risk_manager.py

Tests all 5 risk validation checks:
1. Maximum position size validation
2. Maximum concentration validation
3. Maximum total exposure validation
4. Daily loss limit enforcement
5. Daily trade count limit enforcement
"""

import pytest
import sqlite3
from datetime import datetime, date
from unittest.mock import patch, MagicMock

from backend.risk_manager import RiskManager


@pytest.mark.unit
class TestRiskManagerInitialization:
    """Test risk manager initialization and configuration."""

    def test_risk_manager_loads_limits(self, test_db: sqlite3.Connection):
        """Test that risk manager loads limits from database."""
        rm = RiskManager(db_path=test_db)

        assert rm.limits['max_position_size'] == 0.10
        assert rm.limits['max_daily_loss'] == -0.02
        assert rm.limits['max_total_exposure'] == 0.80
        assert rm.limits['max_orders_per_day'] == 100
        assert rm.limits['max_concentration'] == 0.25

    def test_risk_manager_disabled_mode(self, test_db: sqlite3.Connection):
        """Test risk manager in disabled mode."""
        # Disable risk manager in database
        cursor = test_db.cursor()
        cursor.execute("UPDATE risk_limits SET enabled = 0 WHERE id = 1")
        test_db.commit()

        rm = RiskManager(db_path=test_db)
        assert not rm.enabled

        # All validations should pass when disabled
        result = rm.validate_trade("AAPL", "buy", 1000, 150.0, 100000.0)
        assert result['approved'] is True

    def test_create_default_limits_if_missing(self, test_db_path: str):
        """Test that default limits are created if none exist."""
        # Create fresh connection without limits
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Create only required tables, no limits
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
        conn.commit()
        conn.close()

        # Risk manager should create defaults
        rm = RiskManager(db_path=test_db_path)
        assert rm.limits is not None
        assert rm.limits['max_position_size'] > 0


@pytest.mark.unit
class TestPositionSizeValidation:
    """Test maximum position size validation."""

    def test_position_size_within_limit(self, test_db: sqlite3.Connection):
        """Test that trade within position size limit is approved."""
        rm = RiskManager(db_path=test_db)

        # 10% limit, portfolio = $100k, max position = $10k
        # Buying $5k worth (50 shares @ $100) should pass
        result = rm.validate_trade("AAPL", "buy", 50, 100.0, 100000.0)

        assert result['approved'] is True
        assert 'position_size' not in result.get('violations', [])

    def test_position_size_exceeds_limit(self, test_db: sqlite3.Connection):
        """Test that trade exceeding position size limit is rejected."""
        rm = RiskManager(db_path=test_db)

        # 10% limit, portfolio = $100k, max position = $10k
        # Buying $15k worth (150 shares @ $100) should fail
        result = rm.validate_trade("AAPL", "buy", 150, 100.0, 100000.0)

        assert result['approved'] is False
        assert any('position size' in v.lower() for v in result.get('violations', []))

    def test_position_size_at_exact_limit(self, test_db: sqlite3.Connection):
        """Test that trade at exact position size limit is approved."""
        rm = RiskManager(db_path=test_db)

        # Exactly 10% of portfolio
        result = rm.validate_trade("AAPL", "buy", 100, 100.0, 100000.0)

        assert result['approved'] is True

    def test_sell_orders_always_approved_for_position_size(self, test_db: sqlite3.Connection):
        """Test that sell orders bypass position size checks."""
        rm = RiskManager(db_path=test_db)

        # Selling reduces risk, should always pass position size check
        result = rm.validate_trade("AAPL", "sell", 1000, 100.0, 100000.0)

        # May fail other checks, but not position size
        violations = result.get('violations', [])
        assert not any('position size' in v.lower() for v in violations)


@pytest.mark.unit
class TestConcentrationValidation:
    """Test maximum concentration validation."""

    def test_concentration_within_limit(self, test_db: sqlite3.Connection, test_portfolio):
        """Test that concentration within limit is approved."""
        rm = RiskManager(db_path=test_db)

        # Portfolio has AAPL position worth $1500 (10 @ $150)
        # Adding 50 shares @ $150 = $7500 more, total = $9000
        # Total portfolio ~$100k, concentration = 9%, within 25% limit
        result = rm.validate_trade("AAPL", "buy", 50, 150.0, 100000.0)

        assert result['approved'] is True
        assert 'concentration' not in result.get('violations', [])

    def test_concentration_exceeds_limit(self, test_db: sqlite3.Connection, test_portfolio):
        """Test that excessive concentration is rejected."""
        rm = RiskManager(db_path=test_db)

        # Buying massive position to exceed 25% concentration
        # 200 shares @ $150 = $30k, plus existing $1500 = $31.5k
        # Concentration = 31.5%, exceeds 25% limit
        result = rm.validate_trade("AAPL", "buy", 200, 150.0, 100000.0)

        assert result['approved'] is False
        assert any('concentration' in v.lower() for v in result.get('violations', []))

    def test_new_position_concentration(self, test_db: sqlite3.Connection):
        """Test concentration check for new position."""
        rm = RiskManager(db_path=test_db)

        # New position NVDA, 200 shares @ $500 = $100k
        # Concentration = 100%, exceeds 25% limit
        result = rm.validate_trade("NVDA", "buy", 200, 500.0, 100000.0)

        assert result['approved'] is False
        assert any('concentration' in v.lower() for v in result.get('violations', []))


@pytest.mark.unit
class TestTotalExposureValidation:
    """Test maximum total exposure validation."""

    def test_exposure_within_limit(self, test_db: sqlite3.Connection, test_portfolio):
        """Test that total exposure within limit is approved."""
        rm = RiskManager(db_path=test_db)

        # Current positions: ~$5240 invested
        # Adding $5000 = $10240 total, 10.24% exposure, within 80% limit
        result = rm.validate_trade("NVDA", "buy", 10, 500.0, 100000.0)

        assert result['approved'] is True
        assert 'exposure' not in result.get('violations', [])

    def test_exposure_exceeds_limit(self, test_db: sqlite3.Connection, test_portfolio):
        """Test that excessive exposure is rejected."""
        rm = RiskManager(db_path=test_db)

        # Buying $85k worth of stock (170 shares @ $500)
        # Total exposure would be ~90%, exceeds 80% limit
        result = rm.validate_trade("NVDA", "buy", 170, 500.0, 100000.0)

        assert result['approved'] is False
        assert any('exposure' in v.lower() for v in result.get('violations', []))


@pytest.mark.unit
class TestDailyLossLimit:
    """Test daily loss limit enforcement."""

    def test_daily_loss_within_limit(self, test_db: sqlite3.Connection):
        """Test that trading continues when daily loss is within limit."""
        rm = RiskManager(db_path=test_db)

        # Simulate -1% loss (within -2% limit)
        result = rm.validate_trade("AAPL", "buy", 10, 100.0, 100000.0, daily_pnl=-1000.0)

        assert result['approved'] is True
        assert 'daily loss' not in str(result.get('violations', [])).lower()

    def test_daily_loss_exceeds_limit(self, test_db: sqlite3.Connection):
        """Test that trading stops when daily loss limit is breached."""
        rm = RiskManager(db_path=test_db)

        # Simulate -3% loss (exceeds -2% limit)
        result = rm.validate_trade("AAPL", "buy", 10, 100.0, 100000.0, daily_pnl=-3000.0)

        assert result['approved'] is False
        assert any('daily loss' in v.lower() for v in result.get('violations', []))

    def test_daily_loss_at_exact_limit(self, test_db: sqlite3.Connection):
        """Test behavior at exact daily loss limit."""
        rm = RiskManager(db_path=test_db)

        # Exactly -2% loss
        result = rm.validate_trade("AAPL", "buy", 10, 100.0, 100000.0, daily_pnl=-2000.0)

        # Should be rejected (limit is maximum loss allowed)
        assert result['approved'] is False

    def test_sell_orders_allowed_during_daily_loss(self, test_db: sqlite3.Connection):
        """Test that sell orders are allowed even when daily loss limit breached."""
        rm = RiskManager(db_path=test_db)

        # Large daily loss, but selling to reduce exposure
        result = rm.validate_trade("AAPL", "sell", 10, 100.0, 100000.0, daily_pnl=-3000.0)

        # Sell should pass (reducing risk)
        # Note: Implementation may still allow sells
        # Check if it's approved or if daily_loss is not the blocking violation
        if not result['approved']:
            violations = result.get('violations', [])
            assert not any('daily loss' in v.lower() for v in violations)


@pytest.mark.unit
class TestDailyTradeCountLimit:
    """Test daily trade count limit enforcement."""

    def test_trade_count_within_limit(self, test_db: sqlite3.Connection):
        """Test that trades within daily limit are approved."""
        rm = RiskManager(db_path=test_db)

        # Add some trades for today
        cursor = test_db.cursor()
        today = date.today().isoformat()

        for i in range(50):
            cursor.execute(
                """INSERT INTO trades (symbol, action, shares, price, total, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)""",
                ("AAPL", "buy", 10, 100.0, -1000.0, f"{today}T10:{i:02d}:00")
            )
        test_db.commit()

        # 50 trades today, limit is 100, should pass
        result = rm.validate_trade("AAPL", "buy", 10, 100.0, 100000.0)

        assert result['approved'] is True

    def test_trade_count_exceeds_limit(self, test_db: sqlite3.Connection):
        """Test that trades exceeding daily limit are rejected."""
        rm = RiskManager(db_path=test_db)

        # Add 100 trades for today
        cursor = test_db.cursor()
        today = date.today().isoformat()

        for i in range(100):
            cursor.execute(
                """INSERT INTO trades (symbol, action, shares, price, total, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)""",
                ("AAPL", "buy", 10, 100.0, -1000.0, f"{today}T{i//60:02d}:{i%60:02d}:00")
            )
        test_db.commit()

        # Already at limit, next trade should fail
        result = rm.validate_trade("AAPL", "buy", 10, 100.0, 100000.0)

        assert result['approved'] is False
        assert any('trade count' in v.lower() or 'daily limit' in v.lower()
                  for v in result.get('violations', []))


@pytest.mark.unit
class TestMultipleViolations:
    """Test scenarios with multiple simultaneous violations."""

    def test_multiple_violations_all_reported(self, test_db: sqlite3.Connection):
        """Test that all violations are reported when multiple limits breached."""
        rm = RiskManager(db_path=test_db)

        # Create scenario with multiple violations:
        # - Huge position size (150% of portfolio)
        # - Would exceed concentration
        # - Would exceed exposure
        result = rm.validate_trade("AAPL", "buy", 1500, 100.0, 100000.0)

        assert result['approved'] is False
        violations = result.get('violations', [])
        assert len(violations) >= 2  # At least 2 violations


@pytest.mark.unit
class TestRiskLimitUpdates:
    """Test updating risk limits."""

    def test_update_risk_limits(self, test_db: sqlite3.Connection):
        """Test updating risk limits."""
        rm = RiskManager(db_path=test_db)

        # Update limits
        new_limits = {
            'max_position_size': 0.15,
            'max_daily_loss': -0.03,
            'max_total_exposure': 0.90,
            'max_orders_per_day': 150,
            'max_concentration': 0.30
        }

        rm.update_limits(new_limits)

        # Verify updates
        assert rm.limits['max_position_size'] == 0.15
        assert rm.limits['max_daily_loss'] == -0.03
        assert rm.limits['max_total_exposure'] == 0.90
        assert rm.limits['max_orders_per_day'] == 150
        assert rm.limits['max_concentration'] == 0.30

        # Verify persistence
        rm2 = RiskManager(db_path=test_db)
        assert rm2.limits['max_position_size'] == 0.15

    def test_update_partial_limits(self, test_db: sqlite3.Connection):
        """Test updating only some limits."""
        rm = RiskManager(db_path=test_db)

        original_exposure = rm.limits['max_total_exposure']

        # Update only position size
        rm.update_limits({'max_position_size': 0.20})

        assert rm.limits['max_position_size'] == 0.20
        assert rm.limits['max_total_exposure'] == original_exposure


@pytest.mark.unit
class TestAuditLogging:
    """Test audit logging functionality."""

    def test_audit_log_on_rejection(self, test_db: sqlite3.Connection):
        """Test that rejections are logged to audit log."""
        rm = RiskManager(db_path=test_db)

        # Trigger violation
        rm.validate_trade("AAPL", "buy", 1500, 100.0, 100000.0)

        # Check audit log
        cursor = test_db.cursor()
        logs = cursor.execute(
            "SELECT * FROM audit_log WHERE event_type LIKE '%REJECT%' ORDER BY id DESC LIMIT 1"
        ).fetchone()

        assert logs is not None
        assert 'AAPL' in str(logs)

    def test_audit_log_on_approval(self, test_db: sqlite3.Connection):
        """Test that approvals are logged to audit log."""
        rm = RiskManager(db_path=test_db)

        # Valid trade
        rm.validate_trade("AAPL", "buy", 10, 100.0, 100000.0)

        # Check audit log
        cursor = test_db.cursor()
        logs = cursor.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT 1"
        ).fetchone()

        assert logs is not None


@pytest.mark.unit
class TestGetRiskStatus:
    """Test risk status reporting."""

    def test_get_risk_status(self, test_db: sqlite3.Connection, test_portfolio):
        """Test getting current risk status."""
        rm = RiskManager(db_path=test_db)

        status = rm.get_risk_status(100000.0)

        assert 'limits' in status
        assert 'current_exposure' in status
        assert 'daily_trades_count' in status
        assert 'warnings' in status

    def test_risk_status_includes_warnings(self, test_db: sqlite3.Connection):
        """Test that risk status includes warnings when approaching limits."""
        rm = RiskManager(db_path=test_db)

        # Add many trades to approach daily limit
        cursor = test_db.cursor()
        today = date.today().isoformat()

        for i in range(90):  # Approach 100 limit
            cursor.execute(
                """INSERT INTO trades (symbol, action, shares, price, total, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)""",
                ("AAPL", "buy", 10, 100.0, -1000.0, f"{today}T10:{i:02d}:00")
            )
        test_db.commit()

        status = rm.get_risk_status(100000.0)

        # Should have warning about approaching trade limit
        assert len(status.get('warnings', [])) > 0


@pytest.mark.unit
class TestDailyPnLCalculation:
    """Test daily P&L calculation."""

    def test_calculate_daily_pnl(self, test_db: sqlite3.Connection):
        """Test calculating daily P&L from trades."""
        rm = RiskManager(db_path=test_db)

        # Add trades for today
        cursor = test_db.cursor()
        today = date.today().isoformat()

        trades = [
            ("AAPL", "buy", 10, 100.0, -1000.0),
            ("AAPL", "sell", 10, 105.0, 1050.0),  # +$50 profit
            ("GOOGL", "buy", 5, 100.0, -500.0),
            ("GOOGL", "sell", 5, 98.0, 490.0),    # -$10 loss
        ]

        for symbol, action, shares, price, total in trades:
            cursor.execute(
                """INSERT INTO trades (symbol, action, shares, price, total, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (symbol, action, shares, price, total, f"{today}T10:00:00")
            )
        test_db.commit()

        # Calculate daily P&L
        pnl = rm._calculate_daily_pnl()

        # Net P&L should be +$40 (50 - 10)
        # But we stored totals as negative for buys
        # So actual calculation: 1050 + (-1000) + 490 + (-500) = 40
        assert pnl == pytest.approx(40.0, abs=0.01)

    def test_daily_pnl_empty_day(self, test_db: sqlite3.Connection):
        """Test daily P&L calculation with no trades today."""
        rm = RiskManager(db_path=test_db)

        pnl = rm._calculate_daily_pnl()

        assert pnl == 0.0
