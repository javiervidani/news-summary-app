"""Provider for aljazeera"""
import logging
import feedparser
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

PRIMARY_TOPIC = "sport"
SPORT_KEYWORDS = [
    "sport", "sports", "football", "soccer", "nba", "nfl", "tennis",
    "cricket", "golf", "olympic", "olympics", "fifa", "uefa", "motorsport",
    "formula", "mlb", "nhl", "rugby", "athletics"
]

def _is_sport(entry) -> bool:
    title = (entry.get("title") or "").lower()
    link = (entry.get("link") or "").lower()
    # Check title or link keywords
    if any(k in title or k in link for k in SPORT_KEYWORDS):
        return True
    # Check tags if present
    tags = getattr(entry, 'tags', []) or entry.get('tags') or []
    for t in tags:
        term = ''
        if isinstance(t, dict):
            term = (t.get('term') or '').lower()
        else:
            term = (getattr(t, 'term', '') or '').lower()
        if any(k in term for k in SPORT_KEYWORDS):
            return True
    return False

def fetch_articles() -> List[Dict[str, Any]]:
    """Fetch ONLY sport articles for provider 'aljazeera'. Non-sport entries are skipped."""
    url = "https://www.aljazeera.com/xml/rss/all.xml"
    logger.info("Fetching aljazeera RSS from %s", url)
    d = feedparser.parse(url)
    entries = d.entries or []
    articles: List[Dict[str, Any]] = []
    for entry in entries[:5]:  # initial slice limit
        try:
            if not _is_sport(entry):
                continue  # skip non-sport
            articles.append({
                "title": (entry.get("title") or "").strip(),
                "url": entry.get("link"),
                "content": entry.get("summary") or entry.get("description") or "",
                "published_at": entry.get("published") or entry.get("updated") or "",
                "topic": PRIMARY_TOPIC,
            })
        except Exception as e:  # defensive
            logger.warning("Error parsing entry: %s", e)
            continue
    if not articles:
        logger.info("No sport articles found in aljazeera feed (requested topic: sport); skipping provider.")
    else:
        logger.info("Successfully fetched %d sport articles from aljazeera", len(articles))
    return articles
