"""
Configuration for stock-agent trading system.

This module centralizes all configuration parameters including:
- Stock symbols and trading parameters
- Broker API settings
- TradingView webhook settings
- Risk management controls
- System behavior flags
"""

import os
from typing import Optional

# ── Stock Selection & Trading Parameters ─────────────────────────────────────

STOCKS = {
    "GOOGL": "Google",
    "RIVN":  "Rivian",
    "META":  "Meta",
    "NVDA":  "Nvidia",
    "GLD":   "Gold (ETF)",
    "SLV":   "Silver (ETF)",
    "TSLA":  "Tesla",
    "GS":    "Goldman Sachs",
    "MU":    "Micron Technology",
}

STARTING_CASH        = 100_000.0
ALLOCATION_PER_STOCK = 0.10   # 10% of portfolio per position

BUY_DIP_THRESHOLD    = -0.05  # buy when price dips 5% below rolling ref
TAKE_PROFIT          =  0.10  # sell when +10% from entry
STOP_LOSS            = -0.07  # sell when -7% from entry

POLL_INTERVAL        = 300    # seconds between agent cycles
DB_PATH              = "portfolio.db"

# ── Broker Settings ───────────────────────────────────────────────────────────

# Enable broker integration (if False, runs in pure paper trading mode)
BROKER_ENABLED: bool = False

# Alpaca API credentials (loaded from environment)
ALPACA_API_KEY: Optional[str] = None
ALPACA_API_SECRET: Optional[str] = None

# Use Alpaca paper trading endpoint (if False, uses live trading endpoint)
ALPACA_PAPER_MODE: bool = True

# ── TradingView Integration ───────────────────────────────────────────────────

# Enable TradingView webhook signal processing
TRADINGVIEW_ENABLED: bool = False

# Webhook security passphrase (loaded from environment)
TRADINGVIEW_PASSPHRASE: Optional[str] = None

# ── Risk Management ───────────────────────────────────────────────────────────

# Enable risk manager (validates all orders against risk limits)
ENABLE_RISK_MANAGER: bool = True

# Emergency stop flag (if True, blocks all new orders and can close positions)
EMERGENCY_STOP: bool = False

# ── Environment Variable Loading ──────────────────────────────────────────────


def load_from_env() -> None:
    """
    Load configuration from environment variables.

    This function should be called at application startup to populate
    API keys and secrets from the environment.

    Environment variables:
    - ALPACA_API_KEY: Alpaca API key
    - ALPACA_API_SECRET: Alpaca API secret
    - ALPACA_PAPER_MODE: "true" or "false" (default: true)
    - TRADINGVIEW_PASSPHRASE: Webhook security passphrase
    - BROKER_ENABLED: "true" or "false" (default: false)
    - TRADINGVIEW_ENABLED: "true" or "false" (default: false)
    - ENABLE_RISK_MANAGER: "true" or "false" (default: true)
    - EMERGENCY_STOP: "true" or "false" (default: false)
    """
    global ALPACA_API_KEY, ALPACA_API_SECRET, ALPACA_PAPER_MODE
    global TRADINGVIEW_PASSPHRASE, TRADINGVIEW_ENABLED
    global BROKER_ENABLED, ENABLE_RISK_MANAGER, EMERGENCY_STOP

    # Alpaca broker settings
    ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
    ALPACA_API_SECRET = os.getenv("ALPACA_API_SECRET")
    ALPACA_PAPER_MODE = os.getenv("ALPACA_PAPER_MODE", "true").lower() == "true"

    # TradingView settings
    TRADINGVIEW_PASSPHRASE = os.getenv("TRADINGVIEW_PASSPHRASE", "change-me-to-secure-passphrase")
    TRADINGVIEW_ENABLED = os.getenv("TRADINGVIEW_ENABLED", "false").lower() == "true"

    # Feature flags
    BROKER_ENABLED = os.getenv("BROKER_ENABLED", "false").lower() == "true"
    ENABLE_RISK_MANAGER = os.getenv("ENABLE_RISK_MANAGER", "true").lower() == "true"
    EMERGENCY_STOP = os.getenv("EMERGENCY_STOP", "false").lower() == "true"


def get_broker_client():
    """
    Get an initialized broker client if broker is enabled.

    Returns:
        AlpacaBrokerClient instance or None if broker is disabled or credentials missing
    """
    if not BROKER_ENABLED:
        return None

    if not ALPACA_API_KEY or not ALPACA_API_SECRET:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Broker enabled but credentials not configured")
        return None

    from .broker_client import AlpacaBrokerClient
    return AlpacaBrokerClient(
        api_key=ALPACA_API_KEY,
        api_secret=ALPACA_API_SECRET,
        paper_mode=ALPACA_PAPER_MODE
    )


def validate_config() -> dict:
    """
    Validate current configuration and return status.

    Returns:
        Dictionary with validation results and warnings
    """
    issues = []
    warnings = []

    # Check broker configuration
    if BROKER_ENABLED:
        if not ALPACA_API_KEY:
            issues.append("Broker enabled but ALPACA_API_KEY not set")
        if not ALPACA_API_SECRET:
            issues.append("Broker enabled but ALPACA_API_SECRET not set")
        if not ALPACA_PAPER_MODE:
            warnings.append("LIVE TRADING MODE ACTIVE - Real money at risk!")

    # Check TradingView configuration
    if TRADINGVIEW_ENABLED:
        if not TRADINGVIEW_PASSPHRASE or TRADINGVIEW_PASSPHRASE == "change-me-to-secure-passphrase":
            warnings.append("TradingView enabled with default/weak passphrase")

    # Check risk management
    if BROKER_ENABLED and not ENABLE_RISK_MANAGER:
        warnings.append("Broker trading enabled without risk manager - this is dangerous!")

    # Check emergency stop
    if EMERGENCY_STOP:
        warnings.append("EMERGENCY_STOP is active - new orders will be blocked")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "broker_mode": "LIVE" if (BROKER_ENABLED and not ALPACA_PAPER_MODE) else "PAPER" if BROKER_ENABLED else "DISABLED",
        "tradingview_enabled": TRADINGVIEW_ENABLED,
        "risk_manager_enabled": ENABLE_RISK_MANAGER,
        "emergency_stop": EMERGENCY_STOP
    }
