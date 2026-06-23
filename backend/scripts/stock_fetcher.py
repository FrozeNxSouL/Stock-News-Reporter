"""
Stock price data fetcher with fallback mechanism.
Primary: yfinance library
Fallback: Direct Yahoo Finance Chart API via HTTP
"""
import asyncio
from datetime import datetime, timezone
from typing import List, Optional

import httpx
import yfinance as yf
from models.analysis import StockPricePoint, StockPriceResponse


# ─── Direct Yahoo Finance API (fallback) ───

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


async def _fetch_via_direct_api(ticker: str) -> Optional[StockPriceResponse]:
    """Fallback: fetch stock data directly from Yahoo Finance Chart API.

    The v8/chart endpoint is generally more stable than the quote API
    that yfinance uses internally.
    """
    try:
        async with httpx.AsyncClient(
            timeout=15.0, headers=HEADERS, follow_redirects=True
        ) as client:
            url = YAHOO_CHART_URL.format(ticker=ticker)
            params = {
                "range": "1mo",
                "interval": "1d",
                "includePrePost": "false",
            }
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        chart = data.get("chart", {})
        result_list = chart.get("result", [])
        if not result_list:
            print(f"[Stock] No chart data for {ticker}")
            return None

        result = result_list[0]
        meta = result.get("meta", {})
        timestamps = result.get("timestamp", [])
        indicators = result.get("indicators", {}).get("quote", [{}])[0]

        opens = indicators.get("open", [])
        highs = indicators.get("high", [])
        lows = indicators.get("low", [])
        closes = indicators.get("close", [])
        volumes = indicators.get("volume", [])

        if not timestamps or not closes:
            print(f"[Stock] No price data for {ticker}")
            return None

        # Current price from meta or latest close
        current_price = meta.get("regularMarketPrice")
        if current_price is None:
            valid_closes = [c for c in closes if c is not None]
            current_price = valid_closes[-1] if valid_closes else 0

        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
        if prev_close is None:
            valid_closes = [c for c in closes if c is not None]
            prev_close = valid_closes[-2] if len(valid_closes) > 1 else current_price

        change = float(current_price) - float(prev_close)
        change_percent = (change / float(prev_close)) * 100 if prev_close else 0

        day_high = meta.get("regularMarketDayHigh")
        if day_high is None:
            valid_highs = [h for h in highs if h is not None]
            day_high = max(valid_highs) if valid_highs else current_price

        day_low = meta.get("regularMarketDayLow")
        if day_low is None:
            valid_lows = [l for l in lows if l is not None]
            day_low = min(valid_lows) if valid_lows else current_price

        volume = meta.get("regularMarketVolume")
        if volume is None and volumes and volumes[-1] is not None:
            volume = int(volumes[-1])
        elif volume is None:
            volume = 0

        # Historical data points
        historical = []
        for i in range(len(timestamps)):
            if (
                i < len(opens) and opens[i] is not None
                and i < len(closes) and closes[i] is not None
            ):
                historical.append(StockPricePoint(
                    timestamp=datetime.fromtimestamp(timestamps[i], tz=timezone.utc),
                    open=float(opens[i]),
                    high=float(highs[i]) if highs[i] else float(opens[i]),
                    low=float(lows[i]) if lows[i] else float(opens[i]),
                    close=float(closes[i]),
                    volume=int(volumes[i]) if (volumes and volumes[i]) else 0,
                ))

        return StockPriceResponse(
            ticker=ticker.upper(),
            current_price=round(float(current_price), 2),
            change=round(float(change), 2),
            change_percent=round(float(change_percent), 2),
            day_high=round(float(day_high), 2),
            day_low=round(float(day_low), 2),
            volume=int(volume),
            historical=historical,
            updated_at=datetime.now(timezone.utc),
        )

    except Exception as e:
        print(f"[Stock] Direct API fallback failed for {ticker}: {e}")
        return None


# ─── Primary: yfinance with retry ───

async def _fetch_via_yfinance(ticker: str) -> Optional[StockPriceResponse]:
    """Primary: fetch stock data using yfinance library.

    yfinance runs blocking I/O, so we run it in a thread pool
    to avoid blocking the async event loop.
    """
    try:
        stock = yf.Ticker(ticker)
        loop = asyncio.get_event_loop()

        # history() is blocking — run in executor
        hist = await loop.run_in_executor(
            None, lambda: stock.history(period="1mo", interval="1d")
        )

        if hist is None or hist.empty:
            print(f"[Stock] No data for {ticker} via yfinance (empty history)")
            return None

        # .info may throw on network errors — handle gracefully
        info = {}
        try:
            info = await loop.run_in_executor(None, lambda: stock.info or {})
        except Exception as exc:
            print(f"[Stock] yfinance .info failed for {ticker}: {exc}")

        current_price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or float(hist["Close"].iloc[-1])
        )

        prev_close = (
            info.get("previousClose")
            or (float(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price)
        )
        change = float(current_price) - float(prev_close)
        change_percent = (change / float(prev_close)) * 100 if prev_close else 0

        day_high = info.get("dayHigh") or float(hist["High"].iloc[-1])
        day_low = info.get("dayLow") or float(hist["Low"].iloc[-1])
        volume = info.get("volume") or int(hist["Volume"].iloc[-1])

        historical = []
        for date, row in hist.iterrows():
            historical.append(StockPricePoint(
                timestamp=date.to_pydatetime().replace(tzinfo=timezone.utc),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=int(row["Volume"]),
            ))

        return StockPriceResponse(
            ticker=ticker.upper(),
            current_price=round(float(current_price), 2),
            change=round(float(change), 2),
            change_percent=round(float(change_percent), 2),
            day_high=round(float(day_high), 2),
            day_low=round(float(day_low), 2),
            volume=int(volume),
            historical=historical,
            updated_at=datetime.now(timezone.utc),
        )

    except Exception as e:
        print(f"[Stock] yfinance error for {ticker}: {e}")
        return None


# ─── Public API ───

async def fetch_current_price(ticker: str) -> Optional[StockPriceResponse]:
    """Fetch current stock price and recent history for a ticker.

    Strategy:
      1. Try yfinance library (primary).
      2. If that fails, fall back to the direct Yahoo Finance Chart API.
    """
    result = await _fetch_via_yfinance(ticker)
    if result and result.current_price > 0:
        return result

    print(f"[Stock] yfinance failed for {ticker}, trying direct API fallback …")
    await asyncio.sleep(0.5)  # brief cooldown before fallback

    result = await _fetch_via_direct_api(ticker)
    if result and result.current_price > 0:
        return result

    print(f"[Stock] All methods failed for {ticker}")
    return None


async def fetch_multiple_prices(tickers: List[str]) -> List[StockPriceResponse]:
    """Fetch prices for multiple tickers concurrently."""
    tasks = [fetch_current_price(ticker) for ticker in tickers]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]


# ─── Ticker Search / Lookup ───

YAHOO_SEARCH_URLS = [
    "https://query2.finance.yahoo.com/v1/finance/search",
    "https://query1.finance.yahoo.com/v1/finance/search",
]


async def search_tickers(query: str) -> List[dict]:
    """Search for tickers by symbol or company name via Yahoo Finance search.

    Tries multiple endpoints with delay between retries. Returns a list
    of dicts with keys: symbol, name, exchange, sector. Silent on failure.
    """
    q = query.strip()
    if not q:
        return []

    params = {"q": q, "quotesCount": 8, "newsCount": 0}

    for i, url in enumerate(YAHOO_SEARCH_URLS):
        if i > 0:
            await asyncio.sleep(1.0)

        try:
            async with httpx.AsyncClient(
                timeout=8.0, headers=HEADERS, follow_redirects=True
            ) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

            results = []
            for quote in data.get("quotes", []):
                symbol = quote.get("symbol", "")
                if not symbol:
                    continue
                equity_type = quote.get("quoteType", "").lower()
                if equity_type and equity_type not in ("equity", "etf", ""):
                    continue

                results.append({
                    "symbol": symbol,
                    "name": quote.get("shortname") or quote.get("longname") or "",
                    "exchange": quote.get("exchange", ""),
                    "sector": quote.get("sector", ""),
                })

            if results:
                return results
        except Exception:
            continue  # silent — search is best-effort

    return []


async def lookup_ticker_info(ticker: str) -> Optional[dict]:
    """Look up a single ticker's info (name, sector, exchange).

    Uses yfinance as primary, falls back to search API.
    """
    ticker = ticker.strip().upper()
    if not ticker:
        return None

    # Try yfinance first
    try:
        stock = yf.Ticker(ticker)
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: stock.info or {})
        if info and info.get("shortName") or info.get("longName"):
            return {
                "symbol": ticker,
                "name": info.get("shortName") or info.get("longName") or "",
                "exchange": info.get("exchange", ""),
                "sector": info.get("sector", ""),
            }
    except Exception as e:
        print(f"[Stock] yfinance lookup failed for {ticker}: {e}")

    # Fallback: use search API with exact ticker — brief cooldown first
    await asyncio.sleep(1.0)
    results = await search_tickers(ticker)
    for r in results:
        if r["symbol"].upper() == ticker:
            return r

    # If search didn't return exact match, try broader search
    await asyncio.sleep(0.3)
    results = await search_tickers(ticker)
    for r in results:
        if r["symbol"].upper() == ticker:
            return r

    return None
