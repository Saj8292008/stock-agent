# Stock Agent — Automated Trading System

**Version 2.0** - Paper Trading + Live Broker Integration + TradingView Webhooks

Automated trading system for **Google, Rivian, Meta, Nvidia, Gold (GLD), Silver (SLV), Tesla, Goldman Sachs, and Micron Technology**.

## Features

- **Paper Trading Mode**: Safe simulation without real money
- **Alpaca Broker Integration**: Execute real trades via Alpaca API
- **TradingView Webhooks**: Receive and execute signals from TradingView alerts
- **Risk Management**: Comprehensive position limits and daily loss controls
- **RESTful API**: Monitor and control via HTTP endpoints
- **Complete Audit Trail**: All actions logged to database

## Trading Strategy

| Rule | Threshold |
|------|-----------|
| **Buy** | Price drops ≥ 5% below the rolling reference high |
| **Take profit** | Price rises ≥ 10% above entry |
| **Stop loss** | Price falls ≥ 7% below entry |
| **Allocation** | 10% of portfolio value per position |

Starting capital: **$100,000**. Reference price ratchets up as a stock climbs when you're not holding it.

## Trading Modes

1. **Pure Paper Trading** (default, safest)
2. **Alpaca Paper Mode** (broker-connected paper trading)
3. **Live Trading with Alpaca** (real money)
4. **TradingView Signal Integration** (webhook-driven)

---

## Setup

```bash
# 1. Python backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Frontend
cd frontend
npm install
cd ..

# 3. Environment configuration
cp .env.example .env
# Edit .env and add your API keys (see Configuration section)

# 4. Initialize database
python -c "from backend.portfolio import init_db; init_db()"
```

---

## Configuration

### Quick Start (Paper Trading - No API Keys Needed)

```bash
# .env file
BROKER_ENABLED=false
TRADINGVIEW_ENABLED=false
ENABLE_RISK_MANAGER=true
```

### Alpaca Broker Setup

1. Create account at [alpaca.markets](https://alpaca.markets)
2. Generate API keys (Paper Trading section)
3. Add to `.env`:

```bash
ALPACA_API_KEY=your_key_here
ALPACA_API_SECRET=your_secret_here
ALPACA_PAPER_MODE=true      # true = paper trading, false = live trading
BROKER_ENABLED=true
```

### TradingView Webhook Setup

1. Set a secure passphrase in `.env`:

```bash
TRADINGVIEW_PASSPHRASE=your_secure_random_passphrase
TRADINGVIEW_ENABLED=true
```

2. In TradingView, create an alert with webhook URL:
```
http://your-server-ip:8000/api/webhook/tradingview
```

3. Use this JSON payload in your alert:
```json
{
  "passphrase": "your_passphrase_from_env",
  "ticker": "{{ticker}}",
  "action": "buy",
  "strategy": "{{strategy.order.alert_message}}",
  "price": {{close}}
}
```

### Risk Management Configuration

Default risk limits (can be changed via API):
- Max position size: 10% of portfolio
- Max daily loss: -2%
- Max total exposure: 80%
- Max orders per day: 100
- Max concentration (single stock): 25%

**Update risk limits:**
```bash
curl -X PUT http://localhost:8000/api/risk-limits \
  -H "Content-Type: application/json" \
  -d '{"max_position_size": 0.15, "max_daily_loss": -0.03}'
```

---

## Running

### Option A — Full stack (API + dashboard + agent loop)

```bash
# Terminal 1 — API server (http://localhost:8000)
python serve.py

# Terminal 2 — React dashboard (http://localhost:5173)
cd frontend && npm run dev

# Terminal 3 — continuous trading agent (polls every 5 min)
python main.py
```

### Option B — CLI only

```bash
python cli.py status          # live portfolio overview
python cli.py run-cycle       # run one trade cycle now
python cli.py trades          # show trade history
python cli.py trades --limit 5
python cli.py reset           # wipe and restart at $100k
```

---

## Project Layout

```
stock-agent/
├── backend/
│   ├── config.py          # symbols, thresholds, settings
│   ├── data_feed.py       # yfinance price fetcher
│   ├── portfolio.py       # SQLite portfolio state
│   ├── trading_engine.py  # buy/sell logic
│   └── api.py             # FastAPI REST endpoints
├── frontend/
│   └── src/App.jsx        # React dashboard
├── main.py                # continuous agent loop
├── serve.py               # API server entry-point
├── cli.py                 # CLI interface
└── requirements.txt
```

## API Endpoints

### Portfolio & Trading
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/prices` | Current prices for all symbols |
| GET | `/api/portfolio` | Full portfolio snapshot |
| GET | `/api/trades` | Trade history |
| GET | `/api/history/{symbol}` | Price history (OHLCV) |
| POST | `/api/run-cycle` | Trigger a trade cycle manually |
| GET | `/api/market-status` | Check if market is open |

### Orders & Signals
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/orders` | Order history (with status filter) |
| GET | `/api/orders/{id}` | Get specific order details |
| POST | `/api/orders/cancel/{id}` | Cancel pending order |
| GET | `/api/signals` | TradingView signal history |
| POST | `/api/webhook/tradingview` | Receive TradingView webhooks |

### Risk Management
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/risk-limits` | Get current risk limits |
| PUT | `/api/risk-limits` | Update risk limits |
| GET | `/api/risk-status` | Risk status and warnings |

### Broker Integration
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/account` | Broker account information |
| POST | `/api/sync-positions` | Sync positions from broker |

### System Controls
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/emergency-stop` | Emergency stop all trading |
| GET | `/api/config-status` | Configuration validation |
| GET | `/api/daily-metrics` | Daily performance metrics |

---

## Emergency Procedures

### Emergency Stop

If you need to immediately halt all trading:

```bash
# Via API
curl -X POST http://localhost:8000/api/emergency-stop

# Via environment variable
# Set EMERGENCY_STOP=true in .env and restart
```

This will:
1. Block all new orders
2. Close all open positions (if broker is enabled)
3. Log the emergency stop event

### Position Sync

If local positions are out of sync with broker:

```bash
curl -X POST http://localhost:8000/api/sync-positions
```

### Risk Status Check

Monitor risk exposure and warnings:

```bash
curl http://localhost:8000/api/risk-status
```

---

## Testing Checklist

Before going live with real money, follow this testing progression:

- [ ] **Phase 1**: Test in pure paper mode (`BROKER_ENABLED=false`)
- [ ] **Phase 2**: Test TradingView webhooks in paper mode
- [ ] **Phase 3**: Test with Alpaca paper account (`ALPACA_PAPER_MODE=true`)
- [ ] **Phase 4**: Verify risk manager rejects invalid orders
- [ ] **Phase 5**: Test emergency stop procedure
- [ ] **Phase 6**: Run for at least 1 week in paper mode
- [ ] **Phase 7**: Start live with very small position sizes
- [ ] **Phase 8**: Monitor closely for first 2 weeks

⚠️ **Never skip steps 1-6 before risking real money!**

---

## Documentation

- **CLAUDE.md** - Complete technical documentation
- **.env.example** - Environment configuration template
- **API docs** - Available at `http://localhost:8000/docs` when running

---

## Security Best Practices

1. **Never commit .env file** - It contains API keys
2. **Use strong TradingView passphrase** - Long and random
3. **Rotate API keys periodically** - Every 3-6 months
4. **Keep risk manager enabled** - Always use `ENABLE_RISK_MANAGER=true`
5. **Monitor audit log** - Check `/api/daily-metrics` regularly
6. **Backup database** - Copy `portfolio.db` daily
7. **Use VPN/firewall** - Restrict API access
8. **Test in paper mode first** - Always!

---

## Troubleshooting

### Database Migration Issues
```python
python -c "from backend.migrations import run_migrations, verify_schema; run_migrations(); print(verify_schema())"
```

### Broker Connection Issues
```python
python -c "from backend.config import load_from_env, get_broker_client; load_from_env(); b=get_broker_client(); print(b.get_account())"
```

### Check Configuration
```bash
curl http://localhost:8000/api/config-status
```

---

## Performance Monitoring

```bash
# Daily P&L
curl http://localhost:8000/api/daily-metrics

# Current risk exposure
curl http://localhost:8000/api/risk-status

# Recent trades
curl http://localhost:8000/api/trades?limit=20

# Recent orders
curl http://localhost:8000/api/orders?limit=20
```
