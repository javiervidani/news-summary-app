"""
New York Times RSS provider.
Fetches articles from NYT RSS feeds.
"""

import logging
import requests
import feedparser
from typing import List, Dict, Any
from bs4 import BeautifulSoup

from .base_provider import BaseProvider


class NYTProvider(BaseProvider):
    """New York Times RSS feed provider."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.rss_url = config.get('url', 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml')
        self.topics = config.get('topics', ['general'])
    
    def fetch_articles(self) -> List[Dict[str, Any]]:
        """Fetch articles from NYT RSS feed."""
        articles = []
        
        try:
            self.logger.info(f"Fetching NYT RSS from {self.rss_url}")
            
            # Fetch RSS feed with proper headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.rss_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse RSS feed
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries:
                try:
                    article = self._parse_entry(entry)
                    if article:
                        articles.append(article)
                except Exception as e:
                    self.logger.warning(f"Error parsing NYT entry: {e}")
                    continue
            
            self.logger.info(f"Successfully fetched {len(articles)} articles from NYT")
            return articles
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching NYT RSS: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching NYT articles: {e}")
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
                if 'business' in tag_term:
                    return 'business'
                elif 'technology' in tag_term or 'tech' in tag_term:
                    return 'technology'
                elif 'politics' in tag_term:
                    return 'politics'
                elif 'world' in tag_term or 'international' in tag_term:
                    return 'world'
                elif 'health' in tag_term:
                    return 'health'
                elif 'sports' in tag_term:
                    return 'sports'
        
        # Determine from URL path
        url_lower = url.lower()
        if '/business' in url_lower:
            return 'business'
        elif '/technology' in url_lower or '/tech' in url_lower:
            return 'technology'
        elif '/politics' in url_lower:
            return 'politics'
        elif '/world' in url_lower or '/international' in url_lower:
            return 'world'
        elif '/health' in url_lower:
            return 'health'
        elif '/sports' in url_lower:
            return 'sports'
        elif '/opinion' in url_lower:
            return 'opinion'
        elif '/arts' in url_lower:
            return 'entertainment'
        
        return 'general'


# Main function for the module
def fetch_articles() -> List[Dict[str, Any]]:
    """Main entry point for the NYT provider."""
    # Default config - will be overridden by runner
    config = {
        'url': 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
        'topics': ['general', 'business', 'technology']
    }
    
    provider = NYTProvider(config)
    return provider.fetch_articles()
