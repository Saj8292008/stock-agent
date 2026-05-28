# Stock Agent - Technical Documentation

**Version:** 2.0.0
**Type:** Automated Stock Trading System
**Modes:** Paper Trading, Broker-Connected Trading, TradingView Integration

---

## Project Overview

Stock-agent is an automated trading system that evolved from a simple paper trading simulator to a production-ready live trading platform with broker integration (Alpaca) and TradingView webhook support.

### Key Capabilities

1. **Paper Trading Mode**: Simulates trades without real money
2. **Broker Integration**: Executes real trades via Alpaca API
3. **TradingView Webhooks**: Receives and executes signals from TradingView alerts
4. **Risk Management**: Comprehensive position limits and daily loss controls
5. **Audit Trail**: Complete logging of all trading activities
6. **RESTful API**: FastAPI-based HTTP API for monitoring and control

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    External Systems                          │
├─────────────────────────────────────────────────────────────┤
│  TradingView Alerts  →  Webhook  →  Stock Agent             │
│  Alpaca Broker API   ←  Orders   ←  Stock Agent             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Stock Agent Core                         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  FastAPI     │  │  Trading     │  │  Risk        │      │
│  │  REST API    │  │  Engine      │  │  Manager     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Broker      │  │  Portfolio   │  │  Data Feed   │      │
│  │  Client      │  │  Manager     │  │  (yfinance)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer (SQLite)                       │
├─────────────────────────────────────────────────────────────┤
│  • portfolio         • positions        • trades            │
│  • orders            • tradingview_signals                  │
│  • audit_log         • risk_limits      • daily_metrics     │
└─────────────────────────────────────────────────────────────┘
```

### Module Descriptions

#### `backend/config.py`
Central configuration module with environment variable loading.
- Stock symbols and trading parameters
- Broker API credentials
- TradingView settings
- Feature flags (risk manager, emergency stop)

#### `backend/portfolio.py`
Database interface for portfolio state management.
- Cash and position tracking
- Trade history logging
- Order management
- Signal tracking
- Risk limits storage

#### `backend/trading_engine.py`
Core trading logic and order execution.
- `run_cycle()`: Main buy-the-dip strategy
- `execute_tradingview_signal()`: Process TradingView webhooks
- `_execute_order()`: Unified order execution (paper or broker)
- Risk validation integration

#### `backend/broker_client.py`
Alpaca broker API integration.
- Market/limit/stop order submission
- Order status polling
- Account and position queries
- Real-time price data
- Paper/live mode toggle

#### `backend/broker_feed.py`
Data synchronization between broker and local state.
- Real-time price fetching
- Position reconciliation
- Account balance sync

#### `backend/risk_manager.py`
Risk controls and trade validation.
- Position size limits
- Concentration limits
- Daily loss limits
- Trade frequency limits
- Audit logging

#### `backend/migrations.py`
Database schema migrations.
- Schema version tracking
- Automated table creation
- Column additions for new features

#### `backend/api.py`
FastAPI REST API endpoints.
- Portfolio queries
- Order management
- TradingView webhook receiver
- Risk limit configuration
- Emergency controls

---

## Database Schema

### Core Tables (v0 - Paper Trading)

#### `portfolio`
```sql
CREATE TABLE portfolio (
    id         INTEGER PRIMARY KEY,
    cash       REAL NOT NULL,
    updated_at TEXT NOT NULL,
    -- v1 additions:
    buying_power     REAL,
    margin_used      REAL DEFAULT 0,
    account_value    REAL,
    last_synced_at   TEXT
);
```

#### `positions`
```sql
CREATE TABLE positions (
    symbol     TEXT PRIMARY KEY,
    shares     REAL NOT NULL,
    avg_cost   REAL NOT NULL,
    updated_at TEXT NOT NULL
);
```

#### `trades`
```sql
CREATE TABLE trades (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol    TEXT NOT NULL,
    action    TEXT NOT NULL,
    shares    REAL NOT NULL,
    price     REAL NOT NULL,
    total     REAL NOT NULL,
    reason    TEXT,
    timestamp TEXT NOT NULL,
    -- v1 additions:
    order_id       INTEGER,
    commission     REAL DEFAULT 0,
    slippage       REAL DEFAULT 0,
    pnl            REAL,
    strategy_name  TEXT
);
```

### Live Trading Tables (v1)

#### `orders`
Tracks all broker order submissions and fills.
```sql
CREATE TABLE orders (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    broker_order_id  TEXT UNIQUE,
    symbol           TEXT NOT NULL,
    side             TEXT NOT NULL,      -- 'buy' or 'sell'
    order_type       TEXT NOT NULL,      -- 'market', 'limit', 'stop'
    quantity         REAL NOT NULL,
    limit_price      REAL,
    stop_price       REAL,
    status           TEXT NOT NULL,      -- 'pending', 'filled', 'canceled', etc.
    filled_qty       REAL DEFAULT 0,
    avg_fill_price   REAL,
    commission       REAL DEFAULT 0,
    submitted_at     TEXT NOT NULL,
    filled_at        TEXT,
    canceled_at      TEXT,
    error_message    TEXT,
    strategy_name    TEXT,
    signal_id        INTEGER,
    FOREIGN KEY (signal_id) REFERENCES tradingview_signals(id)
);
```

#### `tradingview_signals`
Stores incoming TradingView webhook signals.
```sql
CREATE TABLE tradingview_signals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol          TEXT NOT NULL,
    action          TEXT NOT NULL,      -- 'buy' or 'sell'
    strategy        TEXT,
    price           REAL,
    quantity        REAL,
    stop_loss       REAL,
    take_profit     REAL,
    raw_payload     TEXT,
    received_at     TEXT NOT NULL,
    processed_at    TEXT,
    order_id        INTEGER,
    status          TEXT NOT NULL,      -- 'pending', 'processed', 'rejected'
    rejection_reason TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);
```

#### `audit_log`
Complete audit trail of system events.
```sql
CREATE TABLE audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type  TEXT NOT NULL,     -- 'TRADE_EXECUTED', 'ORDER_REJECTED', etc.
    symbol      TEXT,
    user_action TEXT,
    data        TEXT,              -- JSON blob
    result      TEXT,
    message     TEXT,
    timestamp   TEXT NOT NULL
);
```

#### `risk_limits`
Configurable risk management parameters.
```sql
CREATE TABLE risk_limits (
    id                  INTEGER PRIMARY KEY,
    max_position_size   REAL NOT NULL,    -- e.g., 0.10 = 10% of portfolio
    max_daily_loss      REAL NOT NULL,    -- e.g., -0.02 = -2%
    max_total_exposure  REAL NOT NULL,    -- e.g., 0.80 = 80%
    max_orders_per_day  INTEGER NOT NULL,
    max_concentration   REAL NOT NULL,    -- e.g., 0.25 = 25% in single stock
    enabled             INTEGER DEFAULT 1,
    updated_at          TEXT NOT NULL
);
```

#### `daily_metrics`
Daily performance tracking.
```sql
CREATE TABLE daily_metrics (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    date             TEXT UNIQUE NOT NULL,
    starting_value   REAL NOT NULL,
    ending_value     REAL NOT NULL,
    daily_pnl        REAL NOT NULL,
    daily_return_pct REAL NOT NULL,
    trades_count     INTEGER DEFAULT 0,
    winners_count    INTEGER DEFAULT 0,
    losers_count     INTEGER DEFAULT 0,
    largest_win      REAL DEFAULT 0,
    largest_loss     REAL DEFAULT 0,
    updated_at       TEXT NOT NULL
);
```

---

## API Endpoints

### Portfolio & Market Data

- `GET /api/prices` - Current prices for all tracked stocks
- `GET /api/portfolio` - Full portfolio snapshot with positions and P&L
- `GET /api/trades` - Trade history (limit parameter)
- `GET /api/history/{symbol}` - Historical price data (OHLCV)
- `GET /api/market-status` - Market open/close status

### Trading Operations

- `POST /api/run-cycle` - Manually trigger a trading cycle
- `POST /api/webhook/tradingview` - Receive TradingView alerts (webhook)

### Order Management

- `GET /api/orders` - Order history (with status filter)
- `GET /api/orders/{order_id}` - Get specific order details
- `POST /api/orders/cancel/{order_id}` - Cancel pending order

### TradingView Signals

- `GET /api/signals` - Signal history from TradingView

### Risk Management

- `GET /api/risk-limits` - Get current risk limits
- `PUT /api/risk-limits` - Update risk limits
- `GET /api/risk-status` - Current risk status and warnings

### Broker Integration

- `GET /api/account` - Broker account information
- `POST /api/sync-positions` - Sync positions from broker

### System Controls

- `POST /api/emergency-stop` - Emergency stop all trading
- `GET /api/config-status` - Configuration validation
- `GET /api/daily-metrics` - Daily performance metrics

---

## TradingView Webhook Setup

### 1. Create Alert in TradingView

When creating an alert, configure the webhook:

**Webhook URL:**
```
http://your-server-ip:8000/api/webhook/tradingview
```

**Webhook JSON Payload:**
```json
{
  "passphrase": "your_passphrase_from_env",
  "ticker": "{{ticker}}",
  "action": "buy",
  "strategy": "{{strategy.order.alert_message}}",
  "price": {{close}},
  "quantity": 10
}
```

### 2. Supported Fields

| Field | Required | Description |
|-------|----------|-------------|
| `passphrase` | Yes | Must match `TRADINGVIEW_PASSPHRASE` in .env |
| `ticker` | Yes | Stock symbol (e.g., "AAPL") |
| `action` | Yes | "buy" or "sell" |
| `strategy` | No | Strategy name for logging |
| `price` | Recommended | Current price (uses {{close}}) |
| `quantity` | No | Number of shares (uses default allocation if omitted) |
| `stop_loss` | No | Stop loss price |
| `take_profit` | No | Take profit price |

### 3. Security

- Passphrase validation prevents unauthorized signals
- All signals logged to database before execution
- Failed signals logged with rejection reason

---

## Risk Management

### Default Risk Limits

```python
max_position_size = 0.10    # Max 10% of portfolio per position
max_daily_loss = -0.02      # Max 2% daily loss
max_total_exposure = 0.80   # Max 80% total exposure
max_orders_per_day = 100    # Max 100 orders per day
max_concentration = 0.25    # Max 25% in single stock
```

### Risk Checks

All BUY orders validated against:
1. Position size limit (% of portfolio)
2. Concentration limit (% in single stock)
3. Total exposure limit (% of portfolio invested)
4. Daily loss limit (stops trading if breached)
5. Daily trade count limit

SELL orders always approved (reducing risk).

### Configuring Limits

```bash
# View current limits
curl http://localhost:8000/api/risk-limits

# Update limits
curl -X PUT http://localhost:8000/api/risk-limits \
  -H "Content-Type: application/json" \
  -d '{
    "max_position_size": 0.15,
    "max_daily_loss": -0.03
  }'

# Check risk status
curl http://localhost:8000/api/risk-status
```

---

## Broker Setup (Alpaca)

### 1. Create Alpaca Account

- Paper Trading: https://app.alpaca.markets/paper/dashboard
- Live Trading: https://alpaca.markets/

### 2. Generate API Keys

Navigate to "Paper Trading" or "Live Trading" → "API Keys"

### 3. Configure Environment

```bash
# .env file
ALPACA_API_KEY=your_key_here
ALPACA_API_SECRET=your_secret_here
ALPACA_PAPER_MODE=true  # true for paper, false for live
BROKER_ENABLED=true
```

### 4. Test Connection

```python
from backend.broker_client import AlpacaBrokerClient

client = AlpacaBrokerClient(
    api_key="your_key",
    api_secret="your_secret",
    paper_mode=True
)

# Test account access
account = client.get_account()
print(f"Buying power: ${account['buying_power']}")

# Test order submission
order = client.submit_market_order("AAPL", 1, "buy")
print(f"Order ID: {order['order_id']}")
```

---

## Coding Conventions

### Python Style

- **PEP 8** compliance
- **Type hints** on all function parameters and returns
- **Docstrings** on all public functions (Google style)
- **Logging** instead of print statements
- **Error handling** with try/except and proper logging

### Example Function

```python
def execute_order(
    symbol: str,
    side: Literal["buy", "sell"],
    quantity: float,
    price: float,
    broker_client: Optional[AlpacaBrokerClient] = None
) -> Optional[dict]:
    """
    Execute an order via broker or paper trading.

    Args:
        symbol: Stock ticker symbol
        side: Order side ("buy" or "sell")
        quantity: Number of shares
        price: Price per share
        broker_client: Optional broker client for live trading

    Returns:
        Order result dictionary or None on failure

    Raises:
        ValueError: If quantity is negative
    """
    if quantity <= 0:
        raise ValueError("Quantity must be positive")

    logger.info(f"Executing {side} order: {quantity} {symbol} @ ${price}")

    try:
        # Implementation
        pass
    except Exception as e:
        logger.error(f"Order execution failed: {e}")
        return None
```

### Database Patterns

Always use connection context properly:

```python
def get_data():
    con = _conn()
    try:
        result = con.execute("SELECT * FROM table").fetchall()
        return result
    finally:
        con.close()
```

### Configuration Access

```python
# Import from config module
from .config import BROKER_ENABLED, get_broker_client

# Check feature flags
if BROKER_ENABLED:
    broker_client = get_broker_client()
```

---

## Testing Procedures

### Phase 1: Paper Trading Test

```bash
# Start with pure paper trading
BROKER_ENABLED=false
TRADINGVIEW_ENABLED=false

# Run API server
python serve.py

# Trigger manual cycle
curl -X POST http://localhost:8000/api/run-cycle

# Check portfolio
curl http://localhost:8000/api/portfolio
```

### Phase 2: TradingView Integration Test

```bash
# Enable TradingView
TRADINGVIEW_ENABLED=true
TRADINGVIEW_PASSPHRASE=test123

# Test webhook (from command line)
curl -X POST http://localhost:8000/api/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{
    "passphrase": "test123",
    "ticker": "AAPL",
    "action": "buy",
    "price": 150.0
  }'

# Check signals
curl http://localhost:8000/api/signals
```

### Phase 3: Broker Paper Trading Test

```bash
# Enable Alpaca paper trading
BROKER_ENABLED=true
ALPACA_PAPER_MODE=true
ALPACA_API_KEY=your_paper_key
ALPACA_API_SECRET=your_paper_secret

# Test account sync
curl http://localhost:8000/api/account

# Test position sync
curl -X POST http://localhost:8000/api/sync-positions

# Run cycle with broker
curl -X POST http://localhost:8000/api/run-cycle

# Check orders
curl http://localhost:8000/api/orders
```

### Phase 4: Live Trading Test (⚠️ REAL MONEY)

```bash
# Only after extensive testing in paper mode!
BROKER_ENABLED=true
ALPACA_PAPER_MODE=false
ALPACA_API_KEY=your_live_key
ALPACA_API_SECRET=your_live_secret

# Start with small positions
# Monitor risk status frequently
curl http://localhost:8000/api/risk-status

# Use emergency stop if needed
curl -X POST http://localhost:8000/api/emergency-stop
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Database migrations run successfully
- [ ] All tests pass in paper mode
- [ ] TradingView webhooks tested
- [ ] Broker API credentials validated
- [ ] Risk limits configured appropriately
- [ ] Emergency stop procedure tested

### Production Setup

- [ ] `.env` file configured with production values
- [ ] API server running with process manager (systemd/supervisor)
- [ ] Database backed up regularly
- [ ] Logs being written and rotated
- [ ] Monitoring alerts configured
- [ ] API accessible only via secure network/VPN

### Safety Checks

- [ ] `ALPACA_PAPER_MODE=true` initially (even with live keys)
- [ ] `ENABLE_RISK_MANAGER=true` always
- [ ] Risk limits set conservatively
- [ ] Daily loss limit configured
- [ ] Position size limits appropriate for account size
- [ ] Emergency stop tested and accessible

---

## Troubleshooting

### Database Issues

```python
# Check schema version
from backend.migrations import get_schema_version, verify_schema
print(get_schema_version())
print(verify_schema())

# Run migrations
from backend.migrations import run_migrations
run_migrations()
```

### Broker Connection Issues

```python
# Test broker connectivity
from backend.config import load_from_env, get_broker_client
load_from_env()
broker = get_broker_client()
print(broker.get_account())
```

### Risk Manager Issues

```python
# Check risk status
from backend.risk_manager import RiskManager
rm = RiskManager()
print(rm.limits)
print(rm.get_risk_status(100000))
```

---

## Monitoring & Maintenance

### Daily Checks

1. Check risk status: `GET /api/risk-status`
2. Review audit log for anomalies
3. Verify position sync with broker
4. Check daily metrics

### Weekly Maintenance

1. Review trade performance
2. Adjust risk limits if needed
3. Check for failed orders
4. Backup database

### Monthly Tasks

1. Rotate API keys
2. Review and optimize strategy parameters
3. Analyze daily metrics trends
4. Update dependencies

---

## License & Disclaimer

This is trading software that can execute real financial transactions. Use at your own risk. The authors are not responsible for any financial losses incurred through use of this software. Always test thoroughly in paper trading mode before risking real money.
