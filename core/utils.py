"""
Common utility functions for the news summary system.
"""

import logging
import os
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration."""
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"news_summary_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in configuration file {config_path}: {e}")
        return {}


def expand_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively expand environment variables in configuration."""
    if isinstance(config, dict):
        return {k: expand_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [expand_env_vars(item) for item in config]
    elif isinstance(config, str) and config.startswith('${') and config.endswith('}'):
        env_var = config[2:-1]
        return os.getenv(env_var, config)
    else:
        return config


def filter_enabled_items(config: Dict[str, Any]) -> Dict[str, Any]:
    """Filter configuration items that are enabled."""
    return {
        name: item for name, item in config.items() 
        if item.get('enabled', True)
    }


def normalize_article(title: str, content: str, url: str = "", topic: str = "general") -> Dict[str, Any]:
    """Normalize article data structure."""
    return {
        'title': title.strip(),
        'content': content.strip(),
        'url': url.strip(),
        'topic': topic.lower(),
        'timestamp': datetime.now().isoformat(),
        'word_count': len(content.split())
    }


def truncate_content(content: str, max_length: int = 2000) -> str:
    """Truncate content to maximum length while preserving word boundaries."""
    if len(content) <= max_length:
        return content
    
    truncated = content[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # Only truncate at word boundary if it's not too far back
        return truncated[:last_space] + "..."
    else:
        return truncated + "..."


def format_summary_message(summary: str, articles: List[Dict[str, Any]], topic: str) -> str:
    """Format the final summary message for delivery."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    article_count = len(articles)
    
    message = f"📰 **News Summary - {topic.title()}**\n"
    message += f"🕐 {timestamp} | 📄 {article_count} articles\n\n"
    message += f"{summary}\n\n"
    
    if articles:
        message += "**Sources:**\n"
        for i, article in enumerate(articles[:5], 1):  # Limit to 5 sources
            if article.get('url'):
                message += f"{i}. [{article['title'][:50]}...]({article['url']})\n"
            else:
                message += f"{i}. {article['title'][:50]}...\n"
    
    return message


def create_embeddings_table_sql() -> str:
    """Return SQL for creating the articles table with vector support."""
    return """
    CREATE EXTENSION IF NOT EXISTS vector;
    
    CREATE TABLE IF NOT EXISTS articles (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        url TEXT,
        topic TEXT NOT NULL,
        provider TEXT NOT NULL,
        embedding vector(384),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed_at TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_articles_topic ON articles(topic);
    CREATE INDEX IF NOT EXISTS idx_articles_provider ON articles(provider);
    CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles(created_at);
    """


def validate_url(url: str) -> bool:
    """Validate if a URL is properly formatted."""
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None
