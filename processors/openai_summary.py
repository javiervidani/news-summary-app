"""
OpenAI API processor for cloud-based summarization.
"""

import logging
import os
from typing import Dict, Any

from .base_processor import BaseProcessor

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIProcessor(BaseProcessor):
    """OpenAI API processor for summarization."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        # Get API key from environment or config
        api_key = os.getenv('OPENAI_API_KEY') or config.get('api_key')
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model = config.get('model', 'gpt-3.5-turbo')
    
    def summarize(self, content: str, config: Dict[str, Any] = None) -> str:
        """Generate summary using OpenAI API."""
        if config:
            self.config.update(config)
        
        try:
            prompt = self.format_prompt(content)
            
            self.logger.info(f"Sending request to OpenAI model: {self.model}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional news summarizer. Create clear, concise, and informative summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.7,
                top_p=0.9
            )
            
            summary = response.choices[0].message.content.strip()
            
            if not summary:
                raise ValueError("Empty response from OpenAI API")
            
            self.logger.info("Summary generated successfully with OpenAI")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error with OpenAI processor: {e}")
            return self._fallback_summary(content)
    
    def _fallback_summary(self, content: str) -> str:
        """Generate a basic fallback summary if API fails."""
        sentences = content.split('. ')
        if len(sentences) <= 3:
            return content
        
        # Take first 3 sentences as basic summary
        summary = '. '.join(sentences[:3])
        if not summary.endswith('.'):
            summary += '.'
        
        return f"[Fallback Summary] {summary}"


# Main function for the module
def summarize(content: str, config: Dict[str, Any] = None) -> str:
    """Main entry point for the OpenAI processor."""
    default_config = {
        'model': 'gpt-3.5-turbo',
        'max_tokens': 300,
        'prompt_template': """Create a comprehensive summary of these news articles. Focus on:
- Key events and developments
- Important people and organizations involved
- Significant implications or consequences
- Any emerging trends or patterns

Articles:
{content}

Provide a well-structured summary:"""
    }
    
    if config:
        default_config.update(config)
    
    processor = OpenAIProcessor(default_config)
    return processor.summarize(content, config)
