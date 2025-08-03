"""
Telegram Command Interface for interacting with the MCP.
Extends the basic Telegram interface with command processing.
"""

import logging
import os
import asyncio
import re
from typing import Dict, Any, Tuple, Optional, List

import requests
from core.utils import load_config
from agent.mcp import MasterControlProgram

logger = logging.getLogger(__name__)

class TelegramCommandInterface:
    """Interface for processing Telegram commands with the MCP."""
    
    def __init__(self):
        """Initialize the Telegram command interface."""
        logger.info("Initializing Telegram Command Interface")
        
        # Set up MCP
        self.mcp = MasterControlProgram()
        
        # Get configuration
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
        
        if not self.bot_token or not self.chat_id:
            raise ValueError("Telegram bot_token and chat_id must be configured")
            
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
    async def process_message(self, message: str, chat_id: str = None, user_id: str = None) -> str:
        """
        Process an incoming Telegram message.
        
        Args:
            message: The message text
            chat_id: The chat ID (optional)
            user_id: The user ID (optional)
            
        Returns:
            Response message
        """
        logger.info(f"Processing Telegram message: {message[:50]}...")
        
        # Set default chat ID if not provided
        chat_id = chat_id or self.chat_id
        
        # Check if it's a command (starts with /)
        if message.startswith('/'):
            return await self._handle_command(message, chat_id, user_id)
        else:
            # Process as natural language command
            return await self.mcp.process_command(message, user_id)
            
    async def _handle_command(self, command: str, chat_id: str, user_id: str = None) -> str:
        """
        Handle Telegram bot commands.
        
        Args:
            command: The command (starts with /)
            chat_id: The chat ID
            user_id: The user ID (optional)
            
        Returns:
            Response message
        """
        # Strip the slash and get the command name
        parts = command[1:].split()
        cmd_name = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Handle built-in commands
        if cmd_name == 'start' or cmd_name == 'help':
            return self._get_help_message()
            
        elif cmd_name == 'sources':
            return await self.mcp.list_sources()
            
        elif cmd_name == 'add':
            # Format: /add name [url]
            if not args:
                return "Usage: /add source_name [url]"
                
            name = args[0]
            url = args[1] if len(args) > 1 else None
            
            return await self.mcp.add_new_source(name, url)
            
        elif cmd_name == 'remove':
            # Format: /remove name
            if not args:
                return "Usage: /remove source_name"
                
            name = args[0]
            return await self.mcp.remove_source(name)
            
        elif cmd_name == 'summarize':
            # Format: /summarize topic
            if not args:
                return "Usage: /summarize topic"
                
            topic = args[0]
            return await self.mcp.summarize_topic(topic)
            
        else:
            return f"Unknown command: {cmd_name}\nType /help for available commands."
            
    def _get_help_message(self) -> str:
        """Get the help message."""
        return """
📰 *News Agent Commands*

*Sources*
/sources - List all available news sources
/add name [url] - Add a new news source
/remove name - Remove a news source

*Summaries*
/summarize topic - Get a summary of a specific topic

*System*
/help - Show this help message

You can also just type your request in natural language, like:
- Add BBC as a news source
- Summarize news about politics
- List all sources
"""
    
    async def send_message(self, message: str, chat_id: str = None) -> bool:
        """
        Send a message to Telegram.
        
        Args:
            message: The message to send
            chat_id: The chat ID (optional)
            
        Returns:
            Success indicator
        """
        chat_id = chat_id or self.chat_id
        
        # Prepare API request
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        url = f"{self.api_url}/sendMessage"
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                logger.info("Message sent successfully to Telegram")
                return True
            else:
                logger.error(f"Telegram API error: {result.get('description')}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {e}")
            return False
            
    async def start_webhook(self, port: int = 8443):
        """
        Start a webhook server to receive Telegram updates.
        This is a simplified version - for production, use a proper web framework.
        
        Args:
            port: The port to listen on
        """
        # This would typically use a web framework like FastAPI or Flask
        # and would set up a webhook with Telegram
        # For simplicity, we're not implementing this here
        logger.info(f"Webhook would listen on port {port}")
        logger.info("This is a placeholder - implement with a proper web framework")
        
    async def start_polling(self):
        """
        Start polling for Telegram updates.
        This is a simple long-polling implementation.
        """
        logger.info("Starting Telegram update polling")
        
        offset = 0
        
        while True:
            try:
                # Get updates from Telegram
                params = {
                    'offset': offset,
                    'timeout': 30,
                    'allowed_updates': ['message']
                }
                
                response = requests.get(f"{self.api_url}/getUpdates", params=params)
                response.raise_for_status()
                
                updates = response.json()
                
                if not updates.get('ok'):
                    logger.error(f"Error getting updates: {updates.get('description')}")
                    await asyncio.sleep(5)
                    continue
                    
                # Process updates
                for update in updates.get('result', []):
                    update_id = update.get('update_id')
                    offset = update_id + 1  # Update offset for next poll
                    
                    # Process message
                    message = update.get('message')
                    if message:
                        chat_id = str(message.get('chat', {}).get('id'))
                        user_id = str(message.get('from', {}).get('id'))
                        text = message.get('text', '')
                        
                        if text:
                            # Process the message
                            response_text = await self.process_message(text, chat_id, user_id)
                            
                            # Send response
                            await self.send_message(response_text, chat_id)
                            
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                await asyncio.sleep(5)
                
            # Wait a bit before next poll
            await asyncio.sleep(1)


# Function to start the Telegram bot
async def start_telegram_bot():
    """Start the Telegram command interface."""
    try:
        bot = TelegramCommandInterface()
        await bot.start_polling()
    except Exception as e:
        logger.error(f"Error starting Telegram bot: {e}")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load environment variables
    from main import load_env_file
    load_env_file()
    
    # Run the bot
    asyncio.run(start_telegram_bot())
