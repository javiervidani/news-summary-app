#!/usr/bin/env python3
"""
Scheduler for the News Summary System.
Fetches and stores articles continuously, and summarizes them on a schedule.
"""

import sys
import time
import logging
import schedule
from pathlib import Path
from datetime import datetime
import subprocess
import os

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.utils import setup_logging, load_env_file

# Load environment variables
load_env_file()

# Setup logging
setup_logging("INFO")
logger = logging.getLogger(__name__)

# Configuration
FETCH_INTERVAL_MINUTES = int(os.getenv('FETCH_INTERVAL_MINUTES', '30'))
SUMMARY_INTERVAL_HOURS = int(os.getenv('SUMMARY_INTERVAL_HOURS', '6'))
PYTHON_EXECUTABLE = os.getenv('PYTHON_EXECUTABLE', 'python3')
ARTICLE_LIMIT = os.getenv('ARTICLE_LIMIT', '')
LIMIT_FLAG = f'--limit {ARTICLE_LIMIT}' if ARTICLE_LIMIT else ''

def fetch_articles():
    """Fetch articles and save to database."""
    logger.info(f"Starting scheduled article fetching at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        cmd = f"{PYTHON_EXECUTABLE} main.py --save-only {LIMIT_FLAG}"
        logger.info(f"Running command: {cmd}")
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Article fetching completed successfully")
            logger.debug(result.stdout)
        else:
            logger.error(f"Article fetching failed with exit code {result.returncode}")
            logger.error(result.stderr)
    
    except Exception as e:
        logger.error(f"Error in scheduled article fetching: {e}")

def process_summaries():
    """Process articles from database and generate summaries."""
    logger.info(f"Starting scheduled summary processing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        cmd = f"{PYTHON_EXECUTABLE} main.py --batch-process --hours {SUMMARY_INTERVAL_HOURS} --send-telegram {LIMIT_FLAG}"
        logger.info(f"Running command: {cmd}")
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Summary processing completed successfully")
            logger.debug(result.stdout)
        else:
            logger.error(f"Summary processing failed with exit code {result.returncode}")
            logger.error(result.stderr)
    
    except Exception as e:
        logger.error(f"Error in scheduled summary processing: {e}")

def main():
    """Main scheduler function."""
    logger.info("Starting News Summary Scheduler")
    
    # Schedule article fetching
    schedule.every(FETCH_INTERVAL_MINUTES).minutes.do(fetch_articles)
    logger.info(f"Scheduled article fetching every {FETCH_INTERVAL_MINUTES} minutes")
    
    # Schedule summary processing
    schedule.every(SUMMARY_INTERVAL_HOURS).hours.do(process_summaries)
    logger.info(f"Scheduled summary processing every {SUMMARY_INTERVAL_HOURS} hours")
    
    # Run the initial fetch immediately
    fetch_articles()
    
    # Run the scheduler loop
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(300)  # Wait 5 minutes before retrying

if __name__ == "__main__":
    main()
