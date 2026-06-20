"""
RSS Feed scraper using feedparser.
Fetches news from financial RSS feeds and extracts articles.
"""
import feedparser
import hashlib
from datetime import datetime, timezone
from typing import List, Optional
from bs4 import BeautifulSoup
import re
from models.news import NewsCreate


# Common stock ticker patterns (NYSE, NASDAQ)
TICKER_PATTERN = re.compile(
    r'\b([A-Z]{1,5})\b'
)

# Stock-specific keywords to match tickers contextually
STOCK_KEYWORDS = {
    'stock', 'shares', 'trading', 'market', 'NYSE', 'NASDAQ',
    'bullish', 'bearish', 'earnings', 'dividend', 'IPO',
    'SEC', 'filing', 'quarterly', 'revenue', 'profit',
}


def extract_tickers(text: str) -> List[str]:
    """
    Extract potential ticker symbols from text.
    Uses heuristics: uppercase 1-5 letter words that appear
    in financial context.
    """
    if not text:
        return []

    potential = set(TICKER_PATTERN.findall(text))
    # Filter out common false positives
    false_positives = {
        'THE', 'FOR', 'AND', 'ARE', 'NOT', 'YOU', 'ITS', 'HAS',
        'WAS', 'BUT', 'ALL', 'CAN', 'NEW', 'HOW', 'WHO', 'WHY',
        'INC', 'LTD', 'CEO', 'CFO', 'USA', 'ETF',
    }
    return [t for t in potential if t not in false_positives and len(t) > 1]


def clean_html(html_text: str) -> str:
    """Remove HTML tags and clean text."""
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, 'lxml')
    return soup.get_text(separator=' ', strip=True)


def parse_rss_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse RSS date string to datetime."""
    if not date_str:
        return None
    try:
        # feedparser handles many formats via _parse_date
        parsed = feedparser._parse_date(date_str)
        if parsed:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
    except Exception:
        pass
    return None


async def fetch_rss_feed(feed_url: str) -> List[NewsCreate]:
    """
    Fetch and parse a single RSS feed.
    Returns list of NewsCreate objects.
    """
    try:
        feed = feedparser.parse(feed_url)
        articles = []

        for entry in feed.entries[:50]:  # Limit to 50 per feed
            title = entry.get('title', '')
            link = entry.get('link', '')

            if not title or not link:
                continue

            # Get summary/content
            summary = ''
            if 'summary' in entry:
                summary = clean_html(entry.summary)
            elif 'description' in entry:
                summary = clean_html(entry.description)

            content = ''
            if 'content' in entry:
                for c in entry.content:
                    if c.get('value'):
                        content += clean_html(c.value)

            published = parse_rss_date(entry.get('published'))

            # Extract tickers from title and summary
            text_for_tickers = f"{title} {summary} {content}"
            tickers = extract_tickers(text_for_tickers)

            source_name = feed.feed.get('title', feed_url)

            article = NewsCreate(
                title=title[:500],
                url=link,
                source=source_name,
                summary=summary[:2000],
                content=content[:5000],
                tickers=tickers,
                published=published,
                source_type='rss',
            )
            articles.append(article)

        print(f"[RSS] Fetched {len(articles)} articles from {feed_url}")
        return articles

    except Exception as e:
        print(f"[RSS] Error fetching {feed_url}: {e}")
        return []


async def fetch_all_feeds(feed_urls: List[str]) -> List[NewsCreate]:
    """Fetch all RSS feeds concurrently."""
    import asyncio
    tasks = [fetch_rss_feed(url) for url in feed_urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_articles = []
    for result in results:
        if isinstance(result, list):
            all_articles.extend(result)

    # Deduplicate by URL
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        if article.url not in seen_urls:
            seen_urls.add(article.url)
            unique_articles.append(article)

    print(f"[RSS] Total unique articles: {len(unique_articles)}")
    return unique_articles
