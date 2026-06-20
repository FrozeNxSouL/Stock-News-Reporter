"""
News analyzer using NLP to determine sentiment, relevance,
and assess impact on stock price direction.
"""
import re
from typing import List, Tuple, Optional
from textblob import TextBlob
from models.analysis import SentimentScore, ImpactAssessment, NewsAnalysisCreate

# Financial sentiment keyword dictionaries
BULLISH_KEYWORDS = {
    'surge', 'soar', 'jump', 'rally', 'boom', 'breakthrough', 'upgrade',
    'outperform', 'beat', 'exceed', 'positive', 'growth', 'profit', 'gain',
    'bullish', 'optimistic', 'strong', 'record', 'dividend', 'buyback',
    'acquisition', 'merger', 'partnership', 'expansion', 'launch',
    'FDA approval', 'patent', 'innovation', 'leadership', 'dominant',
    'upgraded', 'raised', 'increased', 'outlook positive',
    'better-than-expected', 'above expectations',
}

BEARISH_KEYWORDS = {
    'plunge', 'crash', 'drop', 'fall', 'decline', 'downgrade', 'sell-off',
    'bearish', 'pessimistic', 'loss', 'debt', 'lawsuit', 'investigation',
    'SEC probe', 'fraud', 'scandal', 'restructuring', 'layoff', 'firing',
    'resignation', 'competition', 'regulation', 'tariff', 'sanction',
    'downgraded', 'lowered', 'decreased', 'outlook negative', 'warning',
    'below expectations', 'missed estimates', 'short interest',
    'volatile', 'uncertainty', 'risk',
}

STRONG_IMPACT_KEYWORDS = {
    'FDA', 'approval', 'rejection', 'acquisition', 'merger', 'bankruptcy',
    'SEC', 'lawsuit', 'settlement', 'CEO resigns', 'CEO fired',
    'earnings beat', 'earnings miss', 'dividend cut', 'stock split',
    'government investigation', 'antitrust', 'recall', 'data breach',
}

# Ticker-to-company mapping for indirect mentions
TICKER_COMPANY_MAP = {
    'AAPL': 'Apple',
    'MSFT': 'Microsoft',
    'GOOGL': 'Alphabet',
    'GOOG': 'Alphabet',
    'AMZN': 'Amazon',
    'META': 'Meta',
    'NVDA': 'NVIDIA',
    'TSLA': 'Tesla',
    'JPM': 'JPMorgan',
    'V': 'Visa',
    'SPY': 'S&P 500',
    'QQQ': 'Nasdaq',
    'DIA': 'Dow Jones',
    'BABA': 'Alibaba',
    'NFLX': 'Netflix',
    'DIS': 'Disney',
    'BAC': 'Bank of America',
    'WMT': 'Walmart',
    'PG': 'Procter & Gamble',
    'KO': 'Coca-Cola',
    'PEP': 'PepsiCo',
    'JNJ': 'Johnson & Johnson',
    'UNH': 'UnitedHealth',
    'HD': 'Home Depot',
    'INTC': 'Intel',
    'AMD': 'AMD',
    'CRM': 'Salesforce',
    'ADBE': 'Adobe',
    'ORCL': 'Oracle',
    'IBM': 'IBM',
    'CSCO': 'Cisco',
    'QCOM': 'Qualcomm',
    'TXN': 'Texas Instruments',
    'AVGO': 'Broadcom',
    'PYPL': 'PayPal',
    'SNAP': 'Snap',
    'UBER': 'Uber',
    'LYFT': 'Lyft',
    'SQ': 'Block',
    'SHOP': 'Shopify',
    'ZM': 'Zoom',
    'DOCU': 'DocuSign',
    'PLTR': 'Palantir',
    'SNOW': 'Snowflake',
    'DASH': 'DoorDash',
    'COIN': 'Coinbase',
    'HOOD': 'Robinhood',
}


def analyze_sentiment(text: str) -> SentimentScore:
    """
    Analyze sentiment of text using TextBlob + financial keyword enhancement.
    """
    if not text:
        return SentimentScore()

    # TextBlob analysis
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity

    # Financial keyword boost
    text_lower = text.lower()
    bullish_count = sum(1 for kw in BULLISH_KEYWORDS if kw.lower() in text_lower)
    bearish_count = sum(1 for kw in BEARISH_KEYWORDS if kw.lower() in text_lower)

    # Adjust polarity with keyword signals
    keyword_boost = (bullish_count - bearish_count) * 0.05
    polarity = max(-1.0, min(1.0, polarity + keyword_boost))

    # Determine label
    if polarity > 0.15:
        label = 'positive'
    elif polarity < -0.15:
        label = 'negative'
    else:
        label = 'neutral'

    return SentimentScore(
        polarity=round(polarity, 4),
        subjectivity=round(subjectivity, 4),
        label=label,
    )


def assess_impact(text: str, sentiment: SentimentScore) -> ImpactAssessment:
    """
    Assess the potential impact of news on a stock's price.
    """
    if not text:
        return ImpactAssessment()

    text_lower = text.lower()

    # Determine direction
    if sentiment.label == 'positive':
        direction = 'up'
    elif sentiment.label == 'negative':
        direction = 'down'
    else:
        direction = 'neutral'

    # Check for strong impact keywords
    strong_hits = sum(1 for kw in STRONG_IMPACT_KEYWORDS if kw.lower() in text_lower)
    bullish_count = sum(1 for kw in BULLISH_KEYWORDS if kw.lower() in text_lower)
    bearish_count = sum(1 for kw in BEARISH_KEYWORDS if kw.lower() in text_lower)
    total_keywords = bullish_count + bearish_count

    # Determine strength
    if strong_hits >= 2 or total_keywords >= 5 or abs(sentiment.polarity) > 0.6:
        strength = 'high'
    elif strong_hits >= 1 or total_keywords >= 3 or abs(sentiment.polarity) > 0.3:
        strength = 'medium'
    else:
        strength = 'low'

    # Determine effect duration
    duration_hints = {
        'long-term': ['long-term', 'fundamental', 'strategic', 'transformation', 'acquisition',
                      'merger', 'new market', 'expansion plan', 'CEO change', 'restructuring'],
        'medium-term': ['quarterly', 'earnings', 'guidance', 'outlook', 'product launch',
                        'partnership', 'contract', 'regulation', 'legal settlement'],
        'short-term': ['short-term', 'day', 'trading', 'volatility', 'analyst', 'upgrade',
                       'downgrade', 'target', 'rumor', 'speculation'],
    }

    duration_scores = {}
    for duration, keywords in duration_hints.items():
        duration_scores[duration] = sum(1 for kw in keywords if kw.lower() in text_lower)

    if duration_scores.get('long-term', 0) > duration_scores.get('medium-term', 0) and \
       duration_scores['long-term'] > duration_scores.get('short-term', 0):
        effect_duration = 'long-term'
    elif duration_scores.get('medium-term', 0) > duration_scores.get('short-term', 0):
        effect_duration = 'medium-term'
    else:
        effect_duration = 'short-term'

    # Estimate price range percentages
    if strength == 'high':
        if direction == 'up':
            range_low, range_high = 3.0, 10.0
        elif direction == 'down':
            range_low, range_high = -10.0, -3.0
        else:
            range_low, range_high = -3.0, 3.0
    elif strength == 'medium':
        if direction == 'up':
            range_low, range_high = 1.0, 5.0
        elif direction == 'down':
            range_low, range_high = -5.0, -1.0
        else:
            range_low, range_high = -2.0, 2.0
    else:
        if direction == 'up':
            range_low, range_high = 0.5, 2.0
        elif direction == 'down':
            range_low, range_high = -2.0, -0.5
        else:
            range_low, range_high = -1.0, 1.0

    # Confidence based on polarity magnitude and keyword density
    confidence = min(1.0, (abs(sentiment.polarity) * 0.5) + (total_keywords * 0.05) + (strong_hits * 0.1))

    # Generate reasoning
    reasoning_parts = []
    if sentiment.label != 'neutral':
        reasoning_parts.append(
            f"Sentiment is {sentiment.label} (polarity: {sentiment.polarity:.2f})."
        )
    if bullish_count > bearish_count:
        reasoning_parts.append(f"Found {bullish_count} bullish indicators.")
    elif bearish_count > bullish_count:
        reasoning_parts.append(f"Found {bearish_count} bearish indicators.")

    if strong_hits > 0:
        reasoning_parts.append(f"Contains {strong_hits} high-impact signal(s).")

    reasoning = " ".join(reasoning_parts) if reasoning_parts else "Insufficient signals for strong assessment."

    return ImpactAssessment(
        direction=direction,
        strength=strength,
        effect_duration=effect_duration,
        price_range_low=range_low,
        price_range_high=range_high,
        confidence=round(confidence, 4),
        reasoning=reasoning,
    )


def calculate_relevance(title: str, summary: str, ticker: str) -> float:
    """
    Calculate how relevant a news article is to a specific ticker.
    Returns score 0.0 - 1.0.
    """
    text = f"{title} {summary}".lower()
    company_name = TICKER_COMPANY_MAP.get(ticker, '').lower()
    ticker_lower = ticker.lower()

    score = 0.0

    # Direct ticker mention
    if ticker_lower in text:
        score += 0.6

    # Company name mention
    if company_name and company_name in text:
        score += 0.3

    # Sector/industry keywords
    if ticker in TICKER_COMPANY_MAP:
        # Check for related company mentions (for sector-wide news)
        related_mentions = sum(1 for other_ticker in TICKER_COMPANY_MAP
                              if other_ticker != ticker and other_ticker.lower() in text)
        if related_mentions > 2:
            score += 0.15  # sector-wide news

    return min(1.0, score)


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract important keywords from text."""
    if not text:
        return []

    blob = TextBlob(text)
    # Extract noun phrases and frequent words
    words = [word.lower() for word in blob.words if len(word) > 2 and word.isalpha()]

    # Filter stop words
    stop_words = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
        'had', 'her', 'was', 'one', 'our', 'out', 'has', 'have', 'been',
        'this', 'that', 'with', 'from', 'they', 'will', 'would', 'could',
        'should', 'also', 'its', 'than', 'then', 'very', 'just',
    }
    words = [w for w in words if w not in stop_words]

    # Count frequency
    from collections import Counter
    word_counts = Counter(words)

    return [word for word, _ in word_counts.most_common(max_keywords)]


async def analyze_news(news_item, tickers: List[str] = None) -> List[NewsAnalysisCreate]:
    """
    Analyze a news article for all relevant tickers.
    Returns a list of analysis objects.
    """
    text = f"{news_item.title} {news_item.summary} {news_item.content}"

    sentiment = analyze_sentiment(text)
    impact = assess_impact(text, sentiment)
    keywords = extract_keywords(text)

    # If tickers not provided, use news item's tickers
    target_tickers = tickers or news_item.tickers

    analyses = []
    for ticker in target_tickers:
        if len(ticker) > 5 or len(ticker) < 1:
            continue

        relevance = calculate_relevance(news_item.title, news_item.summary, ticker)

        if relevance > 0.1:  # Only analyze if minimally relevant
            analysis = NewsAnalysisCreate(
                news_id=str(news_item.id) if hasattr(news_item, 'id') else str(id(news_item)),
                ticker=ticker,
                sentiment=sentiment,
                impact=impact,
                relevance_score=round(relevance, 4),
                keywords=keywords,
            )
            analyses.append(analysis)

    return analyses
