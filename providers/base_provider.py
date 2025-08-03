"""
Base provider class for consistent interface across all news providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseProvider(ABC):
    """Abstract base class for news providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__.lower().replace('provider', '')
    
    @abstractmethod
    def fetch_articles(self) -> List[Dict[str, Any]]:
        """
        Fetch articles from the news source.
        
        Returns:
            List of article dictionaries with keys:
            - title: str
            - content: str  
            - url: str
            - topic: str
        """
        pass
    
    def normalize_article(self, title: str, content: str, url: str = "", 
                         topic: str = "general") -> Dict[str, Any]:
        """Normalize article data structure."""
        from core.utils import normalize_article
        return normalize_article(title, content, url, topic)
