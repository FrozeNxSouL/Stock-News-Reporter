"""
Web scraping module using Playwright.
Scrapes financial news websites that don't provide RSS feeds.
"""
import asyncio
import re
from datetime import datetime, timezone
from typing import List, Optional
from bs4 import BeautifulSoup
from models.news import NewsCreate
from scrapers.rss_scraper import extract_tickers

# Scraping targets (sites without good RSS)
SCRAPE_TARGETS = [
    {
        "name": "Finviz News",
        "url": "https://finviz.com/news.ashx",
        "type": "list",
        "article_selector": "a.sl",
        "title_selector": None,  # title is the link text
        "link_selector": None,   # href is the link
    },
    {
        "name": "StreetInsider",
        "url": "https://www.streetinsider.com/",
        "type": "list",
        "article_selector": "a",
        "title_selector": None,
        "link_selector": None,
    },
]


async def scrape_with_playwright(url: str, source_name: str) -> List[dict]:
    """
    Scrape a web page using Playwright.
    Returns list of {title, url, summary} dicts.
    """
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                ]
            )
            context = await browser.new_context(
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36'
                ),
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()

            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(3000)  # Extra wait for dynamic content

            # Get page content
            content = await page.content()

            await browser.close()

        # Parse with BeautifulSoup
        soup = BeautifulSoup(content, 'lxml')

        # Try to find article links
        articles = []
        # Strategy: find all links with financial keywords in text
        financial_keywords = re.compile(
            r'(stock|market|earnings|trading|shares|NYSE|NASDAQ|bullish|'
            r'bearish|dividend|IPO|SEC|filing|quarterly|revenue|profit|'
            r'acqui|merger|upgrade|downgrade|target)',
            re.IGNORECASE
        )

        links = soup.find_all('a', href=True)
        seen_urls = set()

        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)

            # Must have meaningful text
            if len(text) < 15:
                continue

            # Must contain financial keywords or be on financial sites
            if not financial_keywords.search(text) and not financial_keywords.search(href):
                continue

            # Make absolute URL
            if href.startswith('/'):
                from urllib.parse import urlparse
                parsed = urlparse(url)
                href = f"{parsed.scheme}://{parsed.netloc}{href}"
            elif not href.startswith('http'):
                continue

            if href in seen_urls:
                continue
            seen_urls.add(href)

            # Get surrounding text as summary
            parent = link.parent
            summary = ""
            if parent:
                summary = parent.get_text(strip=True)[:500]

            articles.append({
                'title': text[:300],
                'url': href,
                'summary': summary,
            })

        print(f"[Playwright] Scraped {len(articles)} articles from {url}")
        return articles[:30]  # Limit

    except Exception as e:
        print(f"[Playwright] Error scraping {url}: {e}")
        return []


async def scrape_finviz_news(ticker: str = None) -> List[NewsCreate]:
    """
    Scrape Finviz news for a specific ticker or general news.
    """
    url = f"https://finviz.com/quote.ashx?t={ticker}" if ticker else "https://finviz.com/news.ashx"
    source_name = f"Finviz{'-' + ticker if ticker else ''}"

    articles_data = await scrape_with_playwright(url, source_name)
    articles = []

    for item in articles_data:
        tickers = extract_tickers(f"{item['title']} {item['summary']}")
        if ticker and ticker not in tickers:
            tickers.append(ticker)
        elif not ticker and not tickers:
            continue

        article = NewsCreate(
            title=item['title'][:500],
            url=item['url'],
            source=source_name,
            summary=item['summary'][:2000],
            tickers=tickers,
            published=datetime.now(timezone.utc),
            source_type='scrape',
        )
        articles.append(article)

    return articles


async def scrape_ticker_news(ticker: str) -> List[NewsCreate]:
    """
    Scrape news for a specific ticker from multiple sources.
    """
    articles = []

    # Finviz
    finviz_articles = await scrape_finviz_news(ticker)
    articles.extend(finviz_articles)

    return articles


async def scrape_all_sources(tickers: List[str] = None) -> List[NewsCreate]:
    """
    Scrape all configured sources for news articles.
    """
    all_articles = []

    # Scrape general financial news pages
    for target in SCRAPE_TARGETS:
        articles_data = await scrape_with_playwright(target['url'], target['name'])
        for item in articles_data:
            tickers = extract_tickers(f"{item['title']} {item['summary']}")
            if not tickers:
                continue
            article = NewsCreate(
                title=item['title'][:500],
                url=item['url'],
                source=target['name'],
                summary=item['summary'][:2000],
                tickers=tickers,
                published=datetime.now(timezone.utc),
                source_type='scrape',
            )
            all_articles.append(article)

    # Scrape per-ticker news if provided
    if tickers:
        for ticker in tickers:
            ticker_articles = await scrape_ticker_news(ticker)
            all_articles.extend(ticker_articles)

    # Deduplicate
    seen_urls = set()
    unique = []
    for article in all_articles:
        if article.url not in seen_urls:
            seen_urls.add(article.url)
            unique.append(article)

    print(f"[Playwright] Total scraped articles: {len(unique)}")
    return unique
