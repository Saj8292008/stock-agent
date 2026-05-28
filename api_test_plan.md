# API Endpoint Testing Plan

## Overview
This document outlines the comprehensive API testing that would be performed on the stock trading system.

## Test Environment
- Mode: Paper Trading (BROKER_ENABLED=false)
- TradingView: Enabled
- Risk Manager: Enabled
- Base URL: http://localhost:8000

## API Endpoints to Test

### 1. GET /api/prices
**Purpose**: Get current prices for all tracked stocks
**Expected Response**:
```json
{
  "AAPL": 150.25,
  "GOOGL": 2800.50,
  "MSFT": 380.75,
  ...
}
```

### 2. GET /api/portfolio
**Purpose**: Get full portfolio snapshot with holdings and P&L
**Expected Response**:
```json
{
  "cash": 100000.00,
  "holdings": [],
  "total_value": 100000.00,
  "total_invested": 0,
  "total_pnl": 0,
  "prices": {...},
  "stocks": {...},
  "refs": {...}
}
```

### 3. GET /api/trades?limit=50
**Purpose**: Get trade history
**Expected Response**: Array of trade objects
```json
[
  {
    "symbol": "AAPL",
    "action": "buy",
    "shares": 10.0,
    "price": 150.0,
    "total": 1500.0,
    "reason": "Test trade",
    "timestamp": "2026-05-28T..."
  }
]
```

### 4. GET /api/orders?limit=100&status=pending
**Purpose**: Get order history with optional status filter
**Expected Response**: Array of order objects
```json
[
  {
    "id": 1,
    "broker_order_id": null,
    "symbol": "GOOGL",
    "side": "buy",
    "order_type": "market",
    "quantity": 5.0,
    "status": "pending",
    "submitted_at": "2026-05-28T...",
    "strategy_name": "test_strategy"
  }
]
```

### 5. GET /api/orders/{order_id}
**Purpose**: Get specific order details
**Expected Response**: Single order object

### 6. GET /api/signals?limit=50
**Purpose**: Get TradingView signal history
**Expected Response**: Array of signal objects
```json
[
  {
    "id": 1,
    "symbol": "MSFT",
    "action": "buy",
    "strategy": "test_strategy",
    "price": 300.0,
    "quantity": 3.0,
    "status": "pending",
    "received_at": "2026-05-28T..."
  }
]
```

### 7. GET /api/config-status
**Purpose**: Get current configuration status
**Expected Response**:
```json
{
  "valid": true,
  "broker_enabled": false,
  "tradingview_enabled": true,
  "risk_manager_enabled": true,
  "emergency_stop": false,
  "paper_mode": true,
  "starting_cash": 100000
}
```

### 8. GET /api/risk-limits
**Purpose**: Get current risk limits
**Expected Response**:
```json
{
  "max_position_size": 0.10,
  "max_daily_loss": -0.02,
  "max_total_exposure": 0.80,
  "max_orders_per_day": 100,
  "max_concentration": 0.25,
  "enabled": true
}
```

### 9. PUT /api/risk-limits
**Purpose**: Update risk limits
**Request Body**:
```json
{
  "max_position_size": 0.15,
  "max_daily_loss": -0.03
}
```
**Expected Response**: Updated risk limits object

### 10. GET /api/risk-status
**Purpose**: Get current risk status and usage
**Expected Response**:
```json
{
  "total_exposure": 0.0,
  "daily_pnl": 0.0,
  "daily_pnl_pct": 0.0,
  "orders_today": 0,
  "max_position_size": 0.10,
  "max_daily_loss": -0.02,
  "breaches": []
}
```

### 11. GET /api/daily-metrics?limit=30
**Purpose**: Get daily performance metrics
**Expected Response**: Array of daily metric objects
```json
[
  {
    "date": "2026-05-28",
    "starting_value": 100000.00,
    "ending_value": 100000.00,
    "daily_pnl": 0.0,
    "daily_return_pct": 0.0,
    "trades_count": 0,
    "winners_count": 0,
    "losers_count": 0
  }
]
```

### 12. POST /api/run-cycle
**Purpose**: Manually trigger a trading cycle
**Expected Response**:
```json
{
  "status": "ok",
  "actions": [],
  "prices": {...}
}
```

### 13. POST /api/webhook/tradingview
**Purpose**: Receive TradingView webhook signals
**Request Body (Valid)**:
```json
{
  "passphrase": "change-me-to-secure-passphrase",
  "ticker": "NASDAQ:GOOGL",
  "action": "buy",
  "strategy": "test_strategy",
  "price": 150.0
}
```
**Expected Response**:
```json
{
  "status": "received",
  "signal_id": 2,
  "execution": {...}
}
```

**Request Body (Invalid Passphrase)**:
```json
{
  "passphrase": "wrong-password",
  "ticker": "NASDAQ:GOOGL",
  "action": "buy"
}
```
**Expected Response**: 401 Unauthorized

### 14. GET /api/market-status
**Purpose**: Check if market is currently open
**Expected Response**:
```json
{
  "is_open": false,
  "current_et": "2026-05-28 11:35:46",
  "seconds_to_open": 5400,
  "next_open_et": "2026-05-29T09:30:00"
}
```

### 15. GET /api/history/{symbol}?period=1mo
**Purpose**: Get price history for a symbol
**Expected Response**: Array of historical price data

## Error Scenarios to Test

### 1. Invalid Webhook Passphrase
- POST /api/webhook/tradingview with wrong passphrase
- Expected: 401 Unauthorized

### 2. Missing Required Fields
- POST /api/webhook/tradingview without ticker
- Expected: 422 Validation Error

### 3. Invalid Symbol
- POST /api/webhook/tradingview with non-existent ticker
- Expected: Signal logged, but execution may fail gracefully

### 4. Order Not Found
- GET /api/orders/99999
- Expected: 404 Not Found

### 5. Cannot Cancel Filled Order
- POST /api/orders/cancel/{order_id} for filled order
- Expected: 400 Bad Request

## Test Success Criteria

✅ All endpoints return appropriate HTTP status codes
✅ Response formats match expected schemas
✅ Authentication/authorization works correctly
✅ Error handling provides clear messages
✅ Database operations persist correctly
✅ Risk limits are enforced
✅ TradingView webhook validation works
✅ Paper trading mode prevents real broker calls

## Notes
- All tests run in paper trading mode
- No real broker credentials required
- No real money involved
- Database is properly migrated before testing
