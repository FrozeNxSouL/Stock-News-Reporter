"""
API routes for stock price data.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from datetime import datetime, timezone
from database import Database
from models.analysis import StockPriceResponse, StockPricePoint
from scripts.stock_fetcher import (
    fetch_current_price,
    fetch_multiple_prices,
    search_tickers,
    lookup_ticker_info,
)
from config import settings

router = APIRouter(prefix="/api/stocks", tags=["Stocks"])


# ── Explicit routes MUST come before /{ticker} wildcard ──────────

@router.get("/search")
async def search_stocks(q: str = Query(..., min_length=1, description="Search query"),):
    """
    Search for tickers by symbol or company name.
    Returns matching tickers with symbol, name, exchange, and sector.
    """
    results = await search_tickers(q)
    return {"results": results}


@router.get("/lookup/{ticker}")
async def lookup_ticker(ticker: str):
    """
    Look up a single ticker to verify it exists and get its info.
    Returns symbol, name, exchange, sector.
    """
    info = await lookup_ticker_info(ticker)
    if not info:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")
    return info


@router.get("/")
async def get_multiple_prices(
    tickers: str = Query(..., description="Comma-separated list of tickers"),
):
    """
    Get stock prices for multiple tickers at once.
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    prices = await fetch_multiple_prices(ticker_list)

    db = Database.stock_prices
    for price in prices:
        if price.current_price > 0:
            doc = price.model_dump()
            doc["timestamp"] = datetime.now(timezone.utc)
            await db.insert_one(doc)

    return {"prices": [p.model_dump() for p in prices]}


# ── Wildcard: /{ticker} MUST be last ─────────────────────────────

@router.get("/{ticker}", response_model=StockPriceResponse)
async def get_stock_price(ticker: str):
    """
    Get current stock price and historical data for a ticker.
    Fetches live data from yfinance with a direct API fallback.
    """
    ticker = ticker.upper()
    price_data = await fetch_current_price(ticker)

    if not price_data:
        return StockPriceResponse(
            ticker=ticker,
            current_price=0,
            change=0,
            change_percent=0,
            day_high=0,
            day_low=0,
            volume=0,
            historical=[],
            updated_at=datetime.now(timezone.utc),
        )

    # Cache price data in MongoDB
    db = Database.stock_prices
    doc = price_data.model_dump()
    doc["timestamp"] = datetime.now(timezone.utc)
    await db.insert_one(doc)

    # Keep only last 1000 price snapshots per ticker
    count = await db.count_documents({"ticker": ticker})
    if count > 1000:
        cursor = db.find({"ticker": ticker}).sort("timestamp", 1).limit(count - 1000)
        old_docs = await cursor.to_list(length=count - 1000)
        for old in old_docs:
            await db.delete_one({"_id": old["_id"]})

    return price_data
