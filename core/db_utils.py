
"""
Database utility functions for the news summary system.
Handles connections, queries, and data storage.
"""

import os
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from . import utils

# Check if psycopg2 is available
try:
    import psycopg2
    from psycopg2.extras import Json, execute_values
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

logger = logging.getLogger(__name__)

def get_connection():
    """Create a connection to the PostgreSQL database."""
    if not PSYCOPG2_AVAILABLE:
        logger.warning("psycopg2 not available. Database functionality is disabled.")
        return None
        
    try:
        # Get database connection parameters from environment
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_DATABASE', 'mcp')
        db_schema = os.getenv('DB_SCHEMA', 'news_summary')
        db_user = os.getenv('DB_USERNAME', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        
        # Connect to the database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        
        # Ensure the schema exists
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {db_schema}")
            conn.commit()
            
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def get_db_config():
    """Get database configuration from the config file."""
    config_dir = Path("config")
    config_path = config_dir / "database.json"
    return utils.load_config(str(config_path))

def get_table_name():
    """Get the configured articles table name."""
    db_conf = get_db_config()
    return db_conf.get("table_name", "articles")

def get_schema():
    """Get the configured database schema."""
    db_conf = get_db_config()
    return db_conf.get("schema", "news_summary")

def ensure_tables_exist():
    """Ensure all required database tables exist."""
    if not PSYCOPG2_AVAILABLE:
        logger.warning("psycopg2 not available. Skipping database table creation.")
        return False
        
    try:
        conn = get_connection()
        if not conn:
            return False
            
        schema = get_schema()
        table_name = get_table_name()
        
        with conn.cursor() as cur:
            # Create the vector extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            
            # Create the articles table
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    url TEXT,
                    topic TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    embedding vector(384),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    summary TEXT
                )
            """)
            
            # Create indexes
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_topic ON {schema}.{table_name}(topic)")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_provider ON {schema}.{table_name}(provider)")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at ON {schema}.{table_name}(created_at)")
            
            conn.commit()
            logger.info("Database tables and extensions verified")
            return True
            
    except Exception as e:
        logger.error(f"Error ensuring tables exist: {e}")
        return False
    finally:
        if conn:
            conn.close()

def save_articles(articles: List[Dict[str, Any]]) -> bool:
    """Save articles to the database."""
    if not articles:
        return True
        
    if not PSYCOPG2_AVAILABLE:
        logger.warning("psycopg2 not available. Skipping article saving to database.")
        return False
        
    try:
        conn = get_connection()
        if not conn:
            return False
            
        schema = get_schema()
        table_name = get_table_name()
        
        # Prepare values for insertion
        values = []
        for article in articles:
            values.append((
                article.get('title', 'Untitled'),
                article.get('content', ''),
                article.get('url', ''),
                article.get('topic', 'general'),
                article.get('provider', 'unknown'),
                None,  # embedding (to be added later)
                datetime.now(),
                None,  # processed_at
                None   # summary
            ))
        
        with conn.cursor() as cur:
            # Insert values using execute_values for efficiency
            execute_values(
                cur,
                f"""
                INSERT INTO {schema}.{table_name} 
                (title, content, url, topic, provider, embedding, created_at, processed_at, summary)
                VALUES %s
                """,
                values
            )
            
            conn.commit()
            logger.info(f"Saved {len(articles)} articles to database")
            return True
            
    except Exception as e:
        logger.error(f"Error saving articles to database: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_unprocessed_articles(hours: int = 6, limit: int = None) -> List[Dict[str, Any]]:
    """Get articles from the last N hours that haven't been processed."""
    if not PSYCOPG2_AVAILABLE:
        logger.warning("psycopg2 not available. Cannot retrieve articles from database.")
        return []
        
    try:
        conn = get_connection()
        if not conn:
            return []
            
        schema = get_schema()
        table_name = get_table_name()
        
        with conn.cursor() as cur:
            query = f"""
                SELECT id, title, content, url, topic, provider, created_at
                FROM {schema}.{table_name}
                WHERE created_at >= NOW() - INTERVAL '{hours} hours'
                AND (processed_at IS NULL OR summary IS NULL)
                ORDER BY created_at DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
                
            cur.execute(query)
            
            # Convert to list of dictionaries
            columns = [desc[0] for desc in cur.description]
            result = []
            for row in cur.fetchall():
                article = dict(zip(columns, row))
                result.append(article)
                
            logger.info(f"Retrieved {len(result)} unprocessed articles from database")
            return result
            
    except Exception as e:
        logger.error(f"Error retrieving unprocessed articles: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_article_summary(article_id: int, summary: str) -> bool:
    """Update an article with its summary and mark as processed."""
    if not PSYCOPG2_AVAILABLE:
        logger.warning("psycopg2 not available. Cannot update article summary in database.")
        return False
        
    try:
        conn = get_connection()
        if not conn:
            return False
            
        schema = get_schema()
        table_name = get_table_name()
        
        with conn.cursor() as cur:
            cur.execute(f"""
                UPDATE {schema}.{table_name}
                SET summary = %s, processed_at = NOW()
                WHERE id = %s
            """, (summary, article_id))
            
            conn.commit()
            return True
            
    except Exception as e:
        logger.error(f"Error updating article summary: {e}")
        return False
    finally:
        if conn:
            conn.close()