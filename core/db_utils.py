"""
Database utility functions for the news summary system.
Handles connections, queries, and data storage.
"""

import os
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
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
    """Ensure all required database tables and columns exist (idempotent/migrating)."""
    if not PSYCOPG2_AVAILABLE:
        logger.warning("psycopg2 not available. Skipping database table creation.")
        return False

    conn = None
    try:
        conn = get_connection()
        if not conn:
            return False

        schema = get_schema()
        table_name = get_table_name()

        with conn.cursor() as cur:
            # Extensions / schema
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

            # Base table (without assuming new columns already exist)
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
                    processed_at TIMESTAMP
                )
            """)

            # Introspect existing columns
            cur.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                """,
                (schema, table_name)
            )
            existing_cols = {r[0] for r in cur.fetchall()}

            # Add missing 'summary' column if needed
            if 'summary' not in existing_cols:
                logger.info("Adding missing 'summary' column to articles table")
                cur.execute(f"ALTER TABLE {schema}.{table_name} ADD COLUMN summary TEXT")
            # Add missing 'telegram_sent_at' column if needed
            if 'telegram_sent_at' not in existing_cols:
                logger.info("Adding missing 'telegram_sent_at' column to articles table")
                cur.execute(f"ALTER TABLE {schema}.{table_name} ADD COLUMN telegram_sent_at TIMESTAMP")

            # Indexes
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_topic ON {schema}.{table_name}(topic)")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_provider ON {schema}.{table_name}(provider)")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at ON {schema}.{table_name}(created_at)")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_telegram_sent ON {schema}.{table_name}(telegram_sent_at)")

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
    """Save articles to the database.

    On success, mutates each article dict by adding its assigned 'id'.
    Returns False if database layer unavailable or insertion failed.
    """
    if not articles:
        return True

    if not PSYCOPG2_AVAILABLE:
        logger.warning("psycopg2 not available. Skipping article saving to database.")
        return False

    conn = None
    try:
        conn = get_connection()
        if not conn:
            logger.error("Database connection not established. Articles not persisted.")
            return False

        schema = get_schema()
        table_name = get_table_name()

        # Prepare values for insertion
        values = [(
            article.get('title', 'Untitled'),
            article.get('content', ''),
            article.get('url', ''),
            article.get('topic', 'general'),
            article.get('provider', 'unknown'),
            None,  # embedding (to be added later)
            datetime.now(),
            None,  # processed_at
            None   # summary
        ) for article in articles]

        with conn.cursor() as cur:
            query = f"""
                INSERT INTO {schema}.{table_name}
                (title, content, url, topic, provider, embedding, created_at, processed_at, summary)
                VALUES %s
                RETURNING id
            """
            returned_ids = execute_values(cur, query, values, fetch=True)
            conn.commit()

        # Attach IDs back to original article dicts
        if returned_ids:
            for article, row in zip(articles, returned_ids):
                if row and isinstance(row, (list, tuple)):
                    article['id'] = row[0]
            logger.info(f"Saved {len(returned_ids)} articles to database (IDs attached)")
        else:
            logger.warning("No IDs returned after insertion; summaries will not be persisted later.")
        return True

    except Exception as e:
        logger.error(f"Error saving articles to database: {e}", exc_info=True)
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

def mark_telegram_sent(article_ids: List[int]) -> None:
    """Mark given article IDs as sent to Telegram."""
    if not article_ids or not PSYCOPG2_AVAILABLE:
        return
    conn = None
    try:
        conn = get_connection()
        if not conn:
            return
        schema = get_schema()
        table_name = get_table_name()
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE {schema}.{table_name} SET telegram_sent_at = NOW() WHERE id = ANY(%s)",
                (article_ids,)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Error marking telegram sent: {e}")
    finally:
        if conn:
            conn.close()

def get_already_sent_urls() -> Set[str]:
    """Return set of URLs already sent to Telegram."""
    if not PSYCOPG2_AVAILABLE:
        return set()
    conn = None
    try:
        conn = get_connection()
        if not conn:
            return set()
        schema = get_schema()
        table_name = get_table_name()
        with conn.cursor() as cur:
            cur.execute(f"SELECT url FROM {schema}.{table_name} WHERE telegram_sent_at IS NOT NULL AND url IS NOT NULL AND url <> ''")
            return {r[0] for r in cur.fetchall()}
    except Exception as e:
        logger.error(f"Error fetching sent URLs: {e}")
        return set()
    finally:
        if conn:
            conn.close()