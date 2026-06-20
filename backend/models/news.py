"""
Pydantic models for news articles.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class NewsBase(BaseModel):
    title: str
    url: str
    source: str = ""
    summary: str = ""
    content: str = ""
    tickers: List[str] = []
    published: Optional[datetime] = None
    source_type: str = "rss"  # 'rss' or 'scrape'


class NewsCreate(NewsBase):
    pass


class NewsInDB(NewsBase):
    id: str = Field(alias="_id")
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
        populate_by_name = True


class NewsResponse(NewsBase):
    id: str = Field(alias="_id")
    fetched_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NewsListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[NewsResponse]
