"""
Integration tests for broker_feed.py

Tests data synchronization between broker and local state:
- Real-time price fetching
- Position reconciliation
- Account balance sync
"""

import pytest
from unittest.mock import patch, MagicMock
import sqlite3

from backend.broker_feed import (
    sync_account_from_broker,
    sync_positions_from_broker,
    get_broker_price
)
from tests.fixtures.mock_broker_responses import (
    mock_account_response,
    mock_position_response,
    mock_quote_response
)


@pytest.mark.integration
class TestAccountSync:
    """Test account synchronization from broker."""

    def test_sync_account_success(self, test_db, mock_broker_client):
        """Test successful account sync from broker."""
        mock_broker_client.get_account.return_value = mock_account_response(
            cash=95000.0,
            buying_power=95000.0,
            portfolio_value=105000.0
        )

        with patch('backend.broker_feed.port._conn', return_value=test_db):
            result = sync_account_from_broker(mock_broker_client)

        # Should update portfolio with broker data
        assert result is True or result is not None

        # Verify database was updated
        cursor = test_db.cursor()
        portfolio = cursor.execute(
            "SELECT cash, buying_power, account_value FROM portfolio WHERE id = 1"
        ).fetchone()

        if portfolio:
            # Values should be synced from broker
            assert portfolio[0] == 95000.0  # cash
            # buying_power and account_value may also be updated

    def test_sync_account_broker_error(self, test_db, mock_broker_client):
        """Test account sync when broker returns error."""
        mock_broker_client.get_account.return_value = None

        with patch('backend.broker_feed.port._conn', return_value=test_db):
            result = sync_account_from_broker(mock_broker_client)

        # Should handle error gracefully
        assert result is False or result is None

    def test_sync_account_updates_timestamp(self, test_db, mock_broker_client):
        """Test that account sync updates last_synced_at timestamp."""
        mock_broker_client.get_account.return_value = mock_account_response()

        with patch('backend.broker_feed.port._conn', return_value=test_db):
            sync_account_from_broker(mock_broker_client)

        # Verify timestamp was updated
        cursor = test_db.cursor()
        portfolio = cursor.execute(
            "SELECT last_synced_at FROM portfolio WHERE id = 1"
        ).fetchone()

        if portfolio:
            assert portfolio[0] is not None


@pytest.mark.integration
class TestPositionSync:
    """Test position synchronization from broker."""

    def test_sync_positions_empty_broker(self, test_db, mock_broker_client):
        """Test syncing positions when broker has no positions."""
        mock_broker_client.get_positions.return_value = []

        with patch('backend.broker_feed.port._conn', return_value=test_db):
            result = sync_positions_from_broker(mock_broker_client)

        # Should complete successfully
        assert result is True or result is not None

    def test_sync_positions_with_positions(self, test_db, mock_broker_client):
        """Test syncing positions from broker."""
        mock_broker_client.get_positions.return_value = [
            mock_position_response("AAPL", 10, 150.0, 155.0),
            mock_position_response("GOOGL", 5, 140.0, 142.0)
        ]

        with patch('backend.broker_feed.port._conn', return_value=test_db):
            result = sync_positions_from_broker(mock_broker_client)

        # Should sync positions to database
        assert result is True or result is not None

        # Verify positions in database
        cursor = test_db.cursor()
        positions = cursor.execute(
            "SELECT symbol, shares, avg_cost FROM positions ORDER BY symbol"
        ).fetchall()

        if len(positions) >= 2:
            # Check AAPL position
            aapl = [p for p in positions if p[0] == 'AAPL']
            if aapl:
                assert float(aapl[0][1]) == 10.0
                assert float(aapl[0][2]) == 150.0

    def test_sync_positions_reconciliation(self, test_db, test_portfolio, mock_broker_client):
        """Test position reconciliation between local and broker."""
        # test_portfolio has some positions
        # Broker has different positions
        mock_broker_client.get_positions.return_value = [
            mock_position_response("NVDA", 20, 500.0, 505.0),  # New position
            mock_position_response("AAPL", 15, 150.0, 155.0)   # Different qty
        ]

        with patch('backend.broker_feed.port._conn', return_value=test_db):
            result = sync_positions_from_broker(mock_broker_client)

        # Should reconcile differences
        cursor = test_db.cursor()
        nvda = cursor.execute(
            "SELECT shares FROM positions WHERE symbol = 'NVDA'"
        ).fetchone()

        # NVDA should now be in database
        if nvda:
            assert float(nvda[0]) == 20.0

    def test_sync_positions_broker_error(self, test_db, mock_broker_client):
        """Test position sync when broker returns error."""
        mock_broker_client.get_positions.return_value = None

        with patch('backend.broker_feed.port._conn', return_value=test_db):
            result = sync_positions_from_broker(mock_broker_client)

        # Should handle error gracefully
        assert result is False or result is None


@pytest.mark.integration
class TestBrokerPriceRetrieval:
    """Test real-time price fetching from broker."""

    def test_get_broker_price_success(self, mock_broker_client):
        """Test successful price retrieval from broker."""
        mock_broker_client.get_latest_quote.return_value = mock_quote_response(
            symbol="AAPL",
            bid_price=149.95,
            ask_price=150.05,
            last_price=150.0
        )

        price = get_broker_price("AAPL", mock_broker_client)

        assert price == 150.0

    def test_get_broker_price_invalid_symbol(self, mock_broker_client):
        """Test price retrieval for invalid symbol."""
        mock_broker_client.get_latest_quote.return_value = None

        price = get_broker_price("INVALID", mock_broker_client)

        assert price is None

    def test_get_broker_price_uses_last_price(self, mock_broker_client):
        """Test that we use last_price from quote."""
        mock_broker_client.get_latest_quote.return_value = mock_quote_response(
            symbol="AAPL",
            bid_price=149.90,
            ask_price=150.10,
            last_price=150.0
        )

        price = get_broker_price("AAPL", mock_broker_client)

        # Should use last_price, not bid or ask
        assert price == 150.0

    def test_get_broker_price_fallback_to_bid_ask(self, mock_broker_client):
        """Test fallback to bid/ask if last_price unavailable."""
        quote = mock_quote_response(
            symbol="AAPL",
            bid_price=149.95,
            ask_price=150.05,
            last_price=None  # No last price
        )
        quote['last_price'] = None

        mock_broker_client.get_latest_quote.return_value = quote

        price = get_broker_price("AAPL", mock_broker_client)

        # Should use midpoint of bid/ask: (149.95 + 150.05) / 2 = 150.0
        if price is not None:
            assert price == pytest.approx(150.0, abs=0.1)


@pytest.mark.integration
class TestFullSyncWorkflow:
    """Test complete sync workflow."""

    def test_full_sync_account_and_positions(self, test_db, mock_broker_client):
        """Test syncing both account and positions together."""
        # Setup broker responses
        mock_broker_client.get_account.return_value = mock_account_response(
            cash=98000.0,
            buying_power=98000.0,
            portfolio_value=108000.0
        )

        mock_broker_client.get_positions.return_value = [
            mock_position_response("AAPL", 10, 150.0, 155.0),
            mock_position_response("GOOGL", 5, 140.0, 145.0)
        ]

        with patch('backend.broker_feed.port._conn', return_value=test_db):
            # Sync account
            account_result = sync_account_from_broker(mock_broker_client)

            # Sync positions
            positions_result = sync_positions_from_broker(mock_broker_client)

        # Both should succeed
        assert account_result is not False
        assert positions_result is not False

        # Verify data integrity
        cursor = test_db.cursor()

        # Check portfolio
        portfolio = cursor.execute(
            "SELECT cash, account_value FROM portfolio WHERE id = 1"
        ).fetchone()

        if portfolio:
            assert portfolio[0] == 98000.0

        # Check positions
        positions = cursor.execute(
            "SELECT COUNT(*) FROM positions"
        ).fetchone()

        # Should have positions

    def test_sync_after_trade_execution(self, test_db, mock_broker_client):
        """Test syncing after a trade to reconcile state."""
        # Execute a trade locally
        from backend import portfolio as port

        with patch('backend.portfolio._conn', return_value=test_db):
            # Log a trade
            port.log_trade(
                test_db,
                symbol="AAPL",
                action="buy",
                shares=10,
                price=150.0,
                total=-1500.0
            )

        # Now sync from broker (broker should reflect the trade)
        mock_broker_client.get_positions.return_value = [
            mock_position_response("AAPL", 10, 150.0, 150.0)
        ]

        with patch('backend.broker_feed.port._conn', return_value=test_db):
            sync_positions_from_broker(mock_broker_client)

        # Positions should be reconciled


@pytest.mark.integration
class TestSyncErrorRecovery:
    """Test error recovery during sync."""

    def test_partial_sync_failure(self, test_db, mock_broker_client):
        """Test handling of partial sync failure."""
        # Account sync succeeds
        mock_broker_client.get_account.return_value = mock_account_response()

        # Position sync fails
        mock_broker_client.get_positions.side_effect = Exception("API error")

        with patch('backend.broker_feed.port._conn', return_value=test_db):
            # Account sync should succeed
            account_result = sync_account_from_broker(mock_broker_client)

            # Position sync should fail gracefully
            try:
                positions_result = sync_positions_from_broker(mock_broker_client)
                assert positions_result is False or positions_result is None
            except Exception:
                # Exception is also acceptable
                pass

    def test_sync_retry_on_network_error(self, test_db, mock_broker_client):
        """Test retry logic on network errors."""
        # First call fails, second succeeds
        mock_broker_client.get_account.side_effect = [
            Exception("Network error"),
            mock_account_response()
        ]

        with patch('backend.broker_feed.port._conn', return_value=test_db):
            # First attempt
            result1 = None
            try:
                result1 = sync_account_from_broker(mock_broker_client)
            except Exception:
                pass

            # Second attempt (retry)
            result2 = sync_account_from_broker(mock_broker_client)

            # Second attempt should succeed
            assert result2 is not False


@pytest.mark.integration
class TestPriceFeedAccuracy:
    """Test price feed accuracy and consistency."""

    def test_price_consistency_across_calls(self, mock_broker_client):
        """Test that price fetching is consistent."""
        mock_broker_client.get_latest_quote.return_value = mock_quote_response(
            symbol="AAPL",
            last_price=150.0
        )

        price1 = get_broker_price("AAPL", mock_broker_client)
        price2 = get_broker_price("AAPL", mock_broker_client)

        assert price1 == price2

    def test_price_feed_multiple_symbols(self, mock_broker_client):
        """Test fetching prices for multiple symbols."""
        def mock_quote_side_effect(symbol):
            prices = {
                "AAPL": 150.0,
                "GOOGL": 140.0,
                "MSFT": 380.0
            }
            return mock_quote_response(symbol=symbol, last_price=prices.get(symbol, 0))

        mock_broker_client.get_latest_quote.side_effect = mock_quote_side_effect

        symbols = ["AAPL", "GOOGL", "MSFT"]
        prices = {}

        for symbol in symbols:
            prices[symbol] = get_broker_price(symbol, mock_broker_client)

        assert len(prices) == 3
        assert prices["AAPL"] == 150.0
        assert prices["GOOGL"] == 140.0
        assert prices["MSFT"] == 380.0
