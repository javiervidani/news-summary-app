"""
Channel 14 news RSS provider (formerly Channel 20).
Fetches articles from Channel 14, an Israeli news channel.
"""

import logging
import requests
import feedparser
from typing import List, Dict, Any
from bs4 import BeautifulSoup

from .base_provider import BaseProvider


class Channel14Provider(BaseProvider):
    """Channel 14 news RSS feed provider."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.rss_url = config.get('url', 'https://www.inn.co.il/Rss.aspx')
        self.topics = config.get('topics', ['israel', 'politics'])
    
    def fetch_articles(self) -> List[Dict[str, Any]]:
        """Fetch articles from Channel 14 RSS feed."""
        articles = []
        
        try:
            self.logger.info(f"Fetching Channel 14 RSS from {self.rss_url}")
            
            # Fetch RSS feed
            response = requests.get(self.rss_url, timeout=30)
            response.raise_for_status()
            
            # Parse RSS feed
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries:
                try:
                    article = self._parse_entry(entry)
                    if article:
                        articles.append(article)
                except Exception as e:
                    self.logger.warning(f"Error parsing Channel 14 entry: {e}")
                    continue
            
            self.logger.info(f"Successfully fetched {len(articles)} articles from Channel 14")
            return articles
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching Channel 14 RSS: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching Channel 14 articles: {e}")
            return []
    
    def _parse_entry(self, entry) -> Dict[str, Any]:
        """Parse a single RSS entry."""
        title = entry.get('title', 'Untitled')
        url = entry.get('link', '')
        
        # Get description/summary
        content = entry.get('description', '')
        if entry.get('summary'):
            content = entry.summary
        
        # Clean HTML from content
        content = self._clean_html(content)
        
        # Determine topic from categories or URL
        topic = self._determine_topic(entry, url)
        
        return self.normalize_article(title, content, url, topic)
    
    def _clean_html(self, content: str) -> str:
        """Remove HTML tags from content."""
        if not content:
            return ""
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            return soup.get_text().strip()
        except Exception:
            return content
    
    def _determine_topic(self, entry, url: str) -> str:
        """Determine article topic from categories or URL."""
        # Check RSS entry tags/categories
        if hasattr(entry, 'tags') and entry.tags:
            for tag in entry.tags:
                tag_term = tag.get('term', '').lower()
                if any(topic in tag_term for topic in self.topics):
                    return tag_term
        
        # Determine from URL path
        url_lower = url.lower()
        if '/news/' in url_lower:
            if '/defense/' in url_lower or '/security/' in url_lower:
                return 'security'
            elif '/foreign/' in url_lower or '/world/' in url_lower:
                return 'world'
            elif '/politics/' in url_lower or '/government/' in url_lower:
                return 'politics'
            else:
                return 'israel'
        elif '/judaism/' in url_lower or '/jewish/' in url_lower:
            return 'judaism'
        elif '/economy/' in url_lower or '/business/' in url_lower:
            return 'business'
        elif '/culture/' in url_lower:
            return 'culture'
        elif '/opinion/' in url_lower:
            return 'opinion'
        
        # Default topic for Channel 14 - setting as 'general' and 'israel'
        return 'general'


# Main function for the module
def fetch_articles() -> List[Dict[str, Any]]:
    """Main entry point for the Channel 14 provider."""
    # Default config - will be overridden by runner
    config = {
        'url': 'https://www.inn.co.il/Rss.aspx',
        'topics': ['israel', 'politics', 'middle_east']
    }
    
    provider = Channel14Provider(config)
    return provider.fetch_articles()
