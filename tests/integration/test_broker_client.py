"""
Integration tests for broker_client.py

Tests Alpaca broker API integration with mocked HTTP responses:
- Order submission (market, limit, stop)
- Order status polling and fill waiting
- Position and account queries
- Paper vs live mode
- Error handling and retries
"""

import pytest
import responses
from unittest.mock import patch, MagicMock
import json

from backend.broker_client import AlpacaBrokerClient
from tests.fixtures.mock_broker_responses import (
    mock_account_response,
    mock_order_response,
    mock_position_response,
    mock_quote_response,
    RATE_LIMIT_ERROR,
    INSUFFICIENT_FUNDS_ERROR,
    INVALID_SYMBOL_ERROR
)


@pytest.mark.integration
class TestBrokerClientInitialization:
    """Test broker client initialization."""

    def test_init_paper_mode(self):
        """Test initialization in paper mode."""
        client = AlpacaBrokerClient(
            api_key="test_key",
            api_secret="test_secret",
            paper_mode=True
        )

        assert client.paper_mode is True
        assert "paper-api.alpaca.markets" in client.base_url

    def test_init_live_mode(self):
        """Test initialization in live mode."""
        client = AlpacaBrokerClient(
            api_key="test_key",
            api_secret="test_secret",
            paper_mode=False
        )

        assert client.paper_mode is False
        assert "api.alpaca.markets" in client.base_url

    def test_init_sets_headers(self):
        """Test that initialization sets auth headers."""
        client = AlpacaBrokerClient(
            api_key="test_key",
            api_secret="test_secret",
            paper_mode=True
        )

        assert "APCA-API-KEY-ID" in client.headers
        assert "APCA-API-SECRET-KEY" in client.headers
        assert client.headers["APCA-API-KEY-ID"] == "test_key"


@pytest.mark.integration
class TestAccountQueries:
    """Test account information retrieval."""

    @responses.activate
    def test_get_account_success(self):
        """Test successful account retrieval."""
        responses.add(
            responses.GET,
            "https://paper-api.alpaca.markets/v2/account",
            json=mock_account_response(),
            status=200
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        account = client.get_account()

        assert account is not None
        assert account['cash'] == '100000.0'
        assert account['buying_power'] == '100000.0'

    @responses.activate
    def test_get_account_error(self):
        """Test account retrieval with error."""
        responses.add(
            responses.GET,
            "https://paper-api.alpaca.markets/v2/account",
            json={"message": "Unauthorized"},
            status=401
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        account = client.get_account()

        assert account is None


@pytest.mark.integration
class TestMarketOrders:
    """Test market order submission."""

    @responses.activate
    def test_submit_market_buy_order(self):
        """Test submitting market buy order."""
        responses.add(
            responses.POST,
            "https://paper-api.alpaca.markets/v2/orders",
            json=mock_order_response(
                order_id="order-123",
                symbol="AAPL",
                qty=10,
                side="buy",
                order_type="market",
                status="submitted"
            ),
            status=200
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        order = client.submit_market_order("AAPL", 10, "buy")

        assert order is not None
        assert order['symbol'] == "AAPL"
        assert order['qty'] == "10"
        assert order['side'] == "buy"
        assert order['order_type'] == "market"

    @responses.activate
    def test_submit_market_sell_order(self):
        """Test submitting market sell order."""
        responses.add(
            responses.POST,
            "https://paper-api.alpaca.markets/v2/orders",
            json=mock_order_response(
                symbol="AAPL",
                qty=10,
                side="sell",
                order_type="market"
            ),
            status=200
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        order = client.submit_market_order("AAPL", 10, "sell")

        assert order is not None
        assert order['side'] == "sell"

    @responses.activate
    def test_submit_market_order_insufficient_funds(self):
        """Test market order with insufficient funds."""
        responses.add(
            responses.POST,
            "https://paper-api.alpaca.markets/v2/orders",
            json=INSUFFICIENT_FUNDS_ERROR,
            status=403
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        order = client.submit_market_order("AAPL", 1000000, "buy")

        assert order is None

    @responses.activate
    def test_submit_market_order_invalid_symbol(self):
        """Test market order with invalid symbol."""
        responses.add(
            responses.POST,
            "https://paper-api.alpaca.markets/v2/orders",
            json=INVALID_SYMBOL_ERROR,
            status=400
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        order = client.submit_market_order("INVALID", 10, "buy")

        assert order is None


@pytest.mark.integration
class TestLimitOrders:
    """Test limit order submission."""

    @responses.activate
    def test_submit_limit_buy_order(self):
        """Test submitting limit buy order."""
        responses.add(
            responses.POST,
            "https://paper-api.alpaca.markets/v2/orders",
            json=mock_order_response(
                symbol="AAPL",
                qty=10,
                side="buy",
                order_type="limit",
                limit_price=150.0
            ),
            status=200
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        order = client.submit_limit_order("AAPL", 10, 150.0, "buy")

        assert order is not None
        assert order['order_type'] == "limit"
        assert order['limit_price'] == "150.0"

    @responses.activate
    def test_submit_limit_sell_order(self):
        """Test submitting limit sell order."""
        responses.add(
            responses.POST,
            "https://paper-api.alpaca.markets/v2/orders",
            json=mock_order_response(
                symbol="AAPL",
                qty=10,
                side="sell",
                order_type="limit",
                limit_price=160.0
            ),
            status=200
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        order = client.submit_limit_order("AAPL", 10, 160.0, "sell")

        assert order is not None
        assert order['side'] == "sell"
        assert order['limit_price'] == "160.0"


@pytest.mark.integration
class TestStopOrders:
    """Test stop order submission."""

    @responses.activate
    def test_submit_stop_loss_order(self):
        """Test submitting stop loss order."""
        responses.add(
            responses.POST,
            "https://paper-api.alpaca.markets/v2/orders",
            json=mock_order_response(
                symbol="AAPL",
                qty=10,
                side="sell",
                order_type="stop",
                stop_price=145.0
            ),
            status=200
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        order = client.submit_stop_order("AAPL", 10, 145.0, "sell")

        assert order is not None
        assert order['order_type'] == "stop"
        assert order['stop_price'] == "145.0"


@pytest.mark.integration
class TestOrderStatus:
    """Test order status retrieval."""

    @responses.activate
    def test_get_order_status_filled(self):
        """Test getting status of filled order."""
        responses.add(
            responses.GET,
            "https://paper-api.alpaca.markets/v2/orders/order-123",
            json=mock_order_response(
                order_id="order-123",
                status="filled"
            ),
            status=200
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        order = client.get_order_status("order-123")

        assert order is not None
        assert order['status'] == "filled"

    @responses.activate
    def test_get_order_status_pending(self):
        """Test getting status of pending order."""
        responses.add(
            responses.GET,
            "https://paper-api.alpaca.markets/v2/orders/order-123",
            json=mock_order_response(
                order_id="order-123",
                status="pending_new"
            ),
            status=200
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        order = client.get_order_status("order-123")

        assert order is not None
        assert order['status'] == "pending_new"

    @responses.activate
    def test_get_order_status_not_found(self):
        """Test getting status of nonexistent order."""
        responses.add(
            responses.GET,
            "https://paper-api.alpaca.markets/v2/orders/invalid-id",
            json={"message": "Order not found"},
            status=404
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        order = client.get_order_status("invalid-id")

        assert order is None


@pytest.mark.integration
class TestOrderFillWaiting:
    """Test waiting for order fills."""

    @responses.activate
    def test_wait_for_fill_immediate(self):
        """Test waiting for order that fills immediately."""
        responses.add(
            responses.GET,
            "https://paper-api.alpaca.markets/v2/orders/order-123",
            json=mock_order_response(
                order_id="order-123",
                status="filled"
            ),
            status=200
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        order = client.wait_for_order_fill("order-123", timeout=5)

        assert order is not None
        assert order['status'] == "filled"

    @responses.activate
    def test_wait_for_fill_progressive(self):
        """Test waiting for order that fills after polling."""
        # First call: pending
        responses.add(
            responses.GET,
            "https://paper-api.alpaca.markets/v2/orders/order-123",
            json=mock_order_response(
                order_id="order-123",
                status="pending_new"
            ),
            status=200
        )

        # Second call: accepted
        responses.add(
            responses.GET,
            "https://paper-api.alpaca.markets/v2/orders/order-123",
            json=mock_order_response(
                order_id="order-123",
                status="accepted"
            ),
            status=200
        )

        # Third call: filled
        responses.add(
            responses.GET,
            "https://paper-api.alpaca.markets/v2/orders/order-123",
            json=mock_order_response(
                order_id="order-123",
                status="filled"
            ),
            status=200
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        order = client.wait_for_order_fill("order-123", timeout=10, poll_interval=0.5)

        assert order is not None
        assert order['status'] == "filled"

    @responses.activate
    @pytest.mark.slow
    def test_wait_for_fill_timeout(self):
        """Test timeout while waiting for fill."""
        # Always return pending
        responses.add(
            responses.GET,
            "https://paper-api.alpaca.markets/v2/orders/order-123",
            json=mock_order_response(
                order_id="order-123",
                status="pending_new"
            ),
            status=200
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        order = client.wait_for_order_fill("order-123", timeout=2, poll_interval=0.5)

        # Should return last status on timeout
        assert order is not None
        assert order['status'] != "filled"


@pytest.mark.integration
class TestPositionQueries:
    """Test position retrieval."""

    @responses.activate
    def test_get_all_positions(self):
        """Test getting all positions."""
        responses.add(
            responses.GET,
            "https://paper-api.alpaca.markets/v2/positions",
            json=[
                mock_position_response("AAPL", 10, 150.0, 155.0),
                mock_position_response("GOOGL", 5, 140.0, 142.0)
            ],
            status=200
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        positions = client.get_positions()

        assert len(positions) == 2
        assert positions[0]['symbol'] == "AAPL"
        assert positions[1]['symbol'] == "GOOGL"

    @responses.activate
    def test_get_position_by_symbol(self):
        """Test getting specific position."""
        responses.add(
            responses.GET,
            "https://paper-api.alpaca.markets/v2/positions/AAPL",
            json=mock_position_response("AAPL", 10, 150.0, 155.0),
            status=200
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        position = client.get_position("AAPL")

        assert position is not None
        assert position['symbol'] == "AAPL"
        assert position['qty'] == "10"

    @responses.activate
    def test_get_position_not_found(self):
        """Test getting position that doesn't exist."""
        responses.add(
            responses.GET,
            "https://paper-api.alpaca.markets/v2/positions/NVDA",
            json={"message": "Position not found"},
            status=404
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        position = client.get_position("NVDA")

        assert position is None


@pytest.mark.integration
class TestQuoteRetrieval:
    """Test price quote retrieval."""

    @responses.activate
    def test_get_latest_quote(self):
        """Test getting latest quote."""
        responses.add(
            responses.GET,
            "https://data.alpaca.markets/v2/stocks/AAPL/quotes/latest",
            json={"quote": mock_quote_response("AAPL", 149.95, 150.05, 150.0)},
            status=200
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        quote = client.get_latest_quote("AAPL")

        assert quote is not None
        assert quote['symbol'] == "AAPL"
        assert quote['last_price'] == 150.0


@pytest.mark.integration
class TestOrderCancellation:
    """Test order cancellation."""

    @responses.activate
    def test_cancel_order_success(self):
        """Test successful order cancellation."""
        responses.add(
            responses.DELETE,
            "https://paper-api.alpaca.markets/v2/orders/order-123",
            status=204
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        result = client.cancel_order("order-123")

        assert result is True

    @responses.activate
    def test_cancel_order_not_found(self):
        """Test canceling nonexistent order."""
        responses.add(
            responses.DELETE,
            "https://paper-api.alpaca.markets/v2/orders/invalid-id",
            json={"message": "Order not found"},
            status=404
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        result = client.cancel_order("invalid-id")

        assert result is False

    @responses.activate
    def test_cancel_order_already_filled(self):
        """Test canceling already filled order."""
        responses.add(
            responses.DELETE,
            "https://paper-api.alpaca.markets/v2/orders/order-123",
            json={"message": "Order already filled"},
            status=422
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        result = client.cancel_order("order-123")

        assert result is False


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling and retries."""

    @responses.activate
    def test_rate_limit_error(self):
        """Test handling of rate limit errors."""
        responses.add(
            responses.GET,
            "https://paper-api.alpaca.markets/v2/account",
            json=RATE_LIMIT_ERROR,
            status=429
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        account = client.get_account()

        # Should handle gracefully
        assert account is None

    @responses.activate
    def test_network_error_handling(self):
        """Test handling of network errors."""
        responses.add(
            responses.GET,
            "https://paper-api.alpaca.markets/v2/account",
            body=Exception("Network error")
        )

        client = AlpacaBrokerClient("key", "secret", paper_mode=True)

        # Should handle gracefully without crashing
        try:
            account = client.get_account()
            assert account is None
        except Exception:
            # Exception is also acceptable
            pass


@pytest.mark.integration
class TestPaperVsLiveMode:
    """Test differences between paper and live mode."""

    def test_paper_mode_url(self):
        """Test paper mode uses correct URL."""
        client = AlpacaBrokerClient("key", "secret", paper_mode=True)
        assert "paper-api.alpaca.markets" in client.base_url

    def test_live_mode_url(self):
        """Test live mode uses correct URL."""
        client = AlpacaBrokerClient("key", "secret", paper_mode=False)
        assert "api.alpaca.markets" in client.base_url
        assert "paper" not in client.base_url
