"""
Risk management system for trade validation and position limits.

This module provides comprehensive risk checks before executing trades,
including position sizing, concentration limits, daily loss limits, and
trade frequency controls.
"""

import logging
import sqlite3
from typing import Dict, Optional, Tuple, Literal
from datetime import datetime, timezone, date

from .config import DB_PATH
from . import portfolio as port

logger = logging.getLogger(__name__)


def _conn() -> sqlite3.Connection:
    """Create a database connection."""
    return sqlite3.connect(DB_PATH)


def _now() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    """Get today's date as string (YYYY-MM-DD)."""
    return date.today().isoformat()


class RiskManager:
    """
    Manages risk controls and validates trades before execution.

    The risk manager enforces:
    - Maximum position size as percentage of portfolio
    - Maximum concentration in a single stock
    - Maximum total portfolio exposure
    - Daily loss limits
    - Maximum number of trades per day
    """

    def __init__(self):
        """Initialize the risk manager and load current risk limits."""
        self.limits = self.load_risk_limits()
        logger.info("RiskManager initialized")

    def load_risk_limits(self) -> dict:
        """
        Load current risk limits from database.

        Returns:
            Dictionary with risk limit parameters
        """
        con = _conn()
        cur = con.cursor()

        row = cur.execute("""
            SELECT max_position_size, max_daily_loss, max_total_exposure,
                   max_orders_per_day, max_concentration, enabled
            FROM risk_limits
            WHERE id = 1
        """).fetchone()

        con.close()

        if not row:
            # Return default limits if none exist
            logger.warning("No risk limits found in database, using defaults")
            return {
                "max_position_size": 0.10,
                "max_daily_loss": -0.02,
                "max_total_exposure": 0.80,
                "max_orders_per_day": 100,
                "max_concentration": 0.25,
                "enabled": True
            }

        return {
            "max_position_size": row[0],
            "max_daily_loss": row[1],
            "max_total_exposure": row[2],
            "max_orders_per_day": row[3],
            "max_concentration": row[4],
            "enabled": bool(row[5])
        }

    def reload_limits(self) -> None:
        """Reload risk limits from database (useful after updates)."""
        self.limits = self.load_risk_limits()
        logger.info("Risk limits reloaded")

    def validate_order(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        quantity: float,
        price: float,
        portfolio_value: float,
        current_positions: Optional[Dict[str, dict]] = None
    ) -> Tuple[bool, str]:
        """
        Validate an order against risk limits.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares
            price: Price per share
            portfolio_value: Current total portfolio value
            current_positions: Current positions dict (fetched if not provided)

        Returns:
            Tuple of (approved: bool, reason: str)
            If approved is True, reason is "OK"
            If approved is False, reason explains why order was rejected
        """
        # If risk manager is disabled, approve all orders
        if not self.limits.get("enabled", True):
            logger.info(f"Risk manager disabled, approving {side} {quantity} {symbol}")
            return (True, "OK (risk manager disabled)")

        # Fetch positions if not provided
        if current_positions is None:
            current_positions = port.get_positions()

        order_value = quantity * price

        # For sells, always approve (reducing risk)
        if side == "sell":
            return (True, "OK (sell order)")

        # Check 1: Maximum position size
        max_position_value = portfolio_value * self.limits["max_position_size"]

        existing_position = current_positions.get(symbol, {"shares": 0, "avg_cost": 0})
        existing_value = existing_position["shares"] * price
        new_position_value = existing_value + order_value

        if new_position_value > max_position_value:
            reason = (f"Position size limit exceeded: ${new_position_value:.2f} would exceed "
                      f"max ${max_position_value:.2f} ({self.limits['max_position_size']:.1%} of portfolio)")
            logger.warning(f"Order rejected - {reason}")
            self.log_risk_check(symbol, side, quantity, price, False, reason)
            return (False, reason)

        # Check 2: Maximum concentration (single stock exposure)
        max_concentration_value = portfolio_value * self.limits["max_concentration"]

        if new_position_value > max_concentration_value:
            reason = (f"Concentration limit exceeded: ${new_position_value:.2f} would exceed "
                      f"max ${max_concentration_value:.2f} ({self.limits['max_concentration']:.1%} of portfolio)")
            logger.warning(f"Order rejected - {reason}")
            self.log_risk_check(symbol, side, quantity, price, False, reason)
            return (False, reason)

        # Check 3: Maximum total exposure
        total_exposure = sum(pos["shares"] * price for pos in current_positions.values())
        total_exposure += order_value
        max_exposure_value = portfolio_value * self.limits["max_total_exposure"]

        if total_exposure > max_exposure_value:
            reason = (f"Total exposure limit exceeded: ${total_exposure:.2f} would exceed "
                      f"max ${max_exposure_value:.2f} ({self.limits['max_total_exposure']:.1%} of portfolio)")
            logger.warning(f"Order rejected - {reason}")
            self.log_risk_check(symbol, side, quantity, price, False, reason)
            return (False, reason)

        # Check 4: Daily loss limit
        daily_pnl = self.get_daily_pnl()
        daily_pnl_pct = daily_pnl / portfolio_value if portfolio_value > 0 else 0

        if daily_pnl_pct <= self.limits["max_daily_loss"]:
            reason = (f"Daily loss limit reached: {daily_pnl_pct:.2%} loss exceeds "
                      f"max {self.limits['max_daily_loss']:.2%}")
            logger.warning(f"Order rejected - {reason}")
            self.log_risk_check(symbol, side, quantity, price, False, reason)
            return (False, reason)

        # Check 5: Daily trade count limit
        daily_order_count = self.get_daily_order_count()

        if daily_order_count >= self.limits["max_orders_per_day"]:
            reason = (f"Daily order limit reached: {daily_order_count} orders >= "
                      f"max {self.limits['max_orders_per_day']}")
            logger.warning(f"Order rejected - {reason}")
            self.log_risk_check(symbol, side, quantity, price, False, reason)
            return (False, reason)

        # All checks passed
        logger.info(f"Order approved: {side} {quantity} {symbol} @ ${price}")
        self.log_risk_check(symbol, side, quantity, price, True, "OK")
        return (True, "OK")

    def get_daily_pnl(self) -> float:
        """
        Calculate today's profit/loss.

        Returns:
            Total P&L for today (can be negative)
        """
        con = _conn()
        cur = con.cursor()

        today = _today()

        # Get sum of realized P&L from trades today
        result = cur.execute("""
            SELECT SUM(pnl)
            FROM trades
            WHERE DATE(timestamp) = ?
            AND pnl IS NOT NULL
        """, (today,)).fetchone()

        con.close()

        realized_pnl = result[0] if result and result[0] else 0.0
        return float(realized_pnl)

    def get_daily_order_count(self) -> int:
        """
        Get the number of orders submitted today.

        Returns:
            Count of orders submitted today
        """
        con = _conn()
        cur = con.cursor()

        today = _today()

        # Count orders from orders table
        result = cur.execute("""
            SELECT COUNT(*)
            FROM orders
            WHERE DATE(submitted_at) = ?
        """, (today,)).fetchone()

        con.close()

        return result[0] if result else 0

    def check_daily_loss_limit(self, portfolio_value: float) -> Tuple[bool, str]:
        """
        Check if daily loss limit has been breached.

        This is used to determine if trading should be halted for the day.

        Args:
            portfolio_value: Current total portfolio value

        Returns:
            Tuple of (ok: bool, message: str)
        """
        daily_pnl = self.get_daily_pnl()
        daily_pnl_pct = daily_pnl / portfolio_value if portfolio_value > 0 else 0

        if daily_pnl_pct <= self.limits["max_daily_loss"]:
            return (
                False,
                f"Daily loss limit breached: {daily_pnl_pct:.2%} loss exceeds max {self.limits['max_daily_loss']:.2%}"
            )

        return (True, "OK")

    def log_risk_check(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        approved: bool,
        reason: str
    ) -> None:
        """
        Log a risk check to the audit log.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares
            price: Price per share
            approved: Whether order was approved
            reason: Approval or rejection reason
        """
        con = _conn()
        cur = con.cursor()

        data = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "order_value": quantity * price
        }

        cur.execute("""
            INSERT INTO audit_log (event_type, symbol, user_action, data, result, message, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "RISK_CHECK",
            symbol,
            f"{side.upper()} {quantity} @ ${price}",
            str(data),
            "APPROVED" if approved else "REJECTED",
            reason,
            _now()
        ))

        con.commit()
        con.close()

    def update_limits(
        self,
        max_position_size: Optional[float] = None,
        max_daily_loss: Optional[float] = None,
        max_total_exposure: Optional[float] = None,
        max_orders_per_day: Optional[int] = None,
        max_concentration: Optional[float] = None,
        enabled: Optional[bool] = None
    ) -> dict:
        """
        Update risk limits.

        Args:
            max_position_size: Max position as fraction of portfolio (e.g., 0.10 = 10%)
            max_daily_loss: Max daily loss as fraction (e.g., -0.02 = -2%)
            max_total_exposure: Max total exposure as fraction (e.g., 0.80 = 80%)
            max_orders_per_day: Max number of orders per day
            max_concentration: Max concentration in single stock (e.g., 0.25 = 25%)
            enabled: Whether risk manager is enabled

        Returns:
            Updated limits dictionary
        """
        con = _conn()
        cur = con.cursor()

        # Build UPDATE query dynamically based on provided parameters
        updates = []
        values = []

        if max_position_size is not None:
            updates.append("max_position_size = ?")
            values.append(max_position_size)

        if max_daily_loss is not None:
            updates.append("max_daily_loss = ?")
            values.append(max_daily_loss)

        if max_total_exposure is not None:
            updates.append("max_total_exposure = ?")
            values.append(max_total_exposure)

        if max_orders_per_day is not None:
            updates.append("max_orders_per_day = ?")
            values.append(max_orders_per_day)

        if max_concentration is not None:
            updates.append("max_concentration = ?")
            values.append(max_concentration)

        if enabled is not None:
            updates.append("enabled = ?")
            values.append(1 if enabled else 0)

        if updates:
            updates.append("updated_at = ?")
            values.append(_now())

            query = f"UPDATE risk_limits SET {', '.join(updates)} WHERE id = 1"
            cur.execute(query, values)
            con.commit()

            logger.info(f"Updated risk limits: {updates}")

        con.close()

        # Reload limits
        self.reload_limits()

        return self.limits

    def get_risk_status(self, portfolio_value: float) -> dict:
        """
        Get current risk status summary.

        Args:
            portfolio_value: Current total portfolio value

        Returns:
            Dictionary with risk status information
        """
        daily_pnl = self.get_daily_pnl()
        daily_pnl_pct = daily_pnl / portfolio_value if portfolio_value > 0 else 0
        daily_orders = self.get_daily_order_count()

        positions = port.get_positions()
        total_exposure = sum(pos["shares"] * pos["avg_cost"] for pos in positions.values())
        exposure_pct = total_exposure / portfolio_value if portfolio_value > 0 else 0

        # Check if any limits are close to being breached (>80% utilization)
        warnings = []

        if daily_pnl_pct < (self.limits["max_daily_loss"] * 0.8):
            warnings.append(f"Daily loss at {daily_pnl_pct:.2%}, approaching limit of {self.limits['max_daily_loss']:.2%}")

        if daily_orders > (self.limits["max_orders_per_day"] * 0.8):
            warnings.append(f"Daily orders at {daily_orders}, approaching limit of {self.limits['max_orders_per_day']}")

        if exposure_pct > (self.limits["max_total_exposure"] * 0.9):
            warnings.append(f"Total exposure at {exposure_pct:.1%}, approaching limit of {self.limits['max_total_exposure']:.1%}")

        return {
            "enabled": self.limits["enabled"],
            "daily_pnl": daily_pnl,
            "daily_pnl_pct": daily_pnl_pct,
            "daily_orders": daily_orders,
            "total_exposure": total_exposure,
            "exposure_pct": exposure_pct,
            "limits": self.limits,
            "warnings": warnings,
            "loss_limit_breached": daily_pnl_pct <= self.limits["max_daily_loss"],
            "order_limit_breached": daily_orders >= self.limits["max_orders_per_day"]
        }
