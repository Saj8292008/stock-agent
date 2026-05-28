"""
Alpaca broker API client for live trade execution.

This module provides a unified interface to the Alpaca brokerage API,
supporting both paper trading and live trading modes.
"""

import logging
import time
from typing import Dict, List, Optional, Literal
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)


class AlpacaBrokerClient:
    """
    Client for interacting with Alpaca brokerage API.

    Supports both paper trading (default) and live trading modes.
    Handles order submission, account queries, and position management.
    """

    PAPER_BASE_URL = "https://paper-api.alpaca.markets"
    LIVE_BASE_URL = "https://api.alpaca.markets"
    DATA_URL = "https://data.alpaca.markets"

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        paper_mode: bool = True
    ):
        """
        Initialize the Alpaca broker client.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            paper_mode: If True, use paper trading endpoint; if False, use live
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.paper_mode = paper_mode
        self.base_url = self.PAPER_BASE_URL if paper_mode else self.LIVE_BASE_URL

        logger.info(f"Initialized AlpacaBrokerClient in {'PAPER' if paper_mode else 'LIVE'} mode")

    def _headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        return {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
            "accept": "application/json",
            "content-type": "application/json"
        }

    def _get(self, endpoint: str) -> Optional[dict]:
        """
        Make a GET request to Alpaca API.

        Args:
            endpoint: API endpoint path (e.g., '/v2/account')

        Returns:
            JSON response or None on failure
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self._headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GET {endpoint} failed: {e}")
            return None

    def _post(self, endpoint: str, payload: dict) -> Optional[dict]:
        """
        Make a POST request to Alpaca API.

        Args:
            endpoint: API endpoint path
            payload: JSON payload

        Returns:
            JSON response or None on failure
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, json=payload, headers=self._headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"POST {endpoint} failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None

    def _delete(self, endpoint: str) -> bool:
        """
        Make a DELETE request to Alpaca API.

        Args:
            endpoint: API endpoint path

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.delete(url, headers=self._headers(), timeout=10)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"DELETE {endpoint} failed: {e}")
            return False

    def get_account(self) -> Optional[dict]:
        """
        Get account information.

        Returns:
            Dictionary with account details including:
            - cash: Available cash
            - buying_power: Buying power
            - portfolio_value: Total portfolio value
            - equity: Account equity
            Or None on failure
        """
        data = self._get("/v2/account")
        if not data:
            return None

        return {
            "cash": float(data.get("cash", 0)),
            "buying_power": float(data.get("buying_power", 0)),
            "portfolio_value": float(data.get("portfolio_value", 0)),
            "equity": float(data.get("equity", 0)),
            "daytrade_count": int(data.get("daytrade_count", 0)),
            "account_blocked": data.get("account_blocked", False),
            "trading_blocked": data.get("trading_blocked", False),
        }

    def get_positions(self) -> List[dict]:
        """
        Get all current positions.

        Returns:
            List of position dictionaries with:
            - symbol: Stock symbol
            - qty: Quantity held
            - avg_entry_price: Average entry price
            - market_value: Current market value
            - unrealized_pl: Unrealized profit/loss
        """
        data = self._get("/v2/positions")
        if not data:
            return []

        positions = []
        for pos in data:
            positions.append({
                "symbol": pos.get("symbol"),
                "qty": float(pos.get("qty", 0)),
                "avg_entry_price": float(pos.get("avg_entry_price", 0)),
                "market_value": float(pos.get("market_value", 0)),
                "unrealized_pl": float(pos.get("unrealized_pl", 0)),
                "unrealized_plpc": float(pos.get("unrealized_plpc", 0)),
                "side": pos.get("side"),
            })
        return positions

    def submit_market_order(
        self,
        symbol: str,
        qty: float,
        side: Literal["buy", "sell"],
        time_in_force: str = "day"
    ) -> Optional[dict]:
        """
        Submit a market order.

        Args:
            symbol: Stock symbol
            qty: Quantity to buy/sell
            side: "buy" or "sell"
            time_in_force: Order duration (day, gtc, ioc, fok)

        Returns:
            Order object with order details or None on failure
        """
        payload = {
            "symbol": symbol.upper(),
            "qty": qty,
            "side": side,
            "type": "market",
            "time_in_force": time_in_force
        }

        logger.info(f"Submitting market order: {side.upper()} {qty} {symbol}")
        data = self._post("/v2/orders", payload)

        if not data:
            return None

        return {
            "order_id": data.get("id"),
            "symbol": data.get("symbol"),
            "side": data.get("side"),
            "type": data.get("type"),
            "qty": float(data.get("qty", 0)),
            "status": data.get("status"),
            "submitted_at": data.get("submitted_at"),
            "filled_at": data.get("filled_at"),
            "filled_qty": float(data.get("filled_qty", 0)),
            "filled_avg_price": float(data.get("filled_avg_price", 0)) if data.get("filled_avg_price") else None,
        }

    def submit_limit_order(
        self,
        symbol: str,
        qty: float,
        side: Literal["buy", "sell"],
        limit_price: float,
        time_in_force: str = "day"
    ) -> Optional[dict]:
        """
        Submit a limit order.

        Args:
            symbol: Stock symbol
            qty: Quantity to buy/sell
            side: "buy" or "sell"
            limit_price: Limit price
            time_in_force: Order duration (day, gtc, ioc, fok)

        Returns:
            Order object with order details or None on failure
        """
        payload = {
            "symbol": symbol.upper(),
            "qty": qty,
            "side": side,
            "type": "limit",
            "limit_price": limit_price,
            "time_in_force": time_in_force
        }

        logger.info(f"Submitting limit order: {side.upper()} {qty} {symbol} @ ${limit_price}")
        data = self._post("/v2/orders", payload)

        if not data:
            return None

        return {
            "order_id": data.get("id"),
            "symbol": data.get("symbol"),
            "side": data.get("side"),
            "type": data.get("type"),
            "qty": float(data.get("qty", 0)),
            "limit_price": float(data.get("limit_price", 0)),
            "status": data.get("status"),
            "submitted_at": data.get("submitted_at"),
        }

    def submit_stop_loss(
        self,
        symbol: str,
        qty: float,
        stop_price: float,
        time_in_force: str = "gtc"
    ) -> Optional[dict]:
        """
        Submit a stop-loss order.

        Args:
            symbol: Stock symbol
            qty: Quantity to sell
            stop_price: Stop price
            time_in_force: Order duration (day, gtc)

        Returns:
            Order object with order details or None on failure
        """
        payload = {
            "symbol": symbol.upper(),
            "qty": qty,
            "side": "sell",
            "type": "stop",
            "stop_price": stop_price,
            "time_in_force": time_in_force
        }

        logger.info(f"Submitting stop-loss order: SELL {qty} {symbol} @ stop ${stop_price}")
        data = self._post("/v2/orders", payload)

        if not data:
            return None

        return {
            "order_id": data.get("id"),
            "symbol": data.get("symbol"),
            "side": data.get("side"),
            "type": data.get("type"),
            "qty": float(data.get("qty", 0)),
            "stop_price": float(data.get("stop_price", 0)),
            "status": data.get("status"),
            "submitted_at": data.get("submitted_at"),
        }

    def get_order_status(self, order_id: str) -> Optional[dict]:
        """
        Get the status of an order.

        Args:
            order_id: Alpaca order ID

        Returns:
            Order status dictionary or None on failure
        """
        data = self._get(f"/v2/orders/{order_id}")
        if not data:
            return None

        return {
            "order_id": data.get("id"),
            "status": data.get("status"),
            "filled_qty": float(data.get("filled_qty", 0)),
            "filled_avg_price": float(data.get("filled_avg_price", 0)) if data.get("filled_avg_price") else None,
            "filled_at": data.get("filled_at"),
            "canceled_at": data.get("canceled_at"),
        }

    def wait_for_fill(self, order_id: str, timeout: int = 60, poll_interval: float = 1.0) -> Optional[dict]:
        """
        Wait for an order to be filled or rejected.

        Args:
            order_id: Alpaca order ID
            timeout: Maximum seconds to wait
            poll_interval: Seconds between status checks

        Returns:
            Final order status or None on timeout
        """
        start_time = time.time()

        while (time.time() - start_time) < timeout:
            status = self.get_order_status(order_id)

            if not status:
                logger.error(f"Failed to get status for order {order_id}")
                return None

            order_status = status.get("status")

            if order_status in ["filled", "canceled", "expired", "rejected"]:
                logger.info(f"Order {order_id} reached terminal state: {order_status}")
                return status

            time.sleep(poll_interval)

        logger.warning(f"Order {order_id} did not fill within {timeout}s")
        return None

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pending order.

        Args:
            order_id: Alpaca order ID

        Returns:
            True if successfully canceled, False otherwise
        """
        logger.info(f"Canceling order {order_id}")
        return self._delete(f"/v2/orders/{order_id}")

    def close_all_positions(self) -> bool:
        """
        Close all open positions (emergency kill switch).

        Returns:
            True if successful, False otherwise
        """
        logger.warning("CLOSING ALL POSITIONS (EMERGENCY STOP)")
        return self._delete("/v2/positions")

    def get_latest_quote(self, symbol: str) -> Optional[dict]:
        """
        Get the latest quote for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Quote dictionary with bid/ask or None on failure
        """
        url = f"{self.DATA_URL}/v2/stocks/{symbol.upper()}/quotes/latest"
        try:
            response = requests.get(url, headers=self._headers(), timeout=10)
            response.raise_for_status()
            data = response.json()

            if "quote" in data:
                quote = data["quote"]
                return {
                    "symbol": symbol,
                    "bid_price": float(quote.get("bp", 0)),
                    "ask_price": float(quote.get("ap", 0)),
                    "bid_size": int(quote.get("bs", 0)),
                    "ask_size": int(quote.get("as", 0)),
                    "timestamp": quote.get("t"),
                }
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            return None

    def get_latest_trade(self, symbol: str) -> Optional[dict]:
        """
        Get the latest trade for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Trade dictionary with price/size or None on failure
        """
        url = f"{self.DATA_URL}/v2/stocks/{symbol.upper()}/trades/latest"
        try:
            response = requests.get(url, headers=self._headers(), timeout=10)
            response.raise_for_status()
            data = response.json()

            if "trade" in data:
                trade = data["trade"]
                return {
                    "symbol": symbol,
                    "price": float(trade.get("p", 0)),
                    "size": int(trade.get("s", 0)),
                    "timestamp": trade.get("t"),
                }
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get trade for {symbol}: {e}")
            return None
