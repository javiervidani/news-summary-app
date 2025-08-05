"""
Telegram bot interface for sending news summaries.
Requires a Telegram bot token and chat ID.
"""

import logging
import requests
from typing import Dict, Any

from .base_interface import BaseInterface


class TelegramInterface(BaseInterface):
    """Telegram bot interface for message delivery."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Extract config values
        interface_config = config.get('config', {})
        
        # Get values, trying both direct and environment variables
        self.bot_token = self._get_config_value(interface_config, 'bot_token', 'TELEGRAM_BOT_TOKEN')
        self.chat_id = self._get_config_value(interface_config, 'chat_id', 'TELEGRAM_CHAT_ID')
        self.parse_mode = interface_config.get('parse_mode', 'Markdown')
        
        # Handle title-only option
        self.title_only = interface_config.get('title_only', False)
        
        # Set up category-specific chat IDs
        self.category_chat_map = {
            'sports': self._get_config_value(interface_config, 'chat_id_sports', 'TELEGRAM_CHAT_ID_SPORTS'),
            'politics': self._get_config_value(interface_config, 'chat_id_politics', 'TELEGRAM_CHAT_ID_POLITICS'),
            'technology': self._get_config_value(interface_config, 'chat_id_tech', 'TELEGRAM_CHAT_ID_TECH'),
            'tech': self._get_config_value(interface_config, 'chat_id_tech', 'TELEGRAM_CHAT_ID_TECH'),
            # Add other categories as needed
        }
        
        if not self.bot_token or not self.chat_id:
            raise ValueError("Telegram bot_token and chat_id must be configured")
        
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def _get_config_value(self, config: Dict[str, Any], key: str, env_var: str) -> str:
        """Get configuration value, trying both from config and environment."""
        import os
        
        # First try from config
        value = config.get(key, '')
        
        # If it's still a template string (starting with ${), try environment variable directly
        if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
            env_name = value[2:-1]
            value = os.getenv(env_name, '')
        
        # If still empty, try the provided env_var name
        if not value:
            value = os.getenv(env_var, '')
        
        # Log what we're using
        self.logger.debug(f"Using {key} value: {value[:5]}{'*'*(len(value)-5) if len(value)>5 else ''}")
            
        return value
    
    def send(self, message: str, topic: str, config: Dict[str, Any] = None) -> bool:
        """Send message via Telegram bot."""
        try:
            # Prepare the message
            formatted_message = self._format_message(message, topic)
            
            # Determine which chat ID to use based on topic/category
            chat_id = self.chat_id  # Default channel
            
            # Normalize topic for lookup
            normalized_topic = topic.lower().strip() if topic else ""
            
            # Check if we have a specific channel for this topic
            if normalized_topic and normalized_topic in self.category_chat_map:
                specific_chat_id = self.category_chat_map[normalized_topic]
                if specific_chat_id:
                    chat_id = specific_chat_id
                    self.logger.info(f"Using category-specific chat ID for '{topic}'")
            
            # Prepare API request
            payload = {
                'chat_id': chat_id,
                'text': formatted_message,
                'parse_mode': self.parse_mode,
                'disable_web_page_preview': True
            }
            
            url = f"{self.api_url}/sendMessage"
            
            self.logger.info(f"Sending message to Telegram chat {chat_id}")
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                self.logger.info(f"Message sent successfully to Telegram for topic '{topic}'")
                return True
            else:
                self.logger.error(f"Telegram API error: {result.get('description')}")
                return False
                
        except requests.RequestException as e:
            self.logger.error(f"Request error sending to Telegram: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending to Telegram: {e}")
            return False
    
    def _format_message(self, message: str, topic: str) -> str:
        """Format message for Telegram with proper escaping."""
        # Extract title if in title-only mode
        if self.title_only:
            # Try to find the title in the first few lines
            lines = message.split('\n')
            for line in lines[:5]:  # Look at first 5 lines
                if line.strip().startswith('# '):  # Markdown title format
                    return line.strip('# ').strip()
                elif line.strip() and not line.startswith('---') and not line.startswith('*'):
                    # Use first non-empty line that's not a separator as title
                    return line.strip()
            # Fallback to first line if no clear title
            return lines[0].strip() if lines else "News Update"
        
        # Telegram has a message limit of 4096 characters
        max_length = 4000  # Leave some buffer
        
        if len(message) > max_length:
            # Truncate message but try to keep it readable
            truncated = message[:max_length-100]
            last_sentence = truncated.rfind('.')
            if last_sentence > max_length * 0.8:
                message = truncated[:last_sentence+1] + "\n\n[Message truncated...]"
            else:
                message = truncated + "...\n\n[Message truncated...]"
        
        # Add category/topic as prefix if available
        if topic:
            message = f"*{topic.upper()}*\n\n{message}"
            
        return message
    
    def test_connection(self) -> bool:
        """Test Telegram bot connection."""
        try:
            url = f"{self.api_url}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                bot_info = result.get('result', {})
                self.logger.info(f"Telegram bot connected: {bot_info.get('username')}")
                return True
            else:
                self.logger.error(f"Telegram bot test failed: {result.get('description')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error testing Telegram connection: {e}")
            return False


# Main function for the module
def send(message: str, topic: str, config: Dict[str, Any]) -> bool:
    """Main entry point for the Telegram interface."""
    try:
        interface = TelegramInterface(config)
        return interface.send(message, topic, config)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to initialize Telegram interface: {e}")
        # Try with environment variables directly
        import os
        
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        
        # Get category-specific chat IDs
        chat_id_sports = os.getenv('TELEGRAM_CHAT_ID_SPORTS', '')
        chat_id_politics = os.getenv('TELEGRAM_CHAT_ID_POLITICS', '')
        chat_id_tech = os.getenv('TELEGRAM_CHAT_ID_TECH', '')
        title_only = os.getenv('TELEGRAM_TITLE_ONLY', '').lower() == 'true'
        
        if not bot_token or not chat_id:
            logging.getLogger(__name__).error("Cannot find Telegram credentials in environment")
            return False
            
        # Create a new config with direct values
        direct_config = {
            'config': {
                'bot_token': bot_token,
                'chat_id': chat_id,
                'parse_mode': 'Markdown',
                'title_only': title_only,
                'chat_id_sports': chat_id_sports,
                'chat_id_politics': chat_id_politics,
                'chat_id_tech': chat_id_tech
            }
        }
        
        interface = TelegramInterface(direct_config)
        return interface.send(message, topic, direct_config)
