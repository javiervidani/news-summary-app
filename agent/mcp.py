"""
Master Control Program (MCP) for the News Summary System.
Handles autonomous operation, self-extension, and command processing.
"""

import logging
import json
import os
import asyncio
from typing import Dict, Any, Tuple, List, Optional

# Will be implemented later
from .command_parser import CommandParser
from .provider_factory import ProviderFactory
from .monitor import SourceMonitor
from .dispatcher import TaskDispatcher

logger = logging.getLogger(__name__)

class MasterControlProgram:
    """Main agent for autonomous news system management."""
    
    def __init__(self):
        """Initialize MCP with its components."""
        logger.info("Initializing Master Control Program")
        self.command_parser = CommandParser()
        self.provider_factory = ProviderFactory()
        self.monitor = SourceMonitor()
        self.dispatcher = TaskDispatcher()
        
        # Load configuration
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
        self.providers = self._load_providers()
        
        logger.info(f"MCP initialized with {len(self.providers)} providers")
        
    def _load_providers(self) -> Dict[str, Any]:
        """Load provider configuration."""
        try:
            providers_path = os.path.join(self.config_dir, "providers.json")
            with open(providers_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading providers: {e}")
            return {}
            
    async def process_command(self, command: str, user_id: Optional[str] = None) -> str:
        """
        Process natural language command from user.
        
        Args:
            command: The natural language command
            user_id: Optional user identifier for personalization
            
        Returns:
            Response message to the user
        """
        logger.info(f"Processing command: {command}")
        
        # Parse the command into an intent and parameters
        intent, params = await self.command_parser.parse(command)
        
        if not intent:
            return "I'm sorry, I couldn't understand that command."
            
        # Handle different command intents
        if intent == "add_source":
            return await self.add_new_source(params.get("name"), params.get("url"))
            
        elif intent == "remove_source":
            return await self.remove_source(params.get("name"))
            
        elif intent == "list_sources":
            return await self.list_sources()
            
        elif intent == "summarize":
            return await self.summarize_topic(params.get("topic"))
            
        elif intent == "help":
            return self.get_help()
            
        else:
            return f"I don't know how to {intent} yet."
    
    async def add_new_source(self, name: str, url: Optional[str] = None) -> str:
        """
        Add a new news source.
        
        Args:
            name: Name of the news source
            url: Optional URL of the news source RSS feed
            
        Returns:
            Status message
        """
        if not name:
            return "Please provide a name for the news source."
            
        # Check if source already exists
        if name.lower() in self.providers:
            return f"The source '{name}' already exists."
            
        # If no URL provided, try to discover it
        if not url:
            logger.info(f"Discovering feed for {name}")
            url = await self.provider_factory.discover_feed(name)
            
            if not url:
                return f"I couldn't find an RSS feed for {name}. Please provide a URL."
        
        logger.info(f"Generating provider for {name} with URL {url}")
        
        # Generate provider code
        result, filename = await self.provider_factory.generate_provider(name, url)
        
        if not result:
            return f"Failed to generate provider for {name}: {filename}"
            
        # Test the new provider
        logger.info(f"Testing provider {name}")
        success, articles = await self.provider_factory.test_provider(name)
        
        if not success:
            # Clean up failed provider
            if os.path.exists(filename):
                os.remove(filename)
            return f"Failed to add {name}: could not fetch articles."
            
        # Register the provider in the configuration
        logger.info(f"Registering provider {name}")
        await self.provider_factory.register_provider(name, url)
        
        # Reload providers
        self.providers = self._load_providers()
        
        return f"Successfully added {name} with {len(articles)} articles."
        
    async def remove_source(self, name: str) -> str:
        """Remove a news source."""
        if not name or name.lower() not in self.providers:
            return f"Source '{name}' not found."
            
        # Remove from configuration
        result = await self.provider_factory.unregister_provider(name)
        
        if result:
            # Reload providers
            self.providers = self._load_providers()
            return f"Successfully removed {name}."
        else:
            return f"Failed to remove {name}."
            
    async def list_sources(self) -> str:
        """List all available news sources."""
        if not self.providers:
            return "No news sources configured."
            
        result = "Available news sources:\n"
        for name, provider in self.providers.items():
            status = "Enabled" if provider.get("enabled", True) else "Disabled"
            topics = ", ".join(provider.get("topics", ["general"]))
            result += f"- {name} ({status}): {topics}\n"
            
        return result
        
    async def summarize_topic(self, topic: str) -> str:
        """Generate a summary for a specific topic."""
        if not topic:
            return "Please provide a topic to summarize."
            
        # This would normally invoke the runner to generate a summary
        return f"I'll generate a summary for the topic '{topic}'. This feature is coming soon."
        
    def get_help(self) -> str:
        """Return help information about available commands."""
        return """
        Here are the commands I understand:
        
        - Add a new source: "Add [source name] as a news source" or "Add [source name] with URL [url]"
        - Remove a source: "Remove [source name]"
        - List sources: "List all news sources" or "Show available sources"
        - Summarize a topic: "Summarize news about [topic]" or "Give me a summary of [topic]"
        - Help: "Help" or "What can you do?"
        """
    
    async def start_monitoring(self):
        """Start monitoring news sources."""
        await self.monitor.start(self.providers)
        
    async def start_scheduling(self):
        """Start task scheduling."""
        await self.dispatcher.start(self.providers)
