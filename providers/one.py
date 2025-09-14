"""Provider for one"""
import logging
import feedparser
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def fetch_articles() -> List[Dict[str, Any]]:
    """Fetch articles for provider 'one'."""
    url = "https://www.one.co.il/cat/coop/xml/rss/newsfeed.aspx"
    logger.info("Fetching one RSS from %s", url)
    d = feedparser.parse(url)
    entries = d.entries or []
    articles: List[Dict[str, Any]] = []
    for entry in entries[:5]:
        try:
            articles.append({
                "title": (entry.get("title") or "").strip(),
                "url": entry.get("link"),
                "content": entry.get("summary") or entry.get("description") or "",
                "published_at": entry.get("published") or entry.get("updated") or "",
                "topic": "general",
            })
        except Exception as e:  # defensive
            logger.warning("Error parsing entry: %s", e)
            continue
    logger.info("Successfully fetched %d articles from one", len(articles))
    return articles
