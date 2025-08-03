"""
Base interface class for consistent delivery across all notification channels.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseInterface(ABC):
    """Abstract base class for delivery interfaces."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def send(self, message: str, topic: str, config: Dict[str, Any] = None) -> bool:
        """
        Send a message through the interface.
        
        Args:
            message: The message content to send
            topic: The topic/category of the message
            config: Optional interface configuration
            
        Returns:
            True if sent successfully, False otherwise
        """
        pass
    
    def validate_config(self, required_keys: list) -> bool:
        """Validate that required configuration keys are present."""
        for key in required_keys:
            if key not in self.config.get('config', {}):
                return False
        return True
