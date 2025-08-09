#!/usr/bin/env python3
"""
Simple test script to verify Mistral LLM is working properly.
"""

import sys
import logging
import requests
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.utils import setup_logging

def test_mistral():
    """Test if Mistral is responding correctly."""
    setup_logging("INFO")
    logger = logging.getLogger("test_mistral")
    
    logger.info("Testing connection to Mistral LLM...")
    
    # Simple test prompt
    prompt = "Summarize the following news headline in one sentence: 'Global economy shows signs of recovery as inflation eases'"
    
    # Request to Mistral
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False,
                "max_tokens": 100
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("Successfully connected to Mistral!")
            logger.info(f"Response: {result.get('response', 'No response text')}")
            return True
        else:
            logger.error(f"Error connecting to Mistral: {response.status_code}, {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("Connection to Mistral timed out")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_mistral()
    sys.exit(0 if success else 1)
