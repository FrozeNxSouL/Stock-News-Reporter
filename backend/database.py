"""
Async MongoDB connection using Motor.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel
from config import settings


class Database:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect(cls):
        """Initialize MongoDB connection."""
        cls.client = AsyncIOMotorClient(settings.mongodb_url)
        cls.db = cls.client[settings.mongodb_db]
        # Create indexes
        await cls._ensure_indexes()
        print(f"[DB] Connected to MongoDB: {settings.mongodb_db}")

    @classmethod
    async def disconnect(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            print("[DB] Disconnected from MongoDB")

    @classmethod
    async def _ensure_indexes(cls):
        """Create required indexes for performance."""
        await cls.db.news.create_indexes([
            IndexModel([("ticker", 1), ("published", -1)]),
            IndexModel([("url", 1)], unique=True),
        ])
        await cls.db.tickers.create_indexes([
            IndexModel([("symbol", 1)], unique=True),
        ])
        await cls.db.analysis.create_indexes([
            IndexModel([("news_id", 1)]),
            IndexModel([("ticker", 1), ("created_at", -1)]),
        ])
        await cls.db.stock_prices.create_indexes([
            IndexModel([("ticker", 1), ("timestamp", -1)]),
        ])
        await cls.db.users.create_indexes([
            IndexModel([("email", 1)], unique=True),
            IndexModel([("username", 1)], unique=True),
        ])

    # ---- Collections ----
    @classmethod
    def get_collection(cls, name: str):
        return cls.db[name]

    @classmethod
    @property
    def news(cls):
        return cls.db.news

    @classmethod
    @property
    def tickers(cls):
        return cls.db.tickers

    @classmethod
    @property
    def analysis(cls):
        return cls.db.analysis

    @classmethod
    @property
    def stock_prices(cls):
        return cls.db.stock_prices

    @classmethod
    @property
    def scrape_sources(cls):
        return cls.db.scrape_sources

    @classmethod
    @property
    def users(cls):
        return cls.db.users
