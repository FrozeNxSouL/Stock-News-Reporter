"""
Pydantic models for news analysis and sentiment.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SentimentScore(BaseModel):
    """NLP sentiment analysis result."""
    polarity: float = 0.0  # -1.0 to 1.0
    subjectivity: float = 0.0  # 0.0 to 1.0
    label: str = "neutral"  # positive, negative, neutral


class ImpactAssessment(BaseModel):
    """Assessed impact on the stock."""
    direction: str = "neutral"  # up, down, neutral
    strength: str = "low"  # low, medium, high
    effect_duration: str = "short-term"  # short-term, medium-term, long-term
    price_range_low: float = -5.0  # percentage range low
    price_range_high: float = 5.0  # percentage range high
    confidence: float = 0.5  # 0.0 to 1.0
    reasoning: str = ""


class NewsAnalysisCreate(BaseModel):
    news_id: str
    ticker: str
    sentiment: SentimentScore
    impact: ImpactAssessment
    relevance_score: float = 0.0  # 0.0 to 1.0 how directly relevant
    keywords: List[str] = []


class NewsAnalysisInDB(NewsAnalysisCreate):
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
        populate_by_name = True


class NewsAnalysisResponse(NewsAnalysisCreate):
    id: str = Field(alias="_id")
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StockPricePoint(BaseModel):
    """Single stock price data point."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockPriceResponse(BaseModel):
    ticker: str
    current_price: float
    change: float
    change_percent: float
    day_high: float
    day_low: float
    volume: int
    historical: List[StockPricePoint] = []
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TickerOverview(BaseModel):
    """Combined view of ticker with latest news and analysis."""
    symbol: str
    name: str
    current_price: Optional[StockPriceResponse] = None
    recent_news: List[dict] = []
    sentiment_summary: Optional[dict] = None
