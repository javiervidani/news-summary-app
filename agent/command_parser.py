"""
Command parser for natural language processing of user commands.
Interprets user requests into structured actions for the MCP.
"""

import logging
import os
import re
from typing import Dict, Any, Tuple, Optional, List

logger = logging.getLogger(__name__)

class CommandParser:
    """Parser for natural language commands."""
    
    def __init__(self):
        """Initialize the command parser."""
        logger.info("Initializing Command Parser")
        self.commands = {
            "add_source": [
                r"add\s+(.+?)\s+(as\s+a\s+news\s+source|as\s+news\s+source)",
                r"add\s+(.+?)\s+with\s+url\s+(.+)",
                r"create\s+(a\s+)?new\s+source\s+(?:called\s+)?(.+)",
                r"create\s+(a\s+)?new\s+provider\s+(?:called\s+)?(.+)"
            ],
            "remove_source": [
                r"remove\s+(.+?)(\s+source)?",
                r"delete\s+(.+?)(\s+source)?",
                r"disable\s+(.+?)(\s+source)?"
            ],
            "list_sources": [
                r"list\s+(all\s+)?sources",
                r"show\s+(all\s+)?sources",
                r"what\s+sources",
                r"available\s+sources"
            ],
            "summarize": [
                r"summarize\s+(?:news\s+)?(?:about\s+)?(.+)",
                r"give\s+me\s+a\s+summary\s+(?:of|about)\s+(.+)",
                r"news\s+(?:about|on)\s+(.+)"
            ],
            "help": [
                r"help",
                r"what\s+can\s+you\s+do",
                r"how\s+(?:do\s+I|to)\s+use"
            ]
        }
    
    async def parse(self, command: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Parse a natural language command into an intent and parameters.
        
        Args:
            command: The natural language command from the user
            
        Returns:
            Tuple containing:
            - Intent name (or None if not recognized)
            - Dictionary of parameters
        """
        if not command:
            return None, {}
            
        # Convert to lowercase for easier matching
        command = command.lower().strip()
        
        # Check each intent pattern
        for intent, patterns in self.commands.items():
            for pattern in patterns:
                match = re.match(pattern, command, re.IGNORECASE)
                if match:
                    # Extract parameters based on the intent
                    params = self._extract_params(intent, match)
                    logger.info(f"Parsed command: {intent} {params}")
                    return intent, params
        
        # If we get here, the command wasn't recognized
        logger.warning(f"Unrecognized command: {command}")
        return None, {}
    
    def _extract_params(self, intent: str, match) -> Dict[str, Any]:
        """
        Extract parameters from a regex match based on the intent.
        
        Args:
            intent: The recognized intent
            match: The regex match object
            
        Returns:
            Dictionary of parameters
        """
        params = {}
        
        if intent == "add_source":
            if len(match.groups()) >= 2 and "url" in match.re.pattern:
                # Pattern is "add X with url Y"
                params["name"] = match.group(1).strip()
                params["url"] = match.group(2).strip()
            else:
                # Pattern is "add X as a news source"
                params["name"] = match.group(1).strip()
        
        elif intent == "remove_source":
            params["name"] = match.group(1).strip()
        
        elif intent == "summarize":
            params["topic"] = match.group(1).strip()
            
        return params
    
    def get_available_commands(self) -> List[str]:
        """Return a list of available command examples."""
        examples = [
            "Add BBC as a news source",
            "Add CNN with URL https://rss.cnn.com/rss/cnn_topstories.rss",
            "Remove BBC",
            "List all sources",
            "Summarize news about politics",
            "Give me a summary of technology news",
            "Help"
        ]
        return examples
