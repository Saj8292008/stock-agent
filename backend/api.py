from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import STOCKS
from . import portfolio as port
from .data_feed import get_current_prices, get_price_history
from .trading_engine import run_cycle
from .scheduler import _is_market_open, _seconds_until_open, _now_et

app = FastAPI(title="Stock Agent", version="1.0.0")

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
