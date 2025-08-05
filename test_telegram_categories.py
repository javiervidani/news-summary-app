#!/usr/bin/env python3
"""
Test script for verifying category-based Telegram routing
and title-only mode functionality.

Usage:
  python test_telegram_categories.py

Environment variables:
  TELEGRAM_BOT_TOKEN - Your Telegram bot token
  TELEGRAM_CHAT_ID - Default Telegram chat ID
  TELEGRAM_CHAT_ID_SPORTS - Sports channel ID (optional)
  TELEGRAM_CHAT_ID_POLITICS - Politics channel ID (optional)
  TELEGRAM_CHAT_ID_TECH - Tech channel ID (optional)
  TELEGRAM_TITLE_ONLY - Set to "true" to test title-only mode (optional)
"""

import os
import logging
import argparse
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_config(title_only: bool = False) -> Dict[str, Any]:
    """Create a test configuration for the Telegram interface."""
    config = {
        'config': {
            'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
            'chat_id': os.getenv('TELEGRAM_CHAT_ID', ''),
            'chat_id_sports': os.getenv('TELEGRAM_CHAT_ID_SPORTS', ''),
            'chat_id_politics': os.getenv('TELEGRAM_CHAT_ID_POLITICS', ''),
            'chat_id_tech': os.getenv('TELEGRAM_CHAT_ID_TECH', ''),
            'title_only': title_only or os.getenv('TELEGRAM_TITLE_ONLY', '').lower() == 'true',
            'parse_mode': 'Markdown'
        }
    }
    return config

def test_category_routing():
    """Test sending messages to different categories."""
    try:
        from interfaces.telegram import TelegramInterface
        
        # Create test configuration
        config = create_test_config()
        
        # Check environment variables
        if not config['config']['bot_token'] or not config['config']['chat_id']:
            logger.error("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables must be set")
            return False
            
        # Create interface instance
        interface = TelegramInterface(config)
        
        # Test connection
        if not interface.test_connection():
            logger.error("Failed to connect to Telegram")
            return False
            
        # Test default channel
        logger.info("Testing default channel...")
        long_message = """# Test News Update
        
This is a test message for the default channel.

The message is intentionally longer to test proper formatting.
It also includes multiple paragraphs to test message handling.

1. Testing formatting
2. Testing categories
3. Testing title-only mode

Thank you for testing!
"""
        success = interface.send(long_message, "general")
        logger.info(f"Default channel test {'successful' if success else 'failed'}")
        
        # Test sports category
        if config['config']['chat_id_sports']:
            logger.info("Testing sports channel...")
            sports_message = """# Sports Update
            
Breaking: Team wins championship!

The underdog team has defied all expectations and won the championship
after a thrilling final match that kept viewers on the edge of their seats.

Coach Smith said: "This is the result of years of hard work and determination."
"""
            success = interface.send(sports_message, "sports")
            logger.info(f"Sports channel test {'successful' if success else 'failed'}")
        else:
            logger.warning("TELEGRAM_CHAT_ID_SPORTS not set, skipping sports test")
            
        # Test politics category
        if config['config']['chat_id_politics']:
            logger.info("Testing politics channel...")
            politics_message = """# Political News
            
New policy announced by government officials.

The administration has unveiled a new set of regulations
that will impact several sectors of the economy.

Opposition leaders have expressed concerns about implementation costs.
"""
            success = interface.send(politics_message, "politics")
            logger.info(f"Politics channel test {'successful' if success else 'failed'}")
        else:
            logger.warning("TELEGRAM_CHAT_ID_POLITICS not set, skipping politics test")
            
        # Test tech category
        if config['config']['chat_id_tech']:
            logger.info("Testing tech channel...")
            tech_message = """# Technology Breakthrough
            
Researchers develop quantum computing milestone.

Scientists at a major university have achieved a significant breakthrough
in quantum computing stability, potentially accelerating development
of practical quantum computers.

This could revolutionize fields from cryptography to drug discovery.
"""
            success = interface.send(tech_message, "tech")
            logger.info(f"Tech channel test {'successful' if success else 'failed'}")
        else:
            logger.warning("TELEGRAM_CHAT_ID_TECH not set, skipping tech test")
            
        return True
            
    except ImportError:
        logger.error("Could not import TelegramInterface - check if the module exists")
        return False
    except Exception as e:
        logger.error(f"Error during category testing: {e}")
        return False

def test_title_only_mode():
    """Test sending messages in title-only mode."""
    try:
        from interfaces.telegram import TelegramInterface
        
        # Create test configuration with title-only enabled
        config = create_test_config(title_only=True)
        
        # Check environment variables
        if not config['config']['bot_token'] or not config['config']['chat_id']:
            logger.error("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables must be set")
            return False
            
        # Create interface instance
        interface = TelegramInterface(config)
        
        # Test connection
        if not interface.test_connection():
            logger.error("Failed to connect to Telegram")
            return False
            
        # Test with markdown title
        logger.info("Testing title-only mode with markdown title...")
        md_message = """# Important Breaking News
        
This is the content of the article that should not be sent.
Only the title "Important Breaking News" should be sent.

More details that should be omitted in title-only mode.
"""
        success = interface.send(md_message, "general")
        logger.info(f"Title-only markdown test {'successful' if success else 'failed'}")
        
        # Test with plain text
        logger.info("Testing title-only mode with plain text...")
        plain_message = """Breaking News: Major Event
        
This is the content of the article that should not be sent.
Only the title "Breaking News: Major Event" should be sent.

More details that should be omitted in title-only mode.
"""
        success = interface.send(plain_message, "tech")
        logger.info(f"Title-only plain text test {'successful' if success else 'failed'}")
        
        return True
            
    except ImportError:
        logger.error("Could not import TelegramInterface - check if the module exists")
        return False
    except Exception as e:
        logger.error(f"Error during title-only testing: {e}")
        return False

def main():
    """Main entry point for testing."""
    parser = argparse.ArgumentParser(description='Test Telegram category routing and title-only mode')
    parser.add_argument('--title-only', action='store_true', help='Test title-only mode')
    parser.add_argument('--categories', action='store_true', help='Test category-based routing')
    args = parser.parse_args()
    
    if args.title_only or (not args.title_only and not args.categories):
        logger.info("Testing title-only mode...")
        if test_title_only_mode():
            logger.info("Title-only mode test completed successfully")
        else:
            logger.error("Title-only mode test failed")
    
    if args.categories or (not args.title_only and not args.categories):
        logger.info("Testing category-based routing...")
        if test_category_routing():
            logger.info("Category-based routing test completed successfully")
        else:
            logger.error("Category-based routing test failed")

if __name__ == "__main__":
    main()
