"""
Stock price data fetcher using yfinance.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from models.analysis import StockPricePoint, StockPriceResponse


async def fetch_current_price(ticker: str) -> Optional[StockPriceResponse]:
    """
    Fetch current stock price and recent history for a ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo", interval="1d")

        if hist.empty:
            print(f"[Stock] No data for {ticker}")
            return None

        # Current price info
        info = stock.info or {}
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        if not current_price:
            current_price = float(hist['Close'].iloc[-1])

        prev_close = info.get('previousClose') or float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
        change = current_price - prev_close
        change_percent = (change / prev_close) * 100 if prev_close else 0

        day_high = info.get('dayHigh') or float(hist['High'].iloc[-1])
        day_low = info.get('dayLow') or float(hist['Low'].iloc[-1])
        volume = info.get('volume') or int(hist['Volume'].iloc[-1])

        # Historical data points
        historical = []
        for date, row in hist.iterrows():
            historical.append(StockPricePoint(
                timestamp=date.to_pydatetime().replace(tzinfo=timezone.utc),
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume']),
            ))

        return StockPriceResponse(
            ticker=ticker.upper(),
            current_price=round(current_price, 2),
            change=round(change, 2),
            change_percent=round(change_percent, 2),
            day_high=round(day_high, 2),
            day_low=round(day_low, 2),
            volume=int(volume),
            historical=historical,
            updated_at=datetime.now(timezone.utc),
        )

    except Exception as e:
        print(f"[Stock] Error fetching {ticker}: {e}")
        return None


async def fetch_multiple_prices(tickers: List[str]) -> List[StockPriceResponse]:
    """
    Fetch prices for multiple tickers.
    """
    results = []
    for ticker in tickers:
        price = await fetch_current_price(ticker)
        if price:
            results.append(price)
    return results
