"""
LLM Client for interacting with language models like Mistral.
Handles generation, completions, and other LLM operations.
"""

import logging
import os
import json
import requests
import time
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class LLMClient:
    """Client for interacting with language models."""
    
    def __init__(self):
        """Initialize the LLM client."""
        logger.info("Initializing LLM Client")
        
        # Load configuration from environment or defaults
        self.endpoint = os.environ.get('MISTRAL_ENDPOINT', 'http://localhost:11434/api/generate')
        self.model = os.environ.get('MISTRAL_MODEL', 'mistral')
        self.timeout = int(os.environ.get('MISTRAL_TIMEOUT', '120'))
        self.max_retries = int(os.environ.get('MISTRAL_MAX_RETRIES', '3'))
        
    async def generate(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Generate text using the LLM.
        
        Args:
            prompt: The input prompt for the LLM
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text
        """
        logger.info(f"Generating response for prompt: {prompt[:50]}...")
        
        # Implement retry mechanism
        retries = 0
        last_error = None
        
        while retries <= self.max_retries:
            try:
                # Prepare request payload for Ollama API
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                }
                
                logger.info(f"Sending request to LLM at {self.endpoint} (attempt {retries+1}/{self.max_retries+1})")
                
                response = requests.post(
                    self.endpoint,
                    json=payload,
                    timeout=self.timeout,
                    headers={'Content-Type': 'application/json'}
                )
                
                response.raise_for_status()
                result = response.json()
                
                generated_text = result.get('response', '').strip()
                
                if not generated_text:
                    raise ValueError("Empty response from LLM")
                
                logger.info(f"Successfully generated {len(generated_text)} chars of text")
                return generated_text
                
            except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
                last_error = e
                retries += 1
                if retries <= self.max_retries:
                    logger.warning(f"Attempt {retries}/{self.max_retries+1} failed: {e}. Retrying...")
                    # Exponential backoff
                    time.sleep(2 ** retries)
                else:
                    logger.error(f"All {self.max_retries+1} attempts failed. Last error: {e}")
                    break
        
        # If we've exhausted all retries, raise the last error
        logger.error(f"Failed to generate text after {self.max_retries+1} attempts")
        return f"Error: Unable to complete the request. Please try again later. ({str(last_error)})"
