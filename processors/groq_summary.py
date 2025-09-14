"""
Groq API processor for cloud-based summarization.
"""

import logging
import os
from typing import Dict, Any

from .base_processor import BaseProcessor

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


class GroqProcessor(BaseProcessor):
    """Groq API processor for summarization."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        if not GROQ_AVAILABLE:
            raise ImportError("groq package not installed. Run: pip install groq")
        
        # Get API key from environment or config
        api_key = os.getenv('GROQ_API_KEY') or config.get('api_key')
        if not api_key:
            raise ValueError("Groq API key not found. Set GROQ_API_KEY environment variable.")
        
        self.client = Groq(api_key=api_key)
        self.model = config.get('model', 'llama3-8b-8192')
    
    def summarize(self, content: str, config: Dict[str, Any] = None) -> str:
        """Generate summary using Groq API."""
        if config:
            self.config.update(config)
        
        try:
            prompt = self.format_prompt(content)
            
            self.logger.info(f"Sending request to Groq model: {self.model}")
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional news summarizer. Create clear, concise, and informative summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=self.max_tokens,
                top_p=0.95,
                reasoning_effort="default",
                stream=False,  # Set to False to get the full summary at once
                stop=None
            )
            
            summary = completion.choices[0].message.content.strip()
            
            if not summary:
                raise ValueError("Empty response from Groq API")
            
            self.logger.info("Summary generated successfully with Groq")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error with Groq processor: {e}")
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
    """Main entry point for the Groq processor."""
    default_config = {
        'model': 'qwen/qwen3-32b',
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
    
    processor = GroqProcessor(default_config)
    return processor.summarize(content, config)