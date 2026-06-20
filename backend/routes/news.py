"""
API routes for news articles.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone
from database import Database
from models.news import NewsResponse, NewsListResponse
from models.analysis import NewsAnalysisResponse
from scrapers.rss_scraper import fetch_all_feeds
from scrapers.playwright_scraper import scrape_all_sources
from scrapers.news_analyzer import analyze_news
from config import settings

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


@router.get("/fetch", status_code=200)
async def fetch_news():
    """
    Manually trigger news fetching from all sources.
    Fetches RSS feeds and scrapes websites.
    """
    # Fetch RSS feeds
    rss_articles = await fetch_all_feeds(settings.default_rss_feeds)

    # Scrape web sources
    scraped_articles = await scrape_all_sources(settings.default_tickers)

    all_articles = rss_articles + scraped_articles

    # Deduplicate by URL
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        if article.url not in seen_urls:
            seen_urls.add(article.url)
            unique_articles.append(article)

    # Save to database
    db = Database.news
    saved_count = 0

    for article in unique_articles:
        existing = await db.find_one({"url": article.url})
        if not existing:
            doc = article.model_dump()
            doc["fetched_at"] = datetime.now(timezone.utc)
            if not doc.get("published"):
                doc["published"] = datetime.now(timezone.utc)
            await db.insert_one(doc)
            saved_count += 1

    # Analyze saved articles
    analyzed_count = 0
    if saved_count > 0:
        # Get recently saved articles
        cursor = db.find().sort("fetched_at", -1).limit(saved_count)
        saved_articles = await cursor.to_list(length=saved_count)

        for article in saved_articles:
            analyses = await analyze_news(article)
            for analysis in analyses:
                analysis.news_id = str(article["_id"])
                analysis_db = Database.analysis
                await analysis_db.insert_one(analysis.model_dump())
                analyzed_count += 1

    return {
        "total_fetched": len(unique_articles),
        "new_saved": saved_count,
        "analyzed": analyzed_count,
    }


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
