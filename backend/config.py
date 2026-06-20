"""
Application configuration loaded from environment variables.
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # App
    app_name: str = "Stock News Analyzer"
    debug: bool = True

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db: str = "stock_news_db"

    # JWT Authentication
    jwt_secret_key: str = "change-me-in-production-use-a-strong-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Stock price refresh interval (seconds)
    stock_refresh_interval: int = 60

    # News scraping interval (minutes)
    news_scrape_interval: int = 15

    # Default RSS feed sources
    default_rss_feeds: List[str] = [
        "https://finance.yahoo.com/news/rssindex",
        "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://feeds.marketwatch.com/marketwatch/marketpulse/",
        "https://www.investing.com/rss/news.rss",
        "https://seekingalpha.com/feed.xml",
    ]

    # Tickers to scrape additional web content for
    default_tickers: List[str] = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META",
        "NVDA", "TSLA", "JPM", "V", "SPY"
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
