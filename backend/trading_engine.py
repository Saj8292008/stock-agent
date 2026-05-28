import logging
from typing import Dict, Optional

from .config import (
    ALLOCATION_PER_STOCK,
    BUY_DIP_THRESHOLD,
    STOCKS,
    STOP_LOSS,
    TAKE_PROFIT,
    EMERGENCY_STOP,
    ENABLE_RISK_MANAGER,
)
from . import portfolio as port

logger = logging.getLogger(__name__)


def run_cycle(
    prices: Dict[str, float],
    broker_client: Optional[object] = None,
    risk_manager: Optional[object] = None
) -> list:
    """
    Evaluate all tracked stocks and execute trades.

    Args:
        prices: Dictionary mapping symbols to current prices
        broker_client: Optional AlpacaBrokerClient for live trading (None = paper mode)
        risk_manager: Optional RiskManager for trade validation (None = no validation)

    Returns:
        List of actions taken (dictionaries with action details)
    """
    # Check emergency stop
    if EMERGENCY_STOP:
        logger.warning("EMERGENCY_STOP is active - blocking all trades")
        return []

    positions  = port.get_positions()
    cash       = port.get_cash()
    total_val  = cash + sum(
        pos["shares"] * prices.get(sym, pos["avg_cost"])
        for sym, pos in positions.items()
    )

    actions = []

    for symbol in STOCKS:
        price = prices.get(symbol)
        if not price:
            continue

        ref_price = port.get_ref_price(symbol)
        if ref_price is None:
            port.set_ref_price(symbol, price)
            ref_price = price

        position = positions.get(symbol)

        if position:
            pct = (price - position["avg_cost"]) / position["avg_cost"]

            if pct >= TAKE_PROFIT:
                action = _execute_order(
                    symbol, "sell", position["shares"], price,
                    f"Take profit {pct:+.1%}",
                    broker_client, risk_manager, "buy_the_dip"
                )
                if action:
                    actions.append(action)
            elif pct <= STOP_LOSS:
                action = _execute_order(
                    symbol, "sell", position["shares"], price,
                    f"Stop loss {pct:+.1%}",
                    broker_client, risk_manager, "buy_the_dip"
                )
                if action:
                    actions.append(action)

        else:
            pct_from_ref = (price - ref_price) / ref_price

            if pct_from_ref <= BUY_DIP_THRESHOLD:
                alloc  = total_val * ALLOCATION_PER_STOCK
                shares = alloc / price
                cost   = shares * price
                cash   = port.get_cash()

                if cash >= cost:
                    action = _execute_order(
                        symbol, "buy", shares, price,
                        f"Dip {pct_from_ref:+.1%} from ref",
                        broker_client, risk_manager, "buy_the_dip"
                    )
                    if action:
                        port.set_ref_price(symbol, price)
                        actions.append(action)
            else:
                # Ratchet reference price up as stock climbs
                if price > ref_price:
                    port.set_ref_price(symbol, price)

    return actions


def _execute_order(
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    reason: str,
    broker_client: Optional[object],
    risk_manager: Optional[object],
    strategy_name: str = "buy_the_dip"
) -> Optional[dict]:
    """
    Execute an order (either via broker or paper trading).

    This unified function handles:
    1. Risk validation (if risk_manager provided)
    2. Broker order submission (if broker_client provided)
    3. Position and cash updates
    4. Trade logging

    Args:
        symbol: Stock symbol
        side: "buy" or "sell"
        quantity: Number of shares
        price: Price per share (for risk validation and paper trading)
        reason: Trade reason/description
        broker_client: Optional broker client for live trading
        risk_manager: Optional risk manager for validation
        strategy_name: Name of strategy generating the trade

    Returns:
        Action dictionary if successful, None if rejected or failed
    """
    # Risk validation for buy orders
    if side == "buy" and risk_manager and ENABLE_RISK_MANAGER:
        positions = port.get_positions()
        cash = port.get_cash()
        total_val = cash + sum(
            pos["shares"] * price for pos in positions.values()
        )

        approved, rejection_reason = risk_manager.validate_order(
            symbol, side, quantity, price, total_val, positions
        )

        if not approved:
            logger.warning(f"Order rejected by risk manager: {rejection_reason}")
            port.log_audit(
                "ORDER_REJECTED",
                symbol,
                f"{side.upper()} {quantity} @ ${price}",
                {"reason": reason},
                "REJECTED",
                rejection_reason
            )
            return None

    # Execute via broker if provided
    if broker_client:
        return _execute_broker_order(
            symbol, side, quantity, price, reason, broker_client, strategy_name
        )
    else:
        return _execute_paper_order(
            symbol, side, quantity, price, reason, strategy_name
        )


def _execute_broker_order(
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    reason: str,
    broker_client: object,
    strategy_name: str
) -> Optional[dict]:
    """
    Execute order via broker API.

    Args:
        symbol: Stock symbol
        side: "buy" or "sell"
        quantity: Number of shares
        price: Reference price (for logging)
        reason: Trade reason
        broker_client: AlpacaBrokerClient instance
        strategy_name: Strategy name

    Returns:
        Action dictionary if successful, None on failure
    """
    try:
        # Submit market order to broker
        order = broker_client.submit_market_order(symbol, quantity, side)

        if not order:
            logger.error(f"Broker order submission failed: {side} {quantity} {symbol}")
            port.log_audit(
                "BROKER_ORDER_FAILED",
                symbol,
                f"{side.upper()} {quantity}",
                {"reason": reason},
                "FAILED",
                "Broker API returned no order"
            )
            return None

        # Log order to database
        order_id = port.log_order(
            broker_order_id=order["order_id"],
            symbol=symbol,
            side=side,
            order_type="market",
            quantity=quantity,
            status=order["status"],
            strategy_name=strategy_name
        )

        logger.info(f"Broker order submitted: {side.upper()} {quantity} {symbol} (order_id={order['order_id']})")

        # Wait for fill (with timeout)
        filled_order = broker_client.wait_for_fill(order["order_id"], timeout=30)

        if filled_order and filled_order.get("status") == "filled":
            fill_price = filled_order.get("filled_avg_price", price)
            filled_qty = filled_order.get("filled_qty", quantity)

            # Update order status
            port.update_order_status(
                order_id,
                status="filled",
                filled_qty=filled_qty,
                avg_fill_price=fill_price,
                filled_at=filled_order.get("filled_at")
            )

            # Update position and cash
            if side == "buy":
                cost = filled_qty * fill_price
                port.set_cash(port.get_cash() - cost)
                existing = port.get_positions().get(symbol, {"shares": 0, "avg_cost": 0})
                new_shares = existing["shares"] + filled_qty
                new_avg_cost = ((existing["shares"] * existing["avg_cost"]) + cost) / new_shares
                port.set_position(symbol, new_shares, new_avg_cost)
            else:  # sell
                proceeds = filled_qty * fill_price
                port.set_cash(port.get_cash() + proceeds)
                existing = port.get_positions().get(symbol, {"shares": 0, "avg_cost": 0})
                new_shares = existing["shares"] - filled_qty
                if new_shares <= 0.0001:
                    port.set_position(symbol, 0, 0)
                else:
                    port.set_position(symbol, new_shares, existing["avg_cost"])

            # Log trade
            pnl = None
            if side == "sell" and symbol in port.get_positions():
                cost_basis = quantity * port.get_positions()[symbol]["avg_cost"]
                pnl = (fill_price * filled_qty) - cost_basis

            # Update trades table with order_id and pnl
            port.log_trade(symbol, side.upper(), filled_qty, fill_price, reason)

            port.log_audit(
                "TRADE_EXECUTED",
                symbol,
                f"{side.upper()} {filled_qty} @ ${fill_price}",
                {"order_id": order["order_id"], "strategy": strategy_name},
                "SUCCESS",
                reason
            )

            logger.info(f"{side.upper()} {filled_qty:.4f} {symbol} @ ${fill_price:.2f} via broker — {reason}")

            return {
                "action": side.upper(),
                "symbol": symbol,
                "shares": filled_qty,
                "price": fill_price,
                "reason": reason,
                "broker_order_id": order["order_id"],
                "mode": "broker"
            }
        else:
            logger.warning(f"Order did not fill: {order['order_id']}")
            port.update_order_status(
                order_id,
                status=filled_order.get("status", "timeout") if filled_order else "timeout"
            )
            return None

    except Exception as e:
        logger.error(f"Broker order execution failed: {e}")
        port.log_audit(
            "BROKER_ORDER_ERROR",
            symbol,
            f"{side.upper()} {quantity}",
            {"reason": reason, "error": str(e)},
            "ERROR",
            str(e)
        )
        return None


def _execute_paper_order(
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    reason: str,
    strategy_name: str
) -> dict:
    """
    Execute order in paper trading mode.

    Args:
        symbol: Stock symbol
        side: "buy" or "sell"
        quantity: Number of shares
        price: Price per share
        reason: Trade reason
        strategy_name: Strategy name

    Returns:
        Action dictionary
    """
    cost = quantity * price

    if side == "buy":
        cash = port.get_cash()
        port.set_cash(cash - cost)

        # Accumulate position (don't overwrite)
        existing_positions = port.get_positions()
        if symbol in existing_positions:
            existing = existing_positions[symbol]
            old_shares = existing["shares"]
            old_avg_cost = existing["avg_cost"]
            new_shares = old_shares + quantity
            new_avg_cost = ((old_shares * old_avg_cost) + cost) / new_shares
            port.set_position(symbol, new_shares, new_avg_cost)
        else:
            port.set_position(symbol, quantity, price)

        port.log_trade(symbol, "BUY", quantity, price, reason)
        logger.info(f"BUY  {quantity:.4f} {symbol} @ ${price:.2f} (paper) — {reason}")
    else:  # sell
        position = port.get_positions().get(symbol, {"shares": 0, "avg_cost": 0})
        proceeds = quantity * price
        port.set_cash(port.get_cash() + proceeds)
        port.set_position(symbol, 0, 0)
        port.log_trade(symbol, "SELL", quantity, price, reason)
        logger.info(f"SELL {quantity:.4f} {symbol} @ ${price:.2f} (paper) — {reason}")

    return {
        "action": side.upper(),
        "symbol": symbol,
        "shares": quantity,
        "price": price,
        "reason": reason,
        "mode": "paper"
    }


def execute_tradingview_signal(
    signal: dict,
    broker_client: Optional[object],
    risk_manager: Optional[object]
) -> dict:
    """
    Execute a TradingView webhook signal.

    Args:
        signal: Signal dictionary from database
        broker_client: Optional broker client for live trading
        risk_manager: Optional risk manager for validation

    Returns:
        Result dictionary with execution status
    """
    symbol = signal["symbol"]
    action = signal["action"].lower()
    quantity = signal.get("quantity")
    price = signal.get("price")

    # If no quantity specified, use default allocation
    if not quantity:
        positions = port.get_positions()
        cash = port.get_cash()
        total_val = cash + sum(pos["shares"] * (price or pos["avg_cost"]) for pos in positions.values())

        if action == "buy":
            alloc = total_val * ALLOCATION_PER_STOCK
            if price:
                quantity = alloc / price
            else:
                logger.error(f"TradingView signal missing price for BUY: {signal}")
                port.mark_signal_processed(signal["id"], rejection_reason="Missing price for BUY order")
                return {"status": "rejected", "reason": "Missing price"}
        elif action == "sell":
            position = positions.get(symbol)
            if position:
                quantity = position["shares"]
            else:
                port.mark_signal_processed(signal["id"], rejection_reason="No position to sell")
                return {"status": "rejected", "reason": "No position to sell"}

    # Get current price if not provided
    if not price:
        from .data_feed import get_current_prices
        prices = get_current_prices([symbol])
        price = prices.get(symbol)
        if not price:
            port.mark_signal_processed(signal["id"], rejection_reason="Could not get current price")
            return {"status": "rejected", "reason": "Could not get current price"}

    # Execute the order
    strategy_name = signal.get("strategy", "tradingview")
    result = _execute_order(
        symbol, action, quantity, price,
        f"TradingView signal: {strategy_name}",
        broker_client, risk_manager, strategy_name
    )

    if result:
        # Mark signal as processed with order ID
        order_id = result.get("broker_order_id")
        port.mark_signal_processed(signal["id"], order_id=order_id)
        return {"status": "executed", "result": result}
    else:
        port.mark_signal_processed(signal["id"], rejection_reason="Order execution failed")
        return {"status": "failed", "reason": "Order execution failed"}
