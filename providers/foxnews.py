"""Provider for foxnews"""
import logging
import feedparser
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

FEED_URL = "https://moxie.foxnews.com/google-publisher/sports.xml"  # was latest.xml
PRIMARY_TOPIC = "sport"

def fetch_articles() -> List[Dict[str, Any]]:
    """Fetch articles from Fox News Sports feed."""
    logger.info("Fetching foxnews RSS from %s", FEED_URL)
    d = feedparser.parse(FEED_URL)
    entries = d.entries or []
    articles: List[Dict[str, Any]] = []
    for entry in entries:
        try:
            articles.append({
                "title": (entry.get("title") or "").strip(),
                "url": entry.get("link"),
                "content": entry.get("summary") or entry.get("description") or "",
                "published_at": entry.get("published") or entry.get("updated") or "",
                "topic": PRIMARY_TOPIC,
            })
        except Exception as e:
            logger.warning("Error parsing entry: %s", e)
            continue
    logger.info("Successfully fetched %d articles from foxnews (sports)", len(articles))
    return articles
