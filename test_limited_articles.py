#!/usr/bin/env python3
"""
Test script for processing a limited number of articles from a specific provider.
"""

import sys
import logging
import os
from pathlib import Path
import argparse

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.utils import setup_logging, expand_env_vars, format_summary_message
from providers.bbc import BBCProvider
from providers.nyt import NYTProvider
from processors.mistral_summary import MistralProcessor
from interfaces.telegram import TelegramInterface

def load_env_file(env_file='.env'):
    """Load environment variables from .env file."""
    if not os.path.exists(env_file):
        return False
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('\'"')
    
    return True

def main():
    """Process a limited number of articles from a specific provider."""
    # Load environment variables from .env file
    load_env_file()
    
    parser = argparse.ArgumentParser(description='Test limited article processing')
    parser.add_argument('--provider', choices=['bbc', 'nyt'], default='bbc',
                      help='News provider to use (default: bbc)')
    parser.add_argument('--limit', type=int, default=3,
                      help='Maximum number of articles to process (default: 3)')
    parser.add_argument('--topic', default='general',
                      help='Topic to filter articles by (default: general)')
    parser.add_argument('--timeout', type=int, default=120,
                      help='API timeout in seconds (default: 120)')
    parser.add_argument('--send-telegram', action='store_true',
                      help='Send the summary to Telegram channel')
    
    args = parser.parse_args()
    
    setup_logging("INFO")
    logger = logging.getLogger("limited_articles_test")
    
    logger.info(f"Starting test with provider: {args.provider}, limit: {args.limit}")
    
    # Initialize provider
    if args.provider == 'bbc':
        provider_config = {
            'url': 'http://feeds.bbci.co.uk/news/rss.xml',
            'topics': [args.topic]
        }
        provider = BBCProvider(provider_config)
    elif args.provider == 'nyt':
        provider_config = {
            'url': 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
            'topics': [args.topic]
        }
        provider = NYTProvider(provider_config)
    
    # Get articles
    logger.info(f"Fetching articles from {args.provider}")
    all_articles = provider.fetch_articles()
    
    if not all_articles:
        logger.error("No articles found")
        return False
        
    # Take the specified number of articles
    articles = all_articles[:args.limit]
    logger.info(f"Successfully fetched {len(articles)} articles")
    
    # Initialize processor
    processor_config = {
        'endpoint': 'http://localhost:11434/api/generate',
        'model': 'mistral',
        'max_tokens': 500,
        'timeout': args.timeout
    }
    processor = MistralProcessor(processor_config)
    
    # Process articles
    logger.info(f"Processing {len(articles)} articles with Mistral")
    combined_content = ""
    for i, article in enumerate(articles, 1):
        combined_content += f"Article {i}: {article['title']}\n{article['content']}\n\n"
    
    summary = processor.summarize(combined_content)
    
    logger.info("Summary generated:")
    print("\n" + "=" * 80)
    print(f"Summary of {len(articles)} articles from {args.provider.upper()}")
    print("-" * 80)
    print(summary)
    print("=" * 80 + "\n")
    
    # Send to Telegram if requested
    if args.send_telegram:
        logger.info("Sending summary to Telegram")
        try:
            # Prepare telegram config
            telegram_config = {
                'config': {
                    'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
                    'chat_id': os.getenv('TELEGRAM_CHAT_ID'),
                    'parse_mode': 'Markdown'
                }
            }
            
            # Create formatted message
            formatted_message = format_summary_message(summary, articles, args.topic)
            
            # Initialize Telegram interface and send message
            telegram = TelegramInterface(telegram_config)
            success = telegram.send(formatted_message, args.topic)
            
            if success:
                logger.info("Summary successfully sent to Telegram")
            else:
                logger.error("Failed to send summary to Telegram")
                
        except Exception as e:
            logger.error(f"Error sending to Telegram: {e}")
    
    return True

if __name__ == "__main__":
    main()
