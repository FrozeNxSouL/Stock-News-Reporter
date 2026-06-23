"""
API routes for news articles.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from database import Database
from models.news import NewsResponse, NewsListResponse
from models.analysis import NewsAnalysisResponse

router = APIRouter(prefix="/api/news", tags=["News"])


@router.get("/", response_model=NewsListResponse)
async def list_news(
    ticker: Optional[str] = Query(None, description="Filter by ticker"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_type: Optional[str] = Query(None, description="rss or scrape"),
):
    """List news articles with optional filtering."""
    db = Database.news
    query = {}

    if ticker:
        query["tickers"] = ticker.upper()
    if source_type:
        query["source_type"] = source_type

    total = await db.count_documents(query)

    cursor = db.find(query).sort("published", -1).skip((page - 1) * page_size).limit(page_size)
    items = await cursor.to_list(length=page_size)

    result_items = []
    for item in items:
        item["_id"] = str(item["_id"])
        result_items.append(NewsResponse(**item))

    return NewsListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=result_items,
    )


@router.get("/{news_id}", response_model=NewsResponse)
async def get_news(news_id: str):
    """Get a single news article by ID."""
    from bson import ObjectId

    db = Database.news
    try:
        doc = await db.find_one({"_id": ObjectId(news_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid news ID")

    if not doc:
        raise HTTPException(status_code=404, detail="News not found")

    doc["_id"] = str(doc["_id"])
    return NewsResponse(**doc)


@router.get("/{news_id}/analysis", response_model=List[NewsAnalysisResponse])
async def get_news_analysis(news_id: str):
    """Get analysis for a specific news article."""
    db = Database.analysis
    cursor = db.find({"news_id": news_id})
    analyses = await cursor.to_list(length=100)

    result = []
    for a in analyses:
        a["_id"] = str(a["_id"])
        result.append(NewsAnalysisResponse(**a))

    return result
