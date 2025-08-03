#!/usr/bin/env python3
"""
Single article test for the news summary system.
Tests individual article processing and database integration.
"""

import sys
import logging
import argparse
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import load_env_file from main
from main import load_env_file

# Load environment variables first
load_env_file()

from core.utils import setup_logging, load_config
from core import db_utils
from providers.bbc import BBCProvider
from providers.ynet import YnetProvider
from processors.mistral_summary import MistralProcessor

def test_direct_processing(provider_name="bbc"):
    """Test processing a single article directly using provider and processor."""
    setup_logging("INFO")
    logger = logging.getLogger("single_article_test")
    
    logger.info(f"Starting single article direct processing test with {provider_name}")
    
    # Initialize provider based on name
    if provider_name.lower() == "ynet":
        provider_config = {
            'url': 'https://www.ynet.co.il/Integration/StoryRss2.xml',
            'topics': ['general', 'israel']
        }
        provider = YnetProvider(provider_config)
    else:
        provider_config = {
            'url': 'http://feeds.bbci.co.uk/news/rss.xml',
            'topics': ['general', 'world', 'politics']
        }
        provider = BBCProvider(provider_config)
    
    # Get a single article
    logger.info(f"Fetching a single article from {provider_name}")
    articles = provider.fetch_articles()
    
    if not articles:
        logger.error("No articles found")
        return False
        
    # Take just one article
    article = articles[0]
    logger.info(f"Successfully fetched article: {article['title']}")
    
    # Initialize processor with retry mechanism
    processor_config = {
        'endpoint': 'http://localhost:11434/api/generate',
        'model': 'mistral',
        'max_tokens': 300,
        'timeout': 180,
        'max_retries': 2
    }
    processor = MistralProcessor(processor_config)
    
    # Process the article
    logger.info("Processing article with Mistral")
    content = f"Title: {article['title']}\n\n{article['content']}"
    summary = processor.summarize(content)
    
    # Save to database if possible
    try:
        logger.info("Saving article to database")
        article_with_id = save_article_to_db(article)
        
        if article_with_id and 'id' in article_with_id:
            logger.info(f"Article saved with ID: {article_with_id['id']}")
            db_utils.update_article_summary(article_with_id['id'], summary)
            logger.info("Article summary updated in database")
    except Exception as e:
        logger.warning(f"Could not save to database: {e}")
    
    logger.info("Summary generated:")
    print("\n" + "=" * 80)
    print(f"Article: {article['title']}")
    print("-" * 80)
    print(summary)
    print("=" * 80 + "\n")
    
    return True

def save_article_to_db(article):
    """Save a single article to database and return article with ID."""
    try:
        # Create a list with just one article
        articles = [article]
        db_utils.save_articles(articles)
        
        # Query the database to get the ID
        conn = db_utils.get_connection()
        if not conn:
            return None
            
        schema = db_utils.get_schema()
        table_name = db_utils.get_table_name()
        
        with conn.cursor() as cur:
            # Find the article by title
            cur.execute(f"""
                SELECT id FROM {schema}.{table_name}
                WHERE title = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (article['title'],))
            
            row = cur.fetchone()
            if row:
                article['id'] = row[0]
                return article
            return None
    except Exception:
        return None

def test_with_runner(provider_name="bbc", save_only=False):
    """Test processing a single article using the NewsRunner."""
    setup_logging("INFO")
    logger = logging.getLogger("single_article_test")
    
    logger.info(f"Starting single article test with NewsRunner using {provider_name}")
    
    # Import here to avoid circular imports
    from core.runner import NewsRunner
    
    # Initialize the runner
    runner = NewsRunner()
    
    # Run with one article
    success = runner.run(
        providers=[provider_name],
        article_limit=1,
        save_only=save_only
    )
    
    if success:
        logger.info("Test completed successfully")
    else:
        logger.error("Test failed")
    
    return success

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test single article processing")
    parser.add_argument("--provider", type=str, default="bbc", 
                      help="Provider to use (default: bbc)")
    parser.add_argument("--mode", type=str, default="direct", 
                      choices=["direct", "runner", "save"],
                      help="Test mode: direct processing or via runner (default: direct)")
    args = parser.parse_args()
    
    if args.mode == "direct":
        test_direct_processing(args.provider)
    elif args.mode == "save":
        test_with_runner(args.provider, save_only=True)
    else:
        test_with_runner(args.provider)
