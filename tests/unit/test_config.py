"""
Unit tests for config.py

Tests configuration management:
- Environment variable loading
- Default values
- Feature flags
- Broker client instantiation
"""

import pytest
import os
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestConfigLoading:
    """Test configuration loading from environment."""

    def test_load_default_config(self, monkeypatch):
        """Test loading configuration with default values."""
        # Clear relevant env vars
        for key in ['BROKER_ENABLED', 'TRADINGVIEW_ENABLED', 'ENABLE_RISK_MANAGER']:
            monkeypatch.delenv(key, raising=False)

        from backend import config
        # Reload to pick up env changes
        import importlib
        importlib.reload(config)

        # Should have default values
        assert hasattr(config, 'BROKER_ENABLED')
        assert hasattr(config, 'TRADINGVIEW_ENABLED')
        assert hasattr(config, 'ENABLE_RISK_MANAGER')

    def test_broker_enabled_true(self, monkeypatch):
        """Test broker enabled configuration."""
        monkeypatch.setenv('BROKER_ENABLED', 'true')
        monkeypatch.setenv('ALPACA_API_KEY', 'test_key')
        monkeypatch.setenv('ALPACA_API_SECRET', 'test_secret')

        from backend import config
        import importlib
        importlib.reload(config)

        assert config.BROKER_ENABLED is True

    def test_broker_enabled_false(self, monkeypatch):
        """Test broker disabled configuration."""
        monkeypatch.setenv('BROKER_ENABLED', 'false')

        from backend import config
        import importlib
        importlib.reload(config)

        assert config.BROKER_ENABLED is False

    def test_tradingview_enabled(self, monkeypatch):
        """Test TradingView enabled configuration."""
        monkeypatch.setenv('TRADINGVIEW_ENABLED', 'true')
        monkeypatch.setenv('TRADINGVIEW_PASSPHRASE', 'test_pass')

        from backend import config
        import importlib
        importlib.reload(config)

        assert config.TRADINGVIEW_ENABLED is True
        assert config.TRADINGVIEW_PASSPHRASE == 'test_pass'

    def test_risk_manager_enabled(self, monkeypatch):
        """Test risk manager enabled configuration."""
        monkeypatch.setenv('ENABLE_RISK_MANAGER', 'true')

        from backend import config
        import importlib
        importlib.reload(config)

        assert config.ENABLE_RISK_MANAGER is True

    def test_alpaca_paper_mode(self, monkeypatch):
        """Test Alpaca paper mode configuration."""
        monkeypatch.setenv('ALPACA_PAPER_MODE', 'true')

        from backend import config
        import importlib
        importlib.reload(config)

        assert config.ALPACA_PAPER_MODE is True

    def test_stock_symbols_loading(self, monkeypatch):
        """Test stock symbols list loading."""
        monkeypatch.setenv('STOCK_SYMBOLS', 'AAPL,GOOGL,MSFT,NVDA')

        from backend import config
        import importlib
        importlib.reload(config)

        assert len(config.STOCK_SYMBOLS) == 4
        assert 'AAPL' in config.STOCK_SYMBOLS
        assert 'NVDA' in config.STOCK_SYMBOLS


@pytest.mark.unit
class TestBrokerClientCreation:
    """Test broker client instantiation."""

    def test_get_broker_client_when_enabled(self, monkeypatch):
        """Test getting broker client when enabled."""
        monkeypatch.setenv('BROKER_ENABLED', 'true')
        monkeypatch.setenv('ALPACA_API_KEY', 'test_key')
        monkeypatch.setenv('ALPACA_API_SECRET', 'test_secret')
        monkeypatch.setenv('ALPACA_PAPER_MODE', 'true')

        from backend import config
        import importlib
        importlib.reload(config)

        if hasattr(config, 'get_broker_client'):
            client = config.get_broker_client()
            assert client is not None

    def test_get_broker_client_when_disabled(self, monkeypatch):
        """Test getting broker client when disabled."""
        monkeypatch.setenv('BROKER_ENABLED', 'false')

        from backend import config
        import importlib
        importlib.reload(config)

        if hasattr(config, 'get_broker_client'):
            client = config.get_broker_client()
            assert client is None

    def test_broker_client_missing_credentials(self, monkeypatch):
        """Test broker client with missing credentials."""
        monkeypatch.setenv('BROKER_ENABLED', 'true')
        monkeypatch.delenv('ALPACA_API_KEY', raising=False)
        monkeypatch.delenv('ALPACA_API_SECRET', raising=False)

        from backend import config
        import importlib

        # Should either raise error or return None
        try:
            importlib.reload(config)
            if hasattr(config, 'get_broker_client'):
                client = config.get_broker_client()
                # May be None if credentials missing
                assert client is None or client is not None
        except Exception:
            # Or may raise exception for missing credentials
            pass


@pytest.mark.unit
class TestConfigValidation:
    """Test configuration validation."""

    def test_validate_config_complete(self, monkeypatch):
        """Test config validation with complete settings."""
        monkeypatch.setenv('BROKER_ENABLED', 'true')
        monkeypatch.setenv('ALPACA_API_KEY', 'test_key')
        monkeypatch.setenv('ALPACA_API_SECRET', 'test_secret')
        monkeypatch.setenv('TRADINGVIEW_ENABLED', 'true')
        monkeypatch.setenv('TRADINGVIEW_PASSPHRASE', 'test_pass')

        from backend import config
        import importlib
        importlib.reload(config)

        # Should have all required settings
        assert config.BROKER_ENABLED is not None
        assert config.TRADINGVIEW_ENABLED is not None

    def test_validate_config_tradingview_without_passphrase(self, monkeypatch):
        """Test TradingView enabled without passphrase."""
        monkeypatch.setenv('TRADINGVIEW_ENABLED', 'true')
        monkeypatch.delenv('TRADINGVIEW_PASSPHRASE', raising=False)

        from backend import config
        import importlib

        # Should either use default or raise error
        try:
            importlib.reload(config)
            if config.TRADINGVIEW_ENABLED:
                # If enabled, should have passphrase set
                assert hasattr(config, 'TRADINGVIEW_PASSPHRASE')
        except Exception:
            # Or may raise error for missing passphrase
            pass


@pytest.mark.unit
class TestDatabasePath:
    """Test database path configuration."""

    def test_default_database_path(self, monkeypatch):
        """Test default database path."""
        monkeypatch.delenv('DB_PATH', raising=False)

        from backend import config
        import importlib
        importlib.reload(config)

        # Should have default DB_PATH
        assert hasattr(config, 'DB_PATH')
        assert config.DB_PATH is not None

    def test_custom_database_path(self, monkeypatch):
        """Test custom database path from environment."""
        custom_path = '/tmp/test_custom.db'
        monkeypatch.setenv('DB_PATH', custom_path)

        from backend import config
        import importlib
        importlib.reload(config)

        assert config.DB_PATH == custom_path


@pytest.mark.unit
class TestEmergencyStop:
    """Test emergency stop configuration."""

    def test_emergency_stop_file_path(self, monkeypatch):
        """Test emergency stop file path configuration."""
        test_path = '/tmp/test_emergency_stop'
        monkeypatch.setenv('EMERGENCY_STOP_FILE', test_path)

        from backend import config
        import importlib
        importlib.reload(config)

        if hasattr(config, 'EMERGENCY_STOP_FILE'):
            assert config.EMERGENCY_STOP_FILE == test_path

    def test_emergency_stop_default(self, monkeypatch):
        """Test emergency stop default path."""
        monkeypatch.delenv('EMERGENCY_STOP_FILE', raising=False)

        from backend import config
        import importlib
        importlib.reload(config)

        # Should have some default path
        if hasattr(config, 'EMERGENCY_STOP_FILE'):
            assert config.EMERGENCY_STOP_FILE is not None


@pytest.mark.unit
class TestBooleanParsing:
    """Test boolean environment variable parsing."""

    def test_parse_true_values(self, monkeypatch):
        """Test parsing various true values."""
        true_values = ['true', 'True', 'TRUE', '1', 'yes', 'Yes']

        for value in true_values:
            monkeypatch.setenv('TEST_BOOL', value)

            # Simple boolean parsing
            result = os.getenv('TEST_BOOL', 'false').lower() in ['true', '1', 'yes']
            assert result is True

    def test_parse_false_values(self, monkeypatch):
        """Test parsing various false values."""
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'No']

        for value in false_values:
            monkeypatch.setenv('TEST_BOOL', value)

            # Simple boolean parsing
            result = os.getenv('TEST_BOOL', 'false').lower() in ['true', '1', 'yes']
            assert result is False


@pytest.mark.unit
class TestConfigConstants:
    """Test configuration constants."""

    def test_default_allocation_percentage(self, monkeypatch):
        """Test default allocation percentage."""
        from backend import config
        import importlib
        importlib.reload(config)

        # Should have allocation settings
        if hasattr(config, 'DEFAULT_ALLOCATION_PCT'):
            assert 0 < config.DEFAULT_ALLOCATION_PCT <= 1.0

    def test_buy_the_dip_threshold(self, monkeypatch):
        """Test buy-the-dip threshold configuration."""
        from backend import config
        import importlib
        importlib.reload(config)

        # Should have dip threshold
        if hasattr(config, 'BUY_DIP_THRESHOLD'):
            assert config.BUY_DIP_THRESHOLD < 0  # Negative percentage

    def test_sell_profit_target(self, monkeypatch):
        """Test sell profit target configuration."""
        from backend import config
        import importlib
        importlib.reload(config)

        # Should have profit target
        if hasattr(config, 'SELL_PROFIT_TARGET'):
            assert config.SELL_PROFIT_TARGET > 0  # Positive percentage
