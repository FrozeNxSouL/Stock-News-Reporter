"""
Stock News Analyzer - FastAPI Backend
Main application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import Database
from config import settings
import uvicorn

# Import routes
from routes.tickers import router as tickers_router
from routes.news import router as news_router
from routes.analysis import router as analysis_router
from routes.stocks import router as stocks_router
from routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: connect/disconnect MongoDB."""
    # Startup
    await Database.connect()
    yield
    # Shutdown
    await Database.disconnect()


app = FastAPI(
    title="Stock News Analyzer API",
    description="Backend API for aggregating stock market news, "
                "analyzing sentiment, and tracking stock prices.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(tickers_router)
app.include_router(news_router)
app.include_router(analysis_router)
app.include_router(stocks_router)


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "app": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected" if Database.client else "disconnected",
    }


def main():
    """Run the application."""
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
