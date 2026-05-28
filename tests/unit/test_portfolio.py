"""
Unit tests for portfolio.py

Tests database operations for:
- Portfolio state management
- Position tracking
- Trade logging
- Order management
- Signal tracking
"""

import pytest
import sqlite3
from datetime import datetime, timedelta

from backend import portfolio


@pytest.mark.unit
class TestPortfolioOperations:
    """Test portfolio state management."""

    def test_get_portfolio_initial_state(self, test_db: sqlite3.Connection):
        """Test getting initial portfolio state."""
        port = portfolio.get_portfolio(test_db)

        assert port is not None
        assert port['cash'] == 100000.0
        assert port['buying_power'] == 100000.0
        assert port['account_value'] == 100000.0

    def test_update_portfolio_cash(self, test_db: sqlite3.Connection):
        """Test updating portfolio cash."""
        portfolio.update_portfolio_cash(test_db, 95000.0)

        port = portfolio.get_portfolio(test_db)
        assert port['cash'] == 95000.0

    def test_update_portfolio_buying_power(self, test_db: sqlite3.Connection):
        """Test updating buying power."""
        portfolio.update_portfolio(
            test_db,
            cash=100000.0,
            buying_power=120000.0,
            account_value=100000.0
        )

        port = portfolio.get_portfolio(test_db)
        assert port['buying_power'] == 120000.0

    def test_sync_broker_account(self, test_db: sqlite3.Connection):
        """Test syncing broker account data."""
        broker_data = {
            'cash': 98000.0,
            'buying_power': 98000.0,
            'portfolio_value': 105000.0
        }

        portfolio.sync_broker_account(test_db, broker_data)

        port = portfolio.get_portfolio(test_db)
        assert port['cash'] == 98000.0
        assert port['account_value'] == 105000.0
        assert port['last_synced_at'] is not None


@pytest.mark.unit
class TestPositionOperations:
    """Test position tracking."""

    def test_add_position(self, test_db: sqlite3.Connection):
        """Test adding a new position."""
        portfolio.add_position(test_db, "NVDA", 10, 500.0)

        pos = portfolio.get_position(test_db, "NVDA")
        assert pos is not None
        assert pos['symbol'] == "NVDA"
        assert pos['shares'] == 10
        assert pos['avg_cost'] == 500.0

    def test_update_existing_position(self, test_db: sqlite3.Connection, test_portfolio):
        """Test updating an existing position (accumulation)."""
        # test_portfolio has AAPL: 10 shares @ $150
        # Add 5 more shares @ $160
        portfolio.update_position(test_db, "AAPL", 15, 153.33)

        pos = portfolio.get_position(test_db, "AAPL")
        assert pos['shares'] == 15
        assert pos['avg_cost'] == pytest.approx(153.33, abs=0.01)

    def test_reduce_position(self, test_db: sqlite3.Connection, test_portfolio):
        """Test reducing a position."""
        # test_portfolio has AAPL: 10 shares @ $150
        # Sell 5 shares
        portfolio.update_position(test_db, "AAPL", 5, 150.0)

        pos = portfolio.get_position(test_db, "AAPL")
        assert pos['shares'] == 5
        assert pos['avg_cost'] == 150.0

    def test_close_position(self, test_db: sqlite3.Connection, test_portfolio):
        """Test closing a position completely."""
        # Sell all AAPL shares
        portfolio.remove_position(test_db, "AAPL")

        pos = portfolio.get_position(test_db, "AAPL")
        assert pos is None

    def test_get_all_positions(self, test_db: sqlite3.Connection, test_portfolio):
        """Test getting all positions."""
        positions = portfolio.get_all_positions(test_db)

        assert len(positions) == 3
        symbols = [p['symbol'] for p in positions]
        assert 'AAPL' in symbols
        assert 'GOOGL' in symbols
        assert 'MSFT' in symbols

    def test_get_nonexistent_position(self, test_db: sqlite3.Connection):
        """Test getting a position that doesn't exist."""
        pos = portfolio.get_position(test_db, "NONEXISTENT")
        assert pos is None

    def test_position_accumulation_bug_fix(self, test_db: sqlite3.Connection):
        """
        Test the critical bug fix from commit d780722.

        Verify that buying the same stock twice accumulates shares
        rather than overwriting the position.
        """
        # First purchase
        portfolio.add_position(test_db, "AAPL", 10, 150.0)

        # Second purchase - should accumulate
        current_pos = portfolio.get_position(test_db, "AAPL")
        new_shares = current_pos['shares'] + 5
        new_avg_cost = ((current_pos['shares'] * current_pos['avg_cost']) +
                       (5 * 155.0)) / new_shares

        portfolio.update_position(test_db, "AAPL", new_shares, new_avg_cost)

        pos = portfolio.get_position(test_db, "AAPL")
        assert pos['shares'] == 15  # Not 5!
        assert pos['avg_cost'] == pytest.approx(151.67, abs=0.01)


@pytest.mark.unit
class TestTradeLogging:
    """Test trade history logging."""

    def test_log_trade(self, test_db: sqlite3.Connection):
        """Test logging a trade."""
        trade_id = portfolio.log_trade(
            test_db,
            symbol="AAPL",
            action="buy",
            shares=10,
            price=150.0,
            total=-1500.0,
            reason="Test purchase"
        )

        assert trade_id is not None
        assert trade_id > 0

    def test_log_trade_with_order_id(self, test_db: sqlite3.Connection):
        """Test logging a trade with broker order ID."""
        trade_id = portfolio.log_trade(
            test_db,
            symbol="AAPL",
            action="buy",
            shares=10,
            price=150.0,
            total=-1500.0,
            order_id=12345,
            strategy_name="RSI Strategy"
        )

        # Retrieve and verify
        cursor = test_db.cursor()
        trade = cursor.execute(
            "SELECT * FROM trades WHERE id = ?", (trade_id,)
        ).fetchone()

        assert trade['order_id'] == 12345
        assert trade['strategy_name'] == "RSI Strategy"

    def test_get_trade_history(self, test_db: sqlite3.Connection, test_portfolio):
        """Test retrieving trade history."""
        trades = portfolio.get_trade_history(test_db, limit=10)

        assert len(trades) >= 3  # From test_portfolio
        assert all('symbol' in t for t in trades)
        assert all('action' in t for t in trades)

    def test_get_trade_history_with_limit(self, test_db: sqlite3.Connection, test_portfolio):
        """Test trade history with limit."""
        # Add more trades
        for i in range(10):
            portfolio.log_trade(
                test_db,
                symbol="TEST",
                action="buy",
                shares=1,
                price=100.0,
                total=-100.0
            )

        trades = portfolio.get_trade_history(test_db, limit=5)
        assert len(trades) == 5

    def test_get_trades_by_symbol(self, test_db: sqlite3.Connection, test_portfolio):
        """Test getting trades for specific symbol."""
        cursor = test_db.cursor()
        trades = cursor.execute(
            "SELECT * FROM trades WHERE symbol = ? ORDER BY timestamp DESC",
            ("AAPL",)
        ).fetchall()

        assert len(trades) >= 1
        assert all(t['symbol'] == "AAPL" for t in trades)


@pytest.mark.unit
class TestOrderManagement:
    """Test order tracking."""

    def test_create_order(self, test_db: sqlite3.Connection):
        """Test creating an order record."""
        order_id = portfolio.create_order(
            test_db,
            broker_order_id="broker-123",
            symbol="AAPL",
            side="buy",
            order_type="market",
            quantity=10,
            status="submitted"
        )

        assert order_id is not None

    def test_update_order_status(self, test_db: sqlite3.Connection):
        """Test updating order status."""
        order_id = portfolio.create_order(
            test_db,
            broker_order_id="broker-123",
            symbol="AAPL",
            side="buy",
            order_type="market",
            quantity=10,
            status="submitted"
        )

        # Update to filled
        portfolio.update_order_status(
            test_db,
            order_id=order_id,
            status="filled",
            filled_qty=10,
            avg_fill_price=150.0
        )

        cursor = test_db.cursor()
        order = cursor.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        ).fetchone()

        assert order['status'] == "filled"
        assert order['filled_qty'] == 10
        assert order['avg_fill_price'] == 150.0
        assert order['filled_at'] is not None

    def test_get_order_by_broker_id(self, test_db: sqlite3.Connection):
        """Test retrieving order by broker ID."""
        portfolio.create_order(
            test_db,
            broker_order_id="unique-broker-id",
            symbol="AAPL",
            side="buy",
            order_type="market",
            quantity=10,
            status="submitted"
        )

        order = portfolio.get_order_by_broker_id(test_db, "unique-broker-id")

        assert order is not None
        assert order['broker_order_id'] == "unique-broker-id"

    def test_get_pending_orders(self, test_db: sqlite3.Connection):
        """Test getting all pending orders."""
        # Create mix of orders
        portfolio.create_order(
            test_db, "order-1", "AAPL", "buy", "market", 10, status="submitted"
        )
        portfolio.create_order(
            test_db, "order-2", "GOOGL", "buy", "limit", 5, status="submitted"
        )
        portfolio.create_order(
            test_db, "order-3", "MSFT", "sell", "market", 8, status="filled"
        )

        pending = portfolio.get_pending_orders(test_db)

        assert len(pending) == 2
        assert all(o['status'] == 'submitted' for o in pending)

    def test_cancel_order(self, test_db: sqlite3.Connection):
        """Test canceling an order."""
        order_id = portfolio.create_order(
            test_db, "order-cancel", "AAPL", "buy", "limit", 10, status="submitted"
        )

        portfolio.cancel_order(test_db, order_id)

        cursor = test_db.cursor()
        order = cursor.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        ).fetchone()

        assert order['status'] == "canceled"
        assert order['canceled_at'] is not None


@pytest.mark.unit
class TestSignalTracking:
    """Test TradingView signal tracking."""

    def test_log_signal(self, test_db: sqlite3.Connection, sample_buy_signal):
        """Test logging a TradingView signal."""
        signal_id = portfolio.log_tradingview_signal(
            test_db,
            symbol=sample_buy_signal['ticker'],
            action=sample_buy_signal['action'],
            strategy=sample_buy_signal.get('strategy'),
            price=sample_buy_signal.get('price'),
            quantity=sample_buy_signal.get('quantity'),
            raw_payload=str(sample_buy_signal),
            status="pending"
        )

        assert signal_id is not None

    def test_update_signal_status(self, test_db: sqlite3.Connection, sample_buy_signal):
        """Test updating signal processing status."""
        signal_id = portfolio.log_tradingview_signal(
            test_db,
            symbol=sample_buy_signal['ticker'],
            action=sample_buy_signal['action'],
            status="pending"
        )

        # Mark as processed
        portfolio.update_signal_status(
            test_db,
            signal_id=signal_id,
            status="processed",
            order_id=123
        )

        cursor = test_db.cursor()
        signal = cursor.execute(
            "SELECT * FROM tradingview_signals WHERE id = ?", (signal_id,)
        ).fetchone()

        assert signal['status'] == "processed"
        assert signal['order_id'] == 123
        assert signal['processed_at'] is not None

    def test_reject_signal(self, test_db: sqlite3.Connection, sample_buy_signal):
        """Test rejecting a signal."""
        signal_id = portfolio.log_tradingview_signal(
            test_db,
            symbol=sample_buy_signal['ticker'],
            action=sample_buy_signal['action'],
            status="pending"
        )

        portfolio.reject_signal(
            test_db,
            signal_id=signal_id,
            reason="Risk limits exceeded"
        )

        cursor = test_db.cursor()
        signal = cursor.execute(
            "SELECT * FROM tradingview_signals WHERE id = ?", (signal_id,)
        ).fetchone()

        assert signal['status'] == "rejected"
        assert signal['rejection_reason'] == "Risk limits exceeded"

    def test_get_recent_signals(self, test_db: sqlite3.Connection):
        """Test retrieving recent signals."""
        # Create multiple signals
        for i in range(5):
            portfolio.log_tradingview_signal(
                test_db,
                symbol="TEST",
                action="buy",
                status="processed"
            )

        signals = portfolio.get_recent_signals(test_db, limit=3)

        assert len(signals) == 3


@pytest.mark.unit
class TestAuditLog:
    """Test audit logging."""

    def test_log_audit_event(self, test_db: sqlite3.Connection):
        """Test logging an audit event."""
        portfolio.log_audit(
            test_db,
            event_type="TRADE_EXECUTED",
            symbol="AAPL",
            data={"shares": 10, "price": 150.0},
            message="Bought 10 shares of AAPL"
        )

        cursor = test_db.cursor()
        audit = cursor.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT 1"
        ).fetchone()

        assert audit is not None
        assert audit['event_type'] == "TRADE_EXECUTED"
        assert audit['symbol'] == "AAPL"

    def test_get_audit_log(self, test_db: sqlite3.Connection):
        """Test retrieving audit log."""
        # Create multiple audit entries
        for i in range(10):
            portfolio.log_audit(
                test_db,
                event_type="TEST_EVENT",
                message=f"Test message {i}"
            )

        log = portfolio.get_audit_log(test_db, limit=5)

        assert len(log) == 5


@pytest.mark.unit
class TestDailyMetrics:
    """Test daily performance metrics."""

    def test_record_daily_metrics(self, test_db: sqlite3.Connection):
        """Test recording daily metrics."""
        from datetime import date

        portfolio.record_daily_metrics(
            test_db,
            date=date.today().isoformat(),
            starting_value=100000.0,
            ending_value=101000.0,
            daily_pnl=1000.0,
            daily_return_pct=1.0,
            trades_count=5,
            winners_count=3,
            losers_count=2
        )

        cursor = test_db.cursor()
        metrics = cursor.execute(
            "SELECT * FROM daily_metrics WHERE date = ?",
            (date.today().isoformat(),)
        ).fetchone()

        assert metrics is not None
        assert metrics['daily_pnl'] == 1000.0
        assert metrics['daily_return_pct'] == 1.0
        assert metrics['trades_count'] == 5

    def test_get_daily_metrics(self, test_db: sqlite3.Connection):
        """Test retrieving daily metrics."""
        from datetime import date

        # Record metrics for today
        portfolio.record_daily_metrics(
            test_db,
            date=date.today().isoformat(),
            starting_value=100000.0,
            ending_value=101000.0,
            daily_pnl=1000.0,
            daily_return_pct=1.0
        )

        metrics = portfolio.get_daily_metrics(test_db, date.today().isoformat())

        assert metrics is not None
        assert metrics['daily_pnl'] == 1000.0


@pytest.mark.unit
class TestTransactionRollback:
    """Test database transaction rollback on errors."""

    def test_rollback_on_error(self, test_db: sqlite3.Connection):
        """Test that transactions rollback on errors."""
        initial_cash = portfolio.get_portfolio(test_db)['cash']

        try:
            cursor = test_db.cursor()
            cursor.execute(
                "UPDATE portfolio SET cash = ? WHERE id = 1", (50000.0,)
            )
            # Simulate error before commit
            raise Exception("Simulated error")
        except Exception:
            test_db.rollback()

        # Cash should be unchanged
        current_cash = portfolio.get_portfolio(test_db)['cash']
        assert current_cash == initial_cash
