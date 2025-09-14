#!/usr/bin/env python3
"""
Main entry point for the Modular News Summary System.
Can be run directly or scheduled via cron.
"""

import argparse
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.runner import NewsRunner
from core.utils import setup_logging


def load_env_file(env_file='.env'):
    """Load environment variables from .env file."""
    import os
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
    # Load environment variables from .env file
    load_env_file()
    
    parser = argparse.ArgumentParser(description='Modular News Summary System')
    parser.add_argument('--topics', nargs='+', default=['general'], 
                       help='Topics to process (default: general)')
    parser.add_argument('--providers', nargs='+', 
                       help='Specific providers to use (default: all enabled)')
    parser.add_argument('--exclude-providers', nargs='+',
                       help='Providers to explicitly exclude (applied after --providers filtering)')
    parser.add_argument('--processor', default='mistral',
                       help='Processor to use for summarization (default: mistral)')
    parser.add_argument('--interfaces', nargs='+',
                       help='Delivery interfaces to use (default: all enabled)')
    parser.add_argument('--config-dir', default='config',
                       help='Configuration directory (default: config)')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level (default: INFO)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run without actually sending notifications')
    parser.add_argument('--limit', type=int, 
                       help='Limit the number of articles processed per provider')
    parser.add_argument('--send-telegram', action='store_true',
                       help='Send the summary to Telegram (shortcut for --interfaces telegram)')
    parser.add_argument('--title-only', action='store_true',
                       help='Skip LLM summarization and send only article titles as links')
    parser.add_argument('--title-only-n-description', action='store_true',
                       help='Skip LLM summarization and send titles plus short description lines')
    
    # Database-related options
    parser.add_argument('--save-only', action='store_true',
                       help='Only save articles to database without processing')
    parser.add_argument('--batch-process', action='store_true',
                       help='Process articles from database instead of fetching new ones')
    parser.add_argument('--hours', type=int, default=6,
                       help='Hours of articles to include in batch processing (default: 6)')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting News Summary System")
    logger.info(f"Topics: {args.topics}")
    logger.info(f"Processor: {args.processor}")
    if args.exclude_providers:
        logger.info(f"Excluding providers: {', '.join(args.exclude_providers)}")
    
    # Handle the --send-telegram shortcut
    if args.send_telegram:
        if args.interfaces:
            if 'telegram' not in args.interfaces:
                args.interfaces.append('telegram')
        else:
            args.interfaces = ['telegram']
        logger.info("Telegram interface enabled via --send-telegram flag")
    
    try:
        # Initialize and run the news runner
        runner = NewsRunner(
            config_dir=args.config_dir,
            dry_run=args.dry_run
        )
        
        # Determine which mode to run in
        if args.batch_process:
            # Run batch processing on articles in the database
            success = runner.run_batch_process(
                hours=args.hours,
                processor=args.processor,
                interfaces=args.interfaces,
                article_limit=args.limit
            )
        else:
            # Regular mode: fetch articles and optionally process them
            success = runner.run(
                topics=args.topics,
                providers=args.providers,
                processor=args.processor,
                interfaces=args.interfaces,
                article_limit=args.limit,
                save_only=args.save_only,
                title_only=args.title_only or args.title_only_n_description,
                title_only_with_description=args.title_only_n_description,
                exclude_providers=args.exclude_providers
            )
        
        if success:
            logger.info("News summary process completed successfully")
            sys.exit(0)
        else:
            logger.error("News summary process failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
