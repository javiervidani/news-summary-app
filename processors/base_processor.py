"""
Base processor class for consistent interface across all summary processors.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseProcessor(ABC):
    """Abstract base class for content processors."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_tokens = config.get('max_tokens', 500)
        self.prompt_template = config.get('prompt_template', 
                                        "Summarize the following content:\n\n{content}")
    
    @abstractmethod
    def summarize(self, content: str, config: Dict[str, Any] = None) -> str:
        """
        Generate a summary of the provided content.
        
        Args:
            content: The text content to summarize
            config: Optional processor configuration
            
        Returns:
            Summarized text
        """
        pass
    
    def format_prompt(self, content: str) -> str:
        """Format the content with the prompt template."""
        return self.prompt_template.format(content=content)
