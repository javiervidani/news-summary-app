"""
Mistral LLM processor for local summarization.
Works with Ollama or any OpenAI-compatible API endpoint.
"""

import logging
import requests
import json
from typing import Dict, Any

from .base_processor import BaseProcessor


class MistralProcessor(BaseProcessor):
    """Mistral LLM processor for summarization."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.endpoint = config.get('endpoint', 'http://localhost:11434/api/generate')
        self.model = config.get('model', 'mistral')
        self.timeout = config.get('timeout', 120)  # Increased timeout
        self.max_retries = config.get('max_retries', 3)
        self.max_tokens = config.get('max_tokens', 500)
    
    def summarize(self, content: str, config: Dict[str, Any] = None) -> str:
        """Generate summary using local Mistral model."""
        if config:
            self.config.update(config)
        
        # Implement retry mechanism
        retries = 0
        max_retries = self.max_retries
        last_error = None
        
        while retries <= max_retries:
            try:
                prompt = self.format_prompt(content)
                
                # Prepare request payload for Ollama API
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": self.max_tokens,
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                }
                
                self.logger.info(f"Sending request to Mistral at {self.endpoint} (attempt {retries+1}/{max_retries+1})")
                
                response = requests.post(
                    self.endpoint,
                    json=payload,
                    timeout=self.timeout,
                    headers={'Content-Type': 'application/json'}
                )
                
                response.raise_for_status()
                result = response.json()
                
                summary = result.get('response', '').strip()
                
                if not summary:
                    raise ValueError("Empty response from Mistral API")
                
                self.logger.info("Summary generated successfully with Mistral")
                return summary
            
            except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
                last_error = e
                retries += 1
                if retries <= max_retries:
                    self.logger.warning(f"Attempt {retries}/{max_retries+1} failed: {e}. Retrying...")
                else:
                    self.logger.error(f"All {max_retries+1} attempts failed. Last error: {e}")
                    
        # If we've exhausted all retries, use fallback
        self.logger.error(f"Failed to generate summary after {max_retries+1} attempts. Last error: {last_error}")
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
    """Main entry point for the Mistral processor."""
    default_config = {
        'endpoint': 'http://localhost:11434/api/generate',
        'model': 'mistral',
        'max_tokens': 500,
        'prompt_template': """Summarize the following news articles in a clear and concise manner. Focus on the key facts, main events, and important implications. Present the information in a structured way that highlights the most newsworthy elements:

{content}

Summary:"""
    }
    
    if config:
        default_config.update(config)
    
    processor = MistralProcessor(default_config)
    return processor.summarize(content, config)
