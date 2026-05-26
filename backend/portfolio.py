import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .config import DB_PATH, STARTING_CASH


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    con = _conn()
    cur = con.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id         INTEGER PRIMARY KEY,
            cash       REAL    NOT NULL,
            updated_at TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS positions (
            symbol     TEXT PRIMARY KEY,
            shares     REAL NOT NULL,
            avg_cost   REAL NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trades (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol     TEXT NOT NULL,
            action     TEXT NOT NULL,
            shares     REAL NOT NULL,
            price      REAL NOT NULL,
            total      REAL NOT NULL,
            reason     TEXT,
            timestamp  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS price_refs (
            symbol     TEXT PRIMARY KEY,
            ref_price  REAL NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    if not cur.execute("SELECT id FROM portfolio LIMIT 1").fetchone():
        cur.execute(
            "INSERT INTO portfolio (cash, updated_at) VALUES (?, ?)",
            (STARTING_CASH, _now()),
        )
    con.commit()
    con.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── cash ──────────────────────────────────────────────────────────────────────

def get_cash() -> float:
    con = _conn()
    row = con.execute("SELECT cash FROM portfolio LIMIT 1").fetchone()
    con.close()
    return row[0] if row else STARTING_CASH


def set_cash(amount: float) -> None:
    con = _conn()
    con.execute("UPDATE portfolio SET cash = ?, updated_at = ?", (amount, _now()))
    con.commit()
    con.close()


# ── positions ─────────────────────────────────────────────────────────────────

def get_positions() -> Dict[str, dict]:
    con = _conn()
    rows = con.execute("SELECT symbol, shares, avg_cost FROM positions").fetchall()
    con.close()
    return {r[0]: {"shares": r[1], "avg_cost": r[2]} for r in rows}


def set_position(symbol: str, shares: float, avg_cost: float) -> None:
    con = _conn()
    if shares <= 0:
        con.execute("DELETE FROM positions WHERE symbol = ?", (symbol,))
    else:
        con.execute(
            "INSERT OR REPLACE INTO positions (symbol, shares, avg_cost, updated_at) VALUES (?, ?, ?, ?)",
            (symbol, shares, avg_cost, _now()),
        )
    con.commit()
    con.close()


# ── trades ────────────────────────────────────────────────────────────────────

def log_trade(symbol: str, action: str, shares: float, price: float, reason: str = "") -> None:
    con = _conn()
    con.execute(
        "INSERT INTO trades (symbol, action, shares, price, total, reason, timestamp) VALUES (?,?,?,?,?,?,?)",
        (symbol, action, shares, price, shares * price, reason, _now()),
    )
    con.commit()
    con.close()


def get_trades(limit: int = 50) -> List[dict]:
    con = _conn()
    rows = con.execute(
        "SELECT symbol, action, shares, price, total, reason, timestamp FROM trades ORDER BY timestamp DESC LIMIT ?",
        (limit,),
    ).fetchall()
    con.close()
    return [
        {"symbol": r[0], "action": r[1], "shares": r[2], "price": r[3],
         "total": r[4], "reason": r[5], "timestamp": r[6]}
        for r in rows
    ]


# ── reference prices ──────────────────────────────────────────────────────────

def get_ref_price(symbol: str) -> Optional[float]:
    con = _conn()
    row = con.execute("SELECT ref_price FROM price_refs WHERE symbol = ?", (symbol,)).fetchone()
    con.close()
    return row[0] if row else None


def set_ref_price(symbol: str, price: float) -> None:
    con = _conn()
    con.execute(
        "INSERT OR REPLACE INTO price_refs (symbol, ref_price, updated_at) VALUES (?, ?, ?)",
        (symbol, price, _now()),
    )
    con.commit()
    con.close()


# ── snapshot for API ──────────────────────────────────────────────────────────

def full_snapshot(prices: Dict[str, float]) -> dict:
    positions = get_positions()
    cash      = get_cash()

    holdings = []
    total_current  = 0.0
    total_invested = 0.0

    for sym, pos in positions.items():
        cur_price  = prices.get(sym, pos["avg_cost"])
        cur_value  = pos["shares"] * cur_price
        cost_basis = pos["shares"] * pos["avg_cost"]
        pnl        = cur_value - cost_basis

        holdings.append({
            "symbol":        sym,
            "shares":        pos["shares"],
            "avg_cost":      pos["avg_cost"],
            "current_price": cur_price,
            "current_value": cur_value,
            "pnl":           pnl,
            "pnl_pct":       pnl / cost_basis if cost_basis else 0,
        })
        total_current  += cur_value
        total_invested += cost_basis

    return {
        "cash":          cash,
        "holdings":      holdings,
        "total_value":   cash + total_current,
        "total_invested": total_invested,
        "total_pnl":     total_current - total_invested,
    }
