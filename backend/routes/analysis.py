"""
API routes for aggregated analysis and dashboard data.
"""
from fastapi import APIRouter, Query
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from database import Database
from models.analysis import (
    NewsAnalysisResponse,
    TickerOverview,
    StockPriceResponse,
)

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


@router.get("/overview/{ticker}")
async def get_ticker_overview(
    ticker: str,
    days: int = Query(7, ge=1, le=30),
):
    """
    Get a comprehensive overview for a ticker including:
    - Recent news with sentiment analysis
    - Current stock price
    - Aggregated sentiment summary
    """
    ticker = ticker.upper()
    db_news = Database.news
    db_analysis = Database.analysis
    db_prices = Database.stock_prices

    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Get recent news for this ticker
    news_cursor = db_news.find(
        {"tickers": ticker, "published": {"$gte": since}}
    ).sort("published", -1).limit(50)
    recent_news = await news_cursor.to_list(length=50)

    news_with_analysis = []
    for article in recent_news:
        article["_id"] = str(article["_id"])

        # Get analysis for this news + ticker
        analysis = await db_analysis.find_one({
            "news_id": article["_id"],
            "ticker": ticker,
        })

        news_item = {
            "id": article["_id"],
            "title": article.get("title", ""),
            "url": article.get("url", ""),
            "source": article.get("source", ""),
            "summary": article.get("summary", ""),
            "published": article.get("published"),
            "source_type": article.get("source_type", ""),
        }

        if analysis:
            analysis["_id"] = str(analysis["_id"])
            news_item["analysis"] = {
                "sentiment": analysis.get("sentiment"),
                "impact": analysis.get("impact"),
                "relevance_score": analysis.get("relevance_score", 0),
                "keywords": analysis.get("keywords", []),
            }

        news_with_analysis.append(news_item)

    # Aggregate sentiment
    sentiment_summary = await aggregate_sentiment(ticker, days)

    # Get latest stock price
    price_doc = await db_prices.find_one(
        {"ticker": ticker},
        sort=[("timestamp", -1)]
    )

    current_price = None
    if price_doc:
        price_doc["_id"] = str(price_doc["_id"])
        current_price = StockPriceResponse(**price_doc)

    return {
        "symbol": ticker,
        "recent_news": news_with_analysis,
        "sentiment_summary": sentiment_summary,
        "current_price": current_price,
    }


@router.get("/sentiment/{ticker}")
async def get_ticker_sentiment(
    ticker: str,
    days: int = Query(7, ge=1, le=30),
):
    """Get aggregated sentiment analysis for a ticker over time."""
    return await aggregate_sentiment(ticker.upper(), days)


async def aggregate_sentiment(ticker: str, days: int) -> dict:
    """
    Aggregate sentiment data for a ticker.
    Returns summary statistics.
    """
    db_analysis = Database.analysis
    db_news = Database.news

    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Find news IDs for this ticker within date range
    news_cursor = db_news.find(
        {"tickers": ticker, "published": {"$gte": since}},
        {"_id": 1}
    )
    news_ids = []
    async for doc in news_cursor:
        news_ids.append(str(doc["_id"]))

    if not news_ids:
        return {
            "ticker": ticker,
            "total_articles": 0,
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
            "avg_polarity": 0,
            "avg_confidence": 0,
            "avg_relevance": 0,
            "dominant_direction": "neutral",
            "dominant_strength": "low",
            "recent_trend": "stable",
        }

    # Get all analyses for these news items
    cursor = db_analysis.find({
        "news_id": {"$in": news_ids},
        "ticker": ticker,
    })
    analyses = await cursor.to_list(length=500)

    if not analyses:
        return {
            "ticker": ticker,
            "total_articles": len(news_ids),
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
            "avg_polarity": 0,
            "avg_confidence": 0,
            "avg_relevance": 0,
            "dominant_direction": "neutral",
            "dominant_strength": "low",
            "recent_trend": "stable",
        }

    # Calculate aggregates
    polarities = []
    confidences = []
    relevances = []
    directions = {}
    strengths = {}
    sentiment_dist = {"positive": 0, "negative": 0, "neutral": 0}

    for a in analyses:
        sentiment = a.get("sentiment", {})
        impact = a.get("impact", {})

        polarities.append(sentiment.get("polarity", 0))
        confidences.append(impact.get("confidence", 0))
        relevances.append(a.get("relevance_score", 0))

        label = sentiment.get("label", "neutral")
        sentiment_dist[label] = sentiment_dist.get(label, 0) + 1

        direction = impact.get("direction", "neutral")
        directions[direction] = directions.get(direction, 0) + 1

        strength = impact.get("strength", "low")
        strengths[strength] = strengths.get(strength, 0) + 1

    avg_polarity = sum(polarities) / len(polarities) if polarities else 0
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    avg_relevance = sum(relevances) / len(relevances) if relevances else 0

    dominant_direction = max(directions, key=directions.get) if directions else "neutral"
    dominant_strength = max(strengths, key=strengths.get) if strengths else "low"

    # Determine recent trend (last vs first half)
    mid = len(analyses) // 2
    if mid > 0:
        first_half = [a.get("sentiment", {}).get("polarity", 0) for a in analyses[:mid]]
        second_half = [a.get("sentiment", {}).get("polarity", 0) for a in analyses[mid:]]
        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0
        diff = avg_second - avg_first
        if diff > 0.1:
            trend = "improving"
        elif diff < -0.1:
            trend = "deteriorating"
        else:
            trend = "stable"
    else:
        trend = "stable"

    return {
        "ticker": ticker,
        "total_articles": len(news_ids),
        "analyzed_articles": len(analyses),
        "sentiment_distribution": sentiment_dist,
        "avg_polarity": round(avg_polarity, 4),
        "avg_confidence": round(avg_confidence, 4),
        "avg_relevance": round(avg_relevance, 4),
        "dominant_direction": dominant_direction,
        "dominant_strength": dominant_strength,
        "recent_trend": trend,
    }
