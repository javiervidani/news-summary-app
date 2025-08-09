# Auto-generated Fox News provider module
import logging
import feedparser

logger = logging.getLogger(__name__)

def fetch(config, topic=None, limit=None):
    url = config["url"]
    logger.info(f"Fetching {{config.get('name','foxnews')}} RSS from {{url}}")
    d = feedparser.parse(url)
    items = d.entries
    lim = limit or config.get("limit")
    if lim:
        items = items[:lim]
    articles = []
    for entry in items:
        articles.append({
            "title": entry.get("title","").strip(),
            "url": entry.get("link"),
            "content": entry.get("summary","") or "",
            "published_at": entry.get("published",""),
            "provider": "foxnews",
            "topic": topic or config.get("topic") or "general",
            "raw": entry
        })
    logger.info(f"Successfully fetched {{len(articles)}} articles from foxnews")
    return articles

def fetch_articles(config, topic=None, limit=None):
    return fetch(config, topic, limit)
