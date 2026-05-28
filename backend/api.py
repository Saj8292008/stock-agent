from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import logging

from .config import (
    STOCKS,
    TRADINGVIEW_ENABLED,
    TRADINGVIEW_PASSPHRASE,
    BROKER_ENABLED,
    EMERGENCY_STOP,
    load_from_env,
    get_broker_client,
    validate_config
)
from . import portfolio as port
from .data_feed import get_current_prices, get_price_history
from .trading_engine import run_cycle, execute_tradingview_signal
from .scheduler import _is_market_open, _seconds_until_open, _now_et

logger = logging.getLogger(__name__)

# Load configuration from environment
load_from_env()

app = FastAPI(title="Stock Agent", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/prices")
def prices():
    return get_current_prices(list(STOCKS.keys()))


@app.get("/api/portfolio")
def portfolio():
    prices = get_current_prices(list(STOCKS.keys()))
    snapshot = port.full_snapshot(prices)
    snapshot["prices"] = prices
    snapshot["stocks"] = STOCKS
    # Attach ref prices and % from ref for each stock
    refs = {}
    for sym in STOCKS:
        r = port.get_ref_price(sym)
        p = prices.get(sym)
        refs[sym] = {
            "ref_price": r,
            "pct_from_ref": ((p - r) / r) if (r and p) else None,
        }
    snapshot["refs"] = refs
    return snapshot


@app.get("/api/trades")
def trades(limit: int = 50):
    return port.get_trades(limit)


@app.get("/api/history/{symbol}")
def history(symbol: str, period: str = "1mo"):
    return get_price_history(symbol.upper(), period)


@app.post("/api/run-cycle")
def manual_cycle():
    prices  = get_current_prices(list(STOCKS.keys()))
    actions = run_cycle(prices)
    return {"status": "ok", "actions": actions, "prices": prices}


@app.get("/api/market-status")
def market_status():
    open_ = _is_market_open()
    from datetime import timedelta
    wait  = _seconds_until_open() if not open_ else 0
    opens_at = (_now_et() + timedelta(seconds=wait)).isoformat() if not open_ else None
    return {
        "is_open":        open_,
        "current_et":     _now_et().strftime("%Y-%m-%d %H:%M:%S"),
        "seconds_to_open": wait,
        "next_open_et":   opens_at,
    }


# ── TradingView Webhook ───────────────────────────────────────────────────────

class TradingViewWebhook(BaseModel):
    passphrase: str
    ticker: str
    action: str
    strategy: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@app.post("/api/webhook/tradingview")
def tradingview_webhook(webhook: TradingViewWebhook):
    """
    Receive and process TradingView webhook signals.

    Expected JSON payload:
    {
        "passphrase": "your_secret_passphrase",
        "ticker": "AAPL",
        "action": "buy",  // or "sell"
        "strategy": "my_strategy_name",
        "price": 150.25,
        "quantity": 10,  // optional, will use default allocation if not provided
        "stop_loss": 145.00,  // optional
        "take_profit": 160.00  // optional
    }
    """
    if not TRADINGVIEW_ENABLED:
        raise HTTPException(status_code=403, detail="TradingView webhook integration is disabled")

    # Validate passphrase
    if webhook.passphrase != TRADINGVIEW_PASSPHRASE:
        logger.warning(f"Invalid passphrase in TradingView webhook: {webhook.passphrase[:5]}...")
        raise HTTPException(status_code=401, detail="Invalid passphrase")

    # Log signal to database
    signal_id = port.log_tradingview_signal(
        symbol=webhook.ticker.upper(),
        action=webhook.action.lower(),
        strategy=webhook.strategy,
        price=webhook.price,
        quantity=webhook.quantity,
        stop_loss=webhook.stop_loss,
        take_profit=webhook.take_profit,
        raw_payload=json.dumps(webhook.dict())
    )

    logger.info(f"Received TradingView signal: {webhook.action} {webhook.ticker} (signal_id={signal_id})")

    # Get broker client and risk manager if enabled
    broker_client = get_broker_client() if BROKER_ENABLED else None

    risk_manager = None
    if BROKER_ENABLED:
        from .risk_manager import RiskManager
        risk_manager = RiskManager()

    # Execute signal
    signal = {
        "id": signal_id,
        "symbol": webhook.ticker.upper(),
        "action": webhook.action.lower(),
        "strategy": webhook.strategy,
        "price": webhook.price,
        "quantity": webhook.quantity,
        "stop_loss": webhook.stop_loss,
        "take_profit": webhook.take_profit
    }

    result = execute_tradingview_signal(signal, broker_client, risk_manager)

    return {
        "status": "received",
        "signal_id": signal_id,
        "execution": result
    }


# ── Orders ────────────────────────────────────────────────────────────────────

@app.get("/api/orders")
def get_orders_endpoint(limit: int = 100, status: Optional[str] = None):
    """Get order history with optional status filter."""
    return port.get_orders(limit=limit, status=status)


@app.get("/api/orders/{order_id}")
def get_order_endpoint(order_id: int):
    """Get specific order by ID."""
    order = port.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.post("/api/orders/cancel/{order_id}")
def cancel_order_endpoint(order_id: int):
    """Cancel a pending order."""
    order = port.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order["status"] not in ["pending", "new", "accepted"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel order in status: {order['status']}")

    broker_client = get_broker_client()
    if not broker_client:
        raise HTTPException(status_code=400, detail="Broker not enabled")

    if not order.get("broker_order_id"):
        raise HTTPException(status_code=400, detail="Order has no broker order ID")

    success = broker_client.cancel_order(order["broker_order_id"])

    if success:
        port.update_order_status(order_id, status="canceled", canceled_at=port._now())
        return {"status": "canceled", "order_id": order_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to cancel order with broker")


# ── TradingView Signals ───────────────────────────────────────────────────────

@app.get("/api/signals")
def get_signals_endpoint(limit: int = 50):
    """Get TradingView signal history."""
    return port.get_signals(limit=limit)


# ── Risk Management ───────────────────────────────────────────────────────────

@app.get("/api/risk-limits")
def get_risk_limits_endpoint():
    """Get current risk limits."""
    limits = port.get_risk_limits()
    if not limits:
        raise HTTPException(status_code=404, detail="Risk limits not configured")
    return limits


class RiskLimitsUpdate(BaseModel):
    max_position_size: Optional[float] = None
    max_daily_loss: Optional[float] = None
    max_total_exposure: Optional[float] = None
    max_orders_per_day: Optional[int] = None
    max_concentration: Optional[float] = None
    enabled: Optional[bool] = None


@app.put("/api/risk-limits")
def update_risk_limits_endpoint(limits: RiskLimitsUpdate):
    """Update risk limits."""
    from .risk_manager import RiskManager
    risk_manager = RiskManager()

    updated = risk_manager.update_limits(
        max_position_size=limits.max_position_size,
        max_daily_loss=limits.max_daily_loss,
        max_total_exposure=limits.max_total_exposure,
        max_orders_per_day=limits.max_orders_per_day,
        max_concentration=limits.max_concentration,
        enabled=limits.enabled
    )

    return updated


@app.get("/api/risk-status")
def get_risk_status_endpoint():
    """Get current risk status and warnings."""
    from .risk_manager import RiskManager
    risk_manager = RiskManager()

    positions = port.get_positions()
    cash = port.get_cash()
    prices = get_current_prices(list(positions.keys()))

    total_val = cash + sum(
        pos["shares"] * prices.get(sym, pos["avg_cost"])
        for sym, pos in positions.items()
    )

    return risk_manager.get_risk_status(total_val)


# ── Emergency Controls ────────────────────────────────────────────────────────

@app.post("/api/emergency-stop")
def emergency_stop_endpoint():
    """
    Emergency stop: Close all positions and block new orders.

    This endpoint triggers the emergency stop flag and optionally closes
    all open positions if broker is enabled.
    """
    # Set emergency stop flag
    import backend.config as config
    config.EMERGENCY_STOP = True

    result = {"emergency_stop_activated": True, "positions_closed": False}

    # Close all positions if broker enabled
    broker_client = get_broker_client()
    if broker_client:
        try:
            success = broker_client.close_all_positions()
            result["positions_closed"] = success
            if success:
                logger.warning("EMERGENCY STOP: All positions closed via broker")
        except Exception as e:
            logger.error(f"Failed to close positions during emergency stop: {e}")
            result["error"] = str(e)

    port.log_audit(
        "EMERGENCY_STOP",
        None,
        "EMERGENCY_STOP",
        result,
        "EXECUTED",
        "Emergency stop activated"
    )

    return result


# ── Broker Integration ────────────────────────────────────────────────────────

@app.get("/api/account")
def get_account_endpoint():
    """Get broker account information."""
    if not BROKER_ENABLED:
        raise HTTPException(status_code=400, detail="Broker not enabled")

    broker_client = get_broker_client()
    if not broker_client:
        raise HTTPException(status_code=500, detail="Failed to initialize broker client")

    account = broker_client.get_account()
    if not account:
        raise HTTPException(status_code=500, detail="Failed to fetch account from broker")

    return account


@app.post("/api/sync-positions")
def sync_positions_endpoint():
    """Manually trigger position synchronization from broker."""
    if not BROKER_ENABLED:
        raise HTTPException(status_code=400, detail="Broker not enabled")

    broker_client = get_broker_client()
    if not broker_client:
        raise HTTPException(status_code=500, detail="Failed to initialize broker client")

    from .broker_feed import sync_positions_from_broker, sync_account_from_broker

    # Sync positions
    position_result = sync_positions_from_broker(broker_client)

    # Sync account
    account_result = sync_account_from_broker(broker_client)

    return {
        "positions": position_result,
        "account": account_result
    }


# ── System Status ─────────────────────────────────────────────────────────────

@app.get("/api/config-status")
def config_status_endpoint():
    """Get current configuration status and validation."""
    return validate_config()


@app.get("/api/daily-metrics")
def daily_metrics_endpoint(limit: int = 30):
    """Get daily performance metrics."""
    return port.get_daily_metrics(limit=limit)
