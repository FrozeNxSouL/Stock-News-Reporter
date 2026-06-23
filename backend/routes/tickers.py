"""
API routes for ticker management.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from database import Database
from models.ticker import TickerCreate, TickerUpdate, TickerResponse
from scripts.stock_fetcher import lookup_ticker_info
from config import settings

router = APIRouter(prefix="/api/tickers", tags=["Tickers"])


@router.get("/", response_model=List[TickerResponse])
async def list_tickers(active: Optional[bool] = None):
    """List all tracked tickers."""
    db = Database.tickers
    query = {}
    if active is not None:
        query["active"] = active

    cursor = db.find(query).sort("symbol", 1)
    tickers = await cursor.to_list(length=1000)

    # Convert _id to string
    result = []
    for t in tickers:
        t["_id"] = str(t["_id"])
        result.append(TickerResponse(**t))

    return result


@router.post("/", response_model=TickerResponse, status_code=201)
async def create_ticker(ticker: TickerCreate):
    """Add a new ticker to track."""
    db = Database.tickers

    # Check if already exists
    existing = await db.find_one({"symbol": ticker.symbol.upper()})
    if existing:
        raise HTTPException(status_code=400, detail=f"Ticker {ticker.symbol} already exists")

    doc = ticker.model_dump()
    doc["symbol"] = doc["symbol"].upper()
    doc["created_at"] = datetime.now(timezone.utc)
    doc["updated_at"] = datetime.now(timezone.utc)

    # Auto-fill name/sector from Yahoo Finance if not provided
    if not doc.get("name") and not doc.get("sector"):
        info = await lookup_ticker_info(doc["symbol"])
        if info:
            doc["name"] = info.get("name", "")
            doc["sector"] = info.get("sector", "")

    result = await db.insert_one(doc)
    doc["_id"] = str(result.inserted_id)

    return TickerResponse(**doc)


@router.get("/defaults", status_code=201)
async def add_default_tickers():
    """Add default tickers to database."""
    db = Database.tickers
    added = 0

    for symbol in settings.default_tickers:
        existing = await db.find_one({"symbol": symbol})
        if not existing:
            doc = {
                "symbol": symbol,
                "name": "",
                "sector": "",
                "active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            await db.insert_one(doc)
            added += 1

    return {"message": f"Added {added} default tickers", "added": added}


@router.delete("/{symbol}", status_code=204)
async def delete_ticker(symbol: str):
    """Remove a ticker."""
    db = Database.tickers
    result = await db.delete_one({"symbol": symbol.upper()})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return None
