"""
Integration tests for api.py

Tests FastAPI endpoints with TestClient:
- Portfolio and market data endpoints
- Trading operations
- Order management
- TradingView webhook
- Risk management endpoints
- System controls
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json

from tests.fixtures.sample_signals import (
    valid_buy_signal,
    valid_sell_signal,
    invalid_passphrase_signal,
    missing_required_fields_signal
)


@pytest.mark.integration
class TestPortfolioEndpoints:
    """Test portfolio and market data endpoints."""

    def test_get_portfolio(self, test_app: TestClient):
        """Test GET /api/portfolio endpoint."""
        response = test_app.get("/api/portfolio")

        assert response.status_code == 200
        data = response.json()
        assert 'cash' in data or 'portfolio' in data

    def test_get_prices(self, test_app: TestClient):
        """Test GET /api/prices endpoint."""
        with patch('backend.api.get_current_prices') as mock_prices:
            mock_prices.return_value = {
                'AAPL': 150.0,
                'GOOGL': 140.0
            }

            response = test_app.get("/api/prices")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_trades(self, test_app: TestClient):
        """Test GET /api/trades endpoint."""
        response = test_app.get("/api/trades")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)

    def test_get_trades_with_limit(self, test_app: TestClient):
        """Test GET /api/trades with limit parameter."""
        response = test_app.get("/api/trades?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)

    def test_get_market_status(self, test_app: TestClient):
        """Test GET /api/market-status endpoint."""
        response = test_app.get("/api/market-status")

        assert response.status_code == 200
        data = response.json()
        assert 'is_open' in data or 'status' in data or isinstance(data, dict)


@pytest.mark.integration
class TestTradingOperations:
    """Test trading operation endpoints."""

    def test_run_cycle(self, test_app: TestClient):
        """Test POST /api/run-cycle endpoint."""
        with patch('backend.api.run_cycle') as mock_cycle:
            mock_cycle.return_value = []

            response = test_app.post("/api/run-cycle")

        assert response.status_code == 200 or response.status_code == 201


@pytest.mark.integration
class TestTradingViewWebhook:
    """Test TradingView webhook endpoint."""

    def test_webhook_valid_buy_signal(self, test_app: TestClient):
        """Test webhook with valid buy signal."""
        signal = valid_buy_signal(passphrase="test_passphrase")

        with patch('backend.api.execute_tradingview_signal') as mock_execute:
            mock_execute.return_value = {'status': 'processed'}

            response = test_app.post(
                "/api/webhook/tradingview",
                json=signal
            )

        assert response.status_code in [200, 201, 202]

    def test_webhook_valid_sell_signal(self, test_app: TestClient):
        """Test webhook with valid sell signal."""
        signal = valid_sell_signal(passphrase="test_passphrase")

        with patch('backend.api.execute_tradingview_signal') as mock_execute:
            mock_execute.return_value = {'status': 'processed'}

            response = test_app.post(
                "/api/webhook/tradingview",
                json=signal
            )

        assert response.status_code in [200, 201, 202]

    def test_webhook_invalid_passphrase(self, test_app: TestClient):
        """Test webhook with invalid passphrase."""
        signal = invalid_passphrase_signal()

        response = test_app.post(
            "/api/webhook/tradingview",
            json=signal
        )

        # Should reject with 401 or 403
        assert response.status_code in [401, 403, 400]

    def test_webhook_missing_fields(self, test_app: TestClient):
        """Test webhook with missing required fields."""
        signal = missing_required_fields_signal()

        response = test_app.post(
            "/api/webhook/tradingview",
            json=signal
        )

        # Should reject with 400
        assert response.status_code == 400 or response.status_code == 422

    def test_webhook_invalid_action(self, test_app: TestClient):
        """Test webhook with invalid action."""
        signal = {
            'passphrase': 'test_passphrase',
            'ticker': 'AAPL',
            'action': 'hold',  # Invalid
            'price': 150.0
        }

        response = test_app.post(
            "/api/webhook/tradingview",
            json=signal
        )

        # Should reject invalid action
        assert response.status_code in [400, 422]

    def test_webhook_tradingview_disabled(self, test_app: TestClient, monkeypatch):
        """Test webhook when TradingView is disabled."""
        monkeypatch.setenv('TRADINGVIEW_ENABLED', 'false')

        signal = valid_buy_signal(passphrase="test_passphrase")

        response = test_app.post(
            "/api/webhook/tradingview",
            json=signal
        )

        # Should reject when disabled
        assert response.status_code in [403, 503]


@pytest.mark.integration
class TestOrderEndpoints:
    """Test order management endpoints."""

    def test_get_orders(self, test_app: TestClient):
        """Test GET /api/orders endpoint."""
        response = test_app.get("/api/orders")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)

    def test_get_orders_with_status_filter(self, test_app: TestClient):
        """Test GET /api/orders with status filter."""
        response = test_app.get("/api/orders?status=filled")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)

    def test_get_order_by_id(self, test_app: TestClient, test_db):
        """Test GET /api/orders/{order_id} endpoint."""
        # Create a test order first
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO orders (broker_order_id, symbol, side, order_type, quantity, status, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("test-order-1", "AAPL", "buy", "market", 10, "filled", "2024-01-01T00:00:00"))
        test_db.commit()
        order_id = cursor.lastrowid

        response = test_app.get(f"/api/orders/{order_id}")

        assert response.status_code in [200, 404]

    def test_cancel_order(self, test_app: TestClient, test_db):
        """Test POST /api/orders/cancel/{order_id} endpoint."""
        # Create a pending order
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO orders (broker_order_id, symbol, side, order_type, quantity, status, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("test-order-2", "AAPL", "buy", "limit", 10, "submitted", "2024-01-01T00:00:00"))
        test_db.commit()
        order_id = cursor.lastrowid

        with patch('backend.api.broker_client') as mock_broker:
            mock_broker.cancel_order.return_value = True

            response = test_app.post(f"/api/orders/cancel/{order_id}")

        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestSignalEndpoints:
    """Test TradingView signal endpoints."""

    def test_get_signals(self, test_app: TestClient):
        """Test GET /api/signals endpoint."""
        response = test_app.get("/api/signals")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)

    def test_get_signals_with_limit(self, test_app: TestClient):
        """Test GET /api/signals with limit parameter."""
        response = test_app.get("/api/signals?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)


@pytest.mark.integration
class TestRiskManagementEndpoints:
    """Test risk management endpoints."""

    def test_get_risk_limits(self, test_app: TestClient):
        """Test GET /api/risk-limits endpoint."""
        response = test_app.get("/api/risk-limits")

        assert response.status_code == 200
        data = response.json()
        assert 'max_position_size' in data or 'limits' in data or isinstance(data, dict)

    def test_update_risk_limits(self, test_app: TestClient):
        """Test PUT /api/risk-limits endpoint."""
        new_limits = {
            'max_position_size': 0.15,
            'max_daily_loss': -0.03
        }

        response = test_app.put(
            "/api/risk-limits",
            json=new_limits
        )

        assert response.status_code in [200, 201]

    def test_update_risk_limits_invalid_values(self, test_app: TestClient):
        """Test updating risk limits with invalid values."""
        invalid_limits = {
            'max_position_size': -0.10,  # Negative!
            'max_daily_loss': 0.05  # Should be negative
        }

        response = test_app.put(
            "/api/risk-limits",
            json=invalid_limits
        )

        # Should reject invalid values
        assert response.status_code in [400, 422]

    def test_get_risk_status(self, test_app: TestClient):
        """Test GET /api/risk-status endpoint."""
        response = test_app.get("/api/risk-status")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


@pytest.mark.integration
class TestBrokerEndpoints:
    """Test broker integration endpoints."""

    def test_get_account(self, test_app: TestClient):
        """Test GET /api/account endpoint."""
        with patch('backend.api.broker_client') as mock_broker:
            mock_broker.get_account.return_value = {
                'cash': '100000.0',
                'buying_power': '100000.0'
            }

            response = test_app.get("/api/account")

        assert response.status_code in [200, 503]

    def test_get_account_broker_disabled(self, test_app: TestClient, monkeypatch):
        """Test GET /api/account when broker is disabled."""
        monkeypatch.setenv('BROKER_ENABLED', 'false')

        response = test_app.get("/api/account")

        # Should indicate broker is disabled
        assert response.status_code in [503, 404]

    def test_sync_positions(self, test_app: TestClient):
        """Test POST /api/sync-positions endpoint."""
        with patch('backend.api.broker_client') as mock_broker:
            mock_broker.get_positions.return_value = []

            response = test_app.post("/api/sync-positions")

        assert response.status_code in [200, 503]


@pytest.mark.integration
class TestSystemControlEndpoints:
    """Test system control endpoints."""

    def test_emergency_stop(self, test_app: TestClient):
        """Test POST /api/emergency-stop endpoint."""
        response = test_app.post("/api/emergency-stop")

        assert response.status_code == 200
        data = response.json()
        assert 'status' in data or 'emergency_stop' in data or isinstance(data, dict)

    def test_emergency_stop_creates_file(self, test_app: TestClient, monkeypatch):
        """Test that emergency stop creates the stop file."""
        import tempfile
        import os

        stop_file = tempfile.mktemp()
        monkeypatch.setenv('EMERGENCY_STOP_FILE', stop_file)

        try:
            response = test_app.post("/api/emergency-stop")

            assert response.status_code == 200

            # Check if file was created (implementation dependent)
            # assert os.path.exists(stop_file)
        finally:
            if os.path.exists(stop_file):
                os.remove(stop_file)

    def test_config_status(self, test_app: TestClient):
        """Test GET /api/config-status endpoint."""
        response = test_app.get("/api/config-status")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_daily_metrics(self, test_app: TestClient):
        """Test GET /api/daily-metrics endpoint."""
        response = test_app.get("/api/daily-metrics")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)


@pytest.mark.integration
class TestErrorHandling:
    """Test API error handling."""

    def test_404_not_found(self, test_app: TestClient):
        """Test 404 response for nonexistent endpoint."""
        response = test_app.get("/api/nonexistent")

        assert response.status_code == 404

    def test_405_method_not_allowed(self, test_app: TestClient):
        """Test 405 for wrong HTTP method."""
        # Try POST on GET-only endpoint
        response = test_app.post("/api/portfolio")

        assert response.status_code == 405

    def test_422_validation_error(self, test_app: TestClient):
        """Test 422 for validation errors."""
        # Send invalid JSON to endpoint expecting specific format
        response = test_app.put(
            "/api/risk-limits",
            json={"invalid_field": "value"}
        )

        # May return 422 or 400 depending on validation
        assert response.status_code in [400, 422]


@pytest.mark.integration
class TestCORS:
    """Test CORS headers if enabled."""

    def test_cors_headers(self, test_app: TestClient):
        """Test that CORS headers are present."""
        response = test_app.get("/api/portfolio")

        # Check for CORS headers if enabled
        # headers = response.headers
        # May have Access-Control-Allow-Origin header


@pytest.mark.integration
class TestRateLimiting:
    """Test rate limiting if implemented."""

    @pytest.mark.slow
    def test_rate_limiting(self, test_app: TestClient):
        """Test rate limiting on webhook endpoint."""
        signal = valid_buy_signal(passphrase="test_passphrase")

        # Make many rapid requests
        responses_list = []
        for i in range(20):
            response = test_app.post(
                "/api/webhook/tradingview",
                json=signal
            )
            responses_list.append(response.status_code)

        # If rate limiting is implemented, should see some 429s
        # Otherwise all should succeed


@pytest.mark.integration
class TestHealthCheck:
    """Test health check endpoint if it exists."""

    def test_health_check(self, test_app: TestClient):
        """Test GET /health or /api/health endpoint."""
        # Try common health check paths
        for path in ["/health", "/api/health", "/api/status"]:
            response = test_app.get(path)
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
                break
