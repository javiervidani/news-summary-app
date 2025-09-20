"""Provider for yahoofinance"""
import logging
import feedparser
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

PRIMARY_TOPIC = "sport"

def fetch_articles() -> List[Dict[str, Any]]:
    """Fetch articles for provider 'yahoofinance'."""
    url = "https://finance.yahoo.com/news/rssindex"
    logger.info("Fetching yahoofinance RSS from %s", url)
    d = feedparser.parse(url)
    entries = d.entries or []
    articles: List[Dict[str, Any]] = []
    for entry in entries:
        try:
            # Make sure to include all required fields
            articles.append({
                "title": (entry.get("title") or "").strip(),
                "url": entry.get("link"),
                "content": entry.get("summary") or entry.get("description") or "",
                "published_at": entry.get("published") or entry.get("updated") or "",
                # Explicitly set topics that match your filtering
                "topic": "finance", 
                "provider": "yahoofinance",
            })
        except Exception as e:
            logger.warning("Error parsing entry: %s", e)
            continue
    logger.info("Successfully fetched %d articles from yahoofinance", len(articles))
    return articles
