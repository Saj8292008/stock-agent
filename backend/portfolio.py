import sqlite3
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .config import DB_PATH, STARTING_CASH


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Initialize database with all required tables and run migrations."""
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

    # Run database migrations to add new tables for live trading
    from .migrations import run_migrations
    run_migrations()


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


# ── audit log ─────────────────────────────────────────────────────────────────

def log_audit(
    event_type: str,
    symbol: Optional[str] = None,
    user_action: Optional[str] = None,
    data: Optional[dict] = None,
    result: Optional[str] = None,
    message: Optional[str] = None
) -> None:
    """Log an event to the audit trail."""
    con = _conn()
    con.execute(
        "INSERT INTO audit_log (event_type, symbol, user_action, data, result, message, timestamp) VALUES (?,?,?,?,?,?,?)",
        (event_type, symbol, user_action, json.dumps(data) if data else None, result, message, _now()),
    )
    con.commit()
    con.close()


# ── orders ────────────────────────────────────────────────────────────────────

def log_order(
    broker_order_id: Optional[str],
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    limit_price: Optional[float] = None,
    stop_price: Optional[float] = None,
    status: str = "pending",
    strategy_name: Optional[str] = None,
    signal_id: Optional[int] = None
) -> int:
    """
    Log a new order to the orders table.

    Returns:
        Order ID (database primary key)
    """
    con = _conn()
    cur = con.cursor()
    cur.execute(
        """INSERT INTO orders (
            broker_order_id, symbol, side, order_type, quantity,
            limit_price, stop_price, status, submitted_at, strategy_name, signal_id
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (broker_order_id, symbol, side, order_type, quantity,
         limit_price, stop_price, status, _now(), strategy_name, signal_id),
    )
    order_id = cur.lastrowid
    con.commit()
    con.close()
    return order_id


def update_order_status(
    order_id: int,
    status: str,
    filled_qty: Optional[float] = None,
    avg_fill_price: Optional[float] = None,
    filled_at: Optional[str] = None,
    canceled_at: Optional[str] = None,
    error_message: Optional[str] = None
) -> None:
    """Update an order's status and fill information."""
    con = _conn()
    cur = con.cursor()

    updates = ["status = ?"]
    values = [status]

    if filled_qty is not None:
        updates.append("filled_qty = ?")
        values.append(filled_qty)

    if avg_fill_price is not None:
        updates.append("avg_fill_price = ?")
        values.append(avg_fill_price)

    if filled_at is not None:
        updates.append("filled_at = ?")
        values.append(filled_at)

    if canceled_at is not None:
        updates.append("canceled_at = ?")
        values.append(canceled_at)

    if error_message is not None:
        updates.append("error_message = ?")
        values.append(error_message)

    query = f"UPDATE orders SET {', '.join(updates)} WHERE id = ?"
    values.append(order_id)

    cur.execute(query, values)
    con.commit()
    con.close()


def get_orders(limit: int = 100, status: Optional[str] = None) -> List[dict]:
    """Get order history with optional status filter."""
    con = _conn()

    if status:
        rows = con.execute(
            """SELECT id, broker_order_id, symbol, side, order_type, quantity,
                      limit_price, stop_price, status, filled_qty, avg_fill_price,
                      commission, submitted_at, filled_at, strategy_name
               FROM orders WHERE status = ? ORDER BY submitted_at DESC LIMIT ?""",
            (status, limit),
        ).fetchall()
    else:
        rows = con.execute(
            """SELECT id, broker_order_id, symbol, side, order_type, quantity,
                      limit_price, stop_price, status, filled_qty, avg_fill_price,
                      commission, submitted_at, filled_at, strategy_name
               FROM orders ORDER BY submitted_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()

    con.close()
    return [
        {
            "id": r[0], "broker_order_id": r[1], "symbol": r[2], "side": r[3],
            "order_type": r[4], "quantity": r[5], "limit_price": r[6],
            "stop_price": r[7], "status": r[8], "filled_qty": r[9],
            "avg_fill_price": r[10], "commission": r[11], "submitted_at": r[12],
            "filled_at": r[13], "strategy_name": r[14]
        }
        for r in rows
    ]


def get_order_by_id(order_id: int) -> Optional[dict]:
    """Get a specific order by ID."""
    con = _conn()
    row = con.execute(
        """SELECT id, broker_order_id, symbol, side, order_type, quantity,
                  limit_price, stop_price, status, filled_qty, avg_fill_price,
                  commission, submitted_at, filled_at, canceled_at, error_message, strategy_name
           FROM orders WHERE id = ?""",
        (order_id,),
    ).fetchone()
    con.close()

    if not row:
        return None

    return {
        "id": row[0], "broker_order_id": row[1], "symbol": row[2], "side": row[3],
        "order_type": row[4], "quantity": row[5], "limit_price": row[6],
        "stop_price": row[7], "status": row[8], "filled_qty": row[9],
        "avg_fill_price": row[10], "commission": row[11], "submitted_at": row[12],
        "filled_at": row[13], "canceled_at": row[14], "error_message": row[15],
        "strategy_name": row[16]
    }


# ── tradingview signals ───────────────────────────────────────────────────────

def log_tradingview_signal(
    symbol: str,
    action: str,
    strategy: Optional[str] = None,
    price: Optional[float] = None,
    quantity: Optional[float] = None,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    raw_payload: Optional[str] = None
) -> int:
    """
    Log a TradingView webhook signal.

    Returns:
        Signal ID (database primary key)
    """
    con = _conn()
    cur = con.cursor()
    cur.execute(
        """INSERT INTO tradingview_signals (
            symbol, action, strategy, price, quantity, stop_loss, take_profit,
            raw_payload, received_at, status
        ) VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (symbol, action, strategy, price, quantity, stop_loss, take_profit,
         raw_payload, _now(), "pending"),
    )
    signal_id = cur.lastrowid
    con.commit()
    con.close()
    return signal_id


def get_pending_signals() -> List[dict]:
    """Get all unprocessed TradingView signals."""
    con = _conn()
    rows = con.execute(
        """SELECT id, symbol, action, strategy, price, quantity, stop_loss,
                  take_profit, received_at
           FROM tradingview_signals
           WHERE status = 'pending'
           ORDER BY received_at ASC"""
    ).fetchall()
    con.close()

    return [
        {
            "id": r[0], "symbol": r[1], "action": r[2], "strategy": r[3],
            "price": r[4], "quantity": r[5], "stop_loss": r[6],
            "take_profit": r[7], "received_at": r[8]
        }
        for r in rows
    ]


def mark_signal_processed(
    signal_id: int,
    order_id: Optional[int] = None,
    rejection_reason: Optional[str] = None
) -> None:
    """Mark a signal as processed (either executed or rejected)."""
    con = _conn()
    status = "rejected" if rejection_reason else "processed"
    con.execute(
        """UPDATE tradingview_signals
           SET status = ?, processed_at = ?, order_id = ?, rejection_reason = ?
           WHERE id = ?""",
        (status, _now(), order_id, rejection_reason, signal_id),
    )
    con.commit()
    con.close()


def get_signals(limit: int = 50) -> List[dict]:
    """Get signal history."""
    con = _conn()
    rows = con.execute(
        """SELECT id, symbol, action, strategy, price, quantity, status,
                  received_at, processed_at, rejection_reason
           FROM tradingview_signals
           ORDER BY received_at DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    con.close()

    return [
        {
            "id": r[0], "symbol": r[1], "action": r[2], "strategy": r[3],
            "price": r[4], "quantity": r[5], "status": r[6],
            "received_at": r[7], "processed_at": r[8], "rejection_reason": r[9]
        }
        for r in rows
    ]


# ── risk limits ───────────────────────────────────────────────────────────────

def get_risk_limits() -> Optional[dict]:
    """Get current risk limits."""
    con = _conn()
    row = con.execute(
        """SELECT max_position_size, max_daily_loss, max_total_exposure,
                  max_orders_per_day, max_concentration, enabled
           FROM risk_limits WHERE id = 1"""
    ).fetchone()
    con.close()

    if not row:
        return None

    return {
        "max_position_size": row[0],
        "max_daily_loss": row[1],
        "max_total_exposure": row[2],
        "max_orders_per_day": row[3],
        "max_concentration": row[4],
        "enabled": bool(row[5])
    }


# ── daily metrics ─────────────────────────────────────────────────────────────

def update_daily_metrics(
    date: str,
    starting_value: float,
    ending_value: float,
    daily_pnl: float,
    daily_return_pct: float,
    trades_count: int = 0,
    winners_count: int = 0,
    losers_count: int = 0,
    largest_win: float = 0,
    largest_loss: float = 0
) -> None:
    """Update or insert daily metrics."""
    con = _conn()
    con.execute(
        """INSERT OR REPLACE INTO daily_metrics (
            date, starting_value, ending_value, daily_pnl, daily_return_pct,
            trades_count, winners_count, losers_count, largest_win, largest_loss, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (date, starting_value, ending_value, daily_pnl, daily_return_pct,
         trades_count, winners_count, losers_count, largest_win, largest_loss, _now()),
    )
    con.commit()
    con.close()


def get_daily_metrics(limit: int = 30) -> List[dict]:
    """Get daily performance metrics."""
    con = _conn()
    rows = con.execute(
        """SELECT date, starting_value, ending_value, daily_pnl, daily_return_pct,
                  trades_count, winners_count, losers_count, largest_win, largest_loss
           FROM daily_metrics
           ORDER BY date DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    con.close()

    return [
        {
            "date": r[0], "starting_value": r[1], "ending_value": r[2],
            "daily_pnl": r[3], "daily_return_pct": r[4], "trades_count": r[5],
            "winners_count": r[6], "losers_count": r[7], "largest_win": r[8],
            "largest_loss": r[9]
        }
        for r in rows
    ]
