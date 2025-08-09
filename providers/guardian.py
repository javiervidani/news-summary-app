"""Provider for guardian"""
import logging
import feedparser
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def fetch_articles() -> List[Dict[str, Any]]:
    """Fetch articles for provider 'guardian'."""
    url = "https://www.theguardian.com/world/rss"
    logger.info("Fetching guardian RSS from %s", url)
    d = feedparser.parse(url)
    entries = d.entries or []
    articles: List[Dict[str, Any]] = []
    for entry in entries[:2]:
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
    logger.info("Successfully fetched %d articles from guardian", len(articles))
    return articles
