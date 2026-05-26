import logging
from typing import Dict, List

import yfinance as yf

logger = logging.getLogger(__name__)


def get_current_prices(symbols: List[str]) -> Dict[str, float]:
    prices: Dict[str, float] = {}
    for symbol in symbols:
        try:
            info = yf.Ticker(symbol).fast_info
            price = getattr(info, "last_price", None) or getattr(info, "regular_market_price", None)
            if price:
                prices[symbol] = float(price)
        except Exception as e:
            logger.warning(f"Price fetch failed for {symbol}: {e}")
    return prices


def get_price_history(symbol: str, period: str = "1mo") -> List[dict]:
    try:
        hist = yf.Ticker(symbol).history(period=period)
        return [
            {"date": str(idx.date()), "close": round(float(row["Close"]), 4)}
            for idx, row in hist.iterrows()
        ]
    except Exception as e:
        logger.warning(f"History fetch failed for {symbol}: {e}")
        return []
