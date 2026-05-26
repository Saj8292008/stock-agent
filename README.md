# Stock Agent — Paper Trading

Tracks **Google, Rivian, Meta, Nvidia, Gold (GLD), Silver (SLV), Tesla, Goldman Sachs, and Micron Technology** with automated paper trading.

## Strategy

| Rule | Threshold |
|------|-----------|
| **Buy** | Price drops ≥ 5 % below the rolling reference high |
| **Take profit** | Price rises ≥ 10 % above entry |
| **Stop loss** | Price falls ≥ 7 % below entry |
| **Allocation** | 10 % of portfolio value per position |

Starting capital: **$100,000**.  Reference price ratchets up as a stock climbs when you're not holding it.

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

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/prices` | Current prices for all symbols |
| GET | `/api/portfolio` | Full portfolio snapshot |
| GET | `/api/trades` | Trade history |
| GET | `/api/history/{symbol}` | Price history (OHLCV) |
| POST | `/api/run-cycle` | Trigger a trade cycle manually |
