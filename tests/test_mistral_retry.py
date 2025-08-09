#!/usr/bin/env python3
"""
Test script for the improved Mistral processor with retry mechanism.
"""

import argparse
import logging
import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, List

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import load_env_file from main
from main import load_env_file

# Load environment variables first
load_env_file()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("mistral-retry-test")

# Import core components
from providers.ynet import YnetProvider
from processors.mistral_summary import MistralProcessor


def load_config(file_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config from {file_path}: {e}")
        return {}


def test_mistral_summarization(article_limit: int = 3, timeout: int = 180):
    """Test the Mistral processor with increased timeout and retry mechanism."""
    logger.info("Starting Mistral summarization test with retry mechanism")
    
    # Load provider config
    provider_config = {
        'url': 'https://www.ynet.co.il/Integration/StoryRss2.xml',
        'topics': ['general', 'israel']
    }
    
    # Load LLM config
    llm_config = load_config('./config/llm.json')
    mistral_config = llm_config.get('models', {}).get('mistral', {})
    
    # Set timeout and retry parameters
    mistral_config['timeout'] = timeout  # Increased timeout
    mistral_config['max_retries'] = 3    # Set number of retries
    mistral_config['max_tokens'] = 500
    
    # Initialize components
    provider = YnetProvider(provider_config)
    processor = MistralProcessor(mistral_config)
    
    # Fetch articles
    logger.info("Fetching articles from Ynet")
    articles = provider.fetch_articles()
    
    # Limit the number of articles
    if article_limit > 0 and len(articles) > article_limit:
        logger.info(f"Limiting articles to {article_limit}")
        articles = articles[:article_limit]
    
    # Process articles
    logger.info(f"Processing {len(articles)} articles with Mistral")
    
    for i, article in enumerate(articles):
        logger.info(f"Processing article {i+1}/{len(articles)}: {article['title']}")
        
        # Construct content for summarization
        content = f"Title: {article['title']}\n\n{article['content']}"
        
        try:
            # Generate summary
            logger.info(f"Generating summary for article: {article['title']}")
            summary = processor.summarize(content)
            
            # Output summary
            logger.info(f"Summary: {summary[:100]}...")
            
        except Exception as e:
            logger.error(f"Error processing article {i+1}: {e}")
    
    logger.info("Test completed")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test Mistral processor with retry mechanism")
    parser.add_argument("--limit", type=int, default=3, help="Limit the number of articles to process")
    parser.add_argument("--timeout", type=int, default=180, help="Timeout value for Mistral requests in seconds")
    args = parser.parse_args()
    
    test_mistral_summarization(args.limit, args.timeout)
