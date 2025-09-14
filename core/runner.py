"""
Central runner that orchestrates the news summary system.
Loads configurations, fetches articles, processes summaries, and delivers results.
"""

import logging
import importlib
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .utils import (
    load_config, expand_env_vars, filter_enabled_items, 
    format_summary_message, truncate_content
)
from . import db_utils

MAX_MESSAGE_LENGTH = 3900  # safe buffer under Telegram 4096 char limit


class NewsRunner:
    """Main orchestrator for the news summary system."""
    
    def __init__(self, config_dir: str = "config", dry_run: bool = False):
        self.config_dir = Path(config_dir)
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)
        
        # Load configurations
        self.providers_config = self._load_and_process_config("providers.json")
        self.processors_config = self._load_and_process_config("processors.json")
        self.interfaces_config = self._load_and_process_config("interfaces.json")
        
        # Ensure database tables exist
        db_utils.ensure_tables_exist()
        
        self.logger.info(f"Loaded {len(self.providers_config)} providers, "
                        f"{len(self.processors_config)} processors, "
                        f"{len(self.interfaces_config)} interfaces")
    
    def _load_and_process_config(self, filename: str) -> Dict[str, Any]:
        """Load and process a configuration file."""
        config_path = self.config_dir / filename
        config = load_config(str(config_path))
        config = expand_env_vars(config)
        return filter_enabled_items(config)
    
    def _import_module(self, module_type: str, module_name: str):
        """Dynamically import a module."""
        try:
            module_path = f"{module_type}.{module_name}"
            return importlib.import_module(module_path)
        except ImportError as e:
            self.logger.error(f"Failed to import {module_path}: {e}")
            return None
    
    def _fetch_articles(self, provider_names: Optional[List[str]] = None, 
                       topics: List[str] = None, article_limit: int = None, exclude: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Fetch articles from specified providers."""
        all_articles = []
        providers_to_use = provider_names or list(self.providers_config.keys())
        if exclude:
            excl = {p.lower() for p in exclude}
            providers_to_use = [p for p in providers_to_use if p.lower() not in excl]
        
        for provider_name in providers_to_use:
            if provider_name not in self.providers_config:
                self.logger.warning(f"Provider '{provider_name}' not found in configuration")
                continue
                
            provider_config = self.providers_config[provider_name]
            provider_module = self._import_module("providers", provider_config["module"])
            
            if not provider_module:
                continue
                
            try:
                self.logger.info(f"Fetching articles from {provider_name}")
                articles = provider_module.fetch_articles()
                
                # Filter by topics if specified
                if topics:
                    articles = [
                        article for article in articles 
                        if any(topic.lower() in article.get('topic', '').lower() for topic in topics)
                    ]
                
                # Apply article limit if specified
                if article_limit and len(articles) > article_limit:
                    self.logger.info(f"Limiting to {article_limit} articles from {provider_name}")
                    articles = articles[:article_limit]
                
                # Add provider metadata
                for article in articles:
                    article['provider'] = provider_name
                
                all_articles.extend(articles)
                self.logger.info(f"Fetched {len(articles)} articles from {provider_name}")
                
            except Exception as e:
                self.logger.error(f"Error fetching from {provider_name}: {e}", exc_info=True)
        
        self.logger.info(f"Total articles fetched: {len(all_articles)}")
        return all_articles
    
    def _process_article(self, article: Dict[str, Any], processor_name: str) -> str:
        """Process a single article with the specified processor."""
        if processor_name not in self.processors_config:
            raise ValueError(f"Processor '{processor_name}' not found in configuration")
        
        processor_config = self.processors_config[processor_name]
        processor_module = self._import_module("processors", processor_config["module"])
        
        if not processor_module:
            raise ImportError(f"Failed to import processor module: {processor_config['module']}")
        
        # Prepare content for summarization
        title = article.get('title', 'Untitled')
        content = article.get('content', '')
        truncated_content = truncate_content(content, 500)  # Limit per article
        article_content = f"**{title}**\n{truncated_content}"
        
        try:
            self.logger.info(f"Processing article: {title} with {processor_name}")
            summary = processor_module.summarize(article_content, processor_config)
            self.logger.info("Article processed successfully")
            
            # Save summary to database if article has an ID
            article_id = article.get('id')
            if article_id:
                db_utils.update_article_summary(article_id, summary)
                self.logger.info(f"Updated summary for article ID {article_id} in database")
            
            return summary
        except Exception as e:
            self.logger.error(f"Error processing article with {processor_name}: {e}", exc_info=True)
            raise
    
    def _process_articles(self, articles: List[Dict[str, Any]], processor_name: str) -> List[Dict[str, Any]]:
        """Process multiple articles with the specified processor, one by one."""
        processed_articles = []
        
        for article in articles:
            try:
                summary = self._process_article(article, processor_name)
                article['summary'] = summary
                processed_articles.append(article)
            except Exception as e:
                self.logger.error(f"Error processing article {article.get('title')}: {e}")
                # Continue with next article even if this one fails
                continue
        
        self.logger.info(f"Successfully processed {len(processed_articles)} of {len(articles)} articles")
        return processed_articles
    
    def _deliver_summary(self, summary: str, articles: List[Dict[str, Any]], 
                        topic: str, interface_names: Optional[List[str]] = None,
                        title_only: bool = False, processor_mode: bool = False,
                        title_only_with_description: bool = False):
        """Deliver summary through specified interfaces.

        title_only: if True, summary already contains bullet list links; do not append Sources block.
        processor_mode: if True, build bullet list of article titles with (source) link and ignore raw LLM text.
        title_only_with_description: if True, summary is bullet list titles + short descriptions.
        """
        interfaces_to_use = interface_names or list(self.interfaces_config.keys())

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Decide header based on mode (avoid calling it "News Summary" when we are not summarizing)
        if processor_mode:
            base_header = f"📰 **News Summary - {topic.title()}**\n🕐 {timestamp}"
        elif title_only_with_description or title_only:
            base_header = f"📰 **{topic.title()} Articles**\n🕐 {timestamp}"
        else:  # fallback
            base_header = f"📰 **News Summary - {topic.title()}**\n🕐 {timestamp}"

        # Build body according to mode
        if title_only_with_description:
            article_count = len(articles)
            header = f"{base_header} | 📄 {article_count} articles"
            body = summary.strip()
        elif title_only:
            article_count = len(articles)
            header = f"{base_header} | 📄 {article_count} articles"
            body = summary.strip()
        elif processor_mode:
            # Build bullet list (source links) from articles ignoring provided summary
            bullet_lines = []
            for a in articles:
                title_txt = a.get('title', 'Untitled')
                url = a.get('url', '')
                if url:
                    bullet_lines.append(f"• {title_txt} ([source]({url}))")
                else:
                    bullet_lines.append(f"• {title_txt}")
            body = '\n'.join(bullet_lines)
            header = base_header
        else:
            # Original formatting path
            full_msg = format_summary_message(summary, articles, topic)
            # split header/body heuristically (first line header assumption)
            header, body = full_msg.split('\n', 1) if '\n' in full_msg else (full_msg, '')
            body = body.strip()

        # Chunking logic (do not split single article / bullet). Bullets start with '•' or blank lines separate sections.
        def split_body(h: str, b: str) -> List[str]:
            if not b:
                return [h]
            lines = b.splitlines()
            chunks = []
            current: List[str] = []
            for line in lines:
                prospective = '\n'.join(current + [line])
                # +2 for spacing between header and body
                if len(h) + 2 + len(prospective) > MAX_MESSAGE_LENGTH and current:
                    chunks.append('\n'.join(current))
                    current = [line]
                else:
                    current.append(line)
            if current:
                chunks.append('\n'.join(current))
            return [h + "\n\n" + c for c in chunks] if chunks else [h]

        messages = split_body(header, body)
        total = len(messages)
        if total > 1:
            for idx in range(total):
                # Append continuation marker except maybe first
                if idx == 0:
                    continue  # keep first as-is
                # Split existing header from body to re-add continuation note
                parts = messages[idx].split('\n\n', 1)
                hdr = parts[0]
                body_part = parts[1] if len(parts) > 1 else ''
                hdr += f" (part {idx+1}/{total})"
                messages[idx] = hdr + "\n\n" + body_part

        for interface_name in interfaces_to_use:
            if interface_name not in self.interfaces_config:
                self.logger.warning(f"Interface '{interface_name}' not found in configuration")
                continue
            interface_config = self.interfaces_config[interface_name]
            interface_module = self._import_module("interfaces", interface_config["module"])
            if not interface_module:
                continue
            try:
                for msg in messages:
                    if self.dry_run:
                        self.logger.info(f"[DRY RUN] Would send via {interface_name} (len={len(msg)}):")
                        self.logger.info(f"Message preview: {msg[:200]}...")
                    else:
                        self.logger.info(f"Sending message chunk via {interface_name} (len={len(msg)})")
                        interface_module.send(msg, topic, interface_config)
                if not self.dry_run:
                    self.logger.info(f"All {total} message chunk(s) sent via {interface_name}")
            except Exception as e:
                self.logger.error(f"Error sending via {interface_name}: {e}", exc_info=True)

    def run(self, topics: List[str] = None, providers: List[str] = None,
            processor: str = "mistral", interfaces: List[str] = None,
            article_limit: int = None, save_only: bool = False, title_only: bool = False,
            exclude_providers: Optional[List[str]] = None, title_only_with_description: bool = False) -> bool:
        """Run the complete news summary pipeline.

        title_only: when True, skip processor and send only article titles as Telegram-compatible links.
        title_only_with_description: like title_only but include short article description/summary snippet.
        exclude_providers: providers to omit even if present/enabled.
        """
        try:
            topics = topics or ["general"]

            # Step 1: Fetch articles
            articles = self._fetch_articles(providers, topics, article_limit, exclude=exclude_providers)

            if not articles:
                self.logger.warning("No articles fetched. Exiting.")
                return False

            # Save articles to database
            self.logger.info(f"Saving {len(articles)} articles to database")
            db_save_result = db_utils.save_articles(articles)
            if not db_save_result:
                self.logger.error("Failed to persist articles to database.")
                if save_only or title_only or title_only_with_description:
                    return False
                else:
                    self.logger.warning("Continuing without DB persistence; summaries will not be queryable later.")

            # If save_only mode, stop here
            if save_only:
                self.logger.info("Save-only mode. Skipping processing and delivery.")
                return db_save_result

            # Title-only with description mode
            if title_only_with_description:
                self.logger.info("Title-only-with-description mode enabled: skipping summarization and sending titles with short descriptions")
                sent_urls = db_utils.get_already_sent_urls()
                if sent_urls:
                    self.logger.info(f"Found {len(sent_urls)} previously sent article URLs; filtering duplicates")
                articles_by_topic = {}
                for article in articles:
                    if article.get('url') and article['url'] in sent_urls:
                        continue
                    article_topic = article.get('topic', 'general')
                    articles_by_topic.setdefault(article_topic, []).append(article)
                if not any(articles_by_topic.values()):
                    self.logger.info("No new articles to send (all already sent).")
                    return True
                sent_article_ids = []
                for topic, topic_articles in articles_by_topic.items():
                    if topic.lower() not in [t.lower() for t in topics]:
                        continue
                    if not topic_articles:
                        continue
                    lines = []
                    for a in topic_articles:
                        title = a.get('title', 'Untitled')
                        url = a.get('url', '')
                        desc = (a.get('content') or '').strip().split('\n')[0][:160].strip()
                        if url:
                            lines.append(f"• [{title}]({url})\n  - {desc}" if desc else f"• [{title}]({url})")
                        else:
                            lines.append(f"• {title}\n  - {desc}" if desc else f"• {title}")
                        if a.get('id'):
                            sent_article_ids.append(a['id'])
                    summary_text = '\n'.join(lines)
                    self._deliver_summary(summary_text, topic_articles, topic, interfaces, title_only_with_description=True)
                db_utils.mark_telegram_sent(sent_article_ids)
                return True

            # Existing title-only mode
            if title_only:
                self.logger.info("Title-only mode enabled: skipping summarization and sending titles with links")
                sent_urls = db_utils.get_already_sent_urls()
                if sent_urls:
                    self.logger.info(f"Found {len(sent_urls)} previously sent article URLs; filtering duplicates")
                articles_by_topic = {}
                for article in articles:
                    if article.get('url') and article['url'] in sent_urls:
                        continue
                    article_topic = article.get('topic', 'general')
                    articles_by_topic.setdefault(article_topic, []).append(article)
                if not any(articles_by_topic.values()):
                    self.logger.info("No new articles to send (all already sent).")
                    return True
                sent_article_ids = []
                for topic, topic_articles in articles_by_topic.items():
                    if topic.lower() not in [t.lower() for t in topics]:
                        continue
                    if not topic_articles:
                        continue
                    lines = []
                    for a in topic_articles:
                        title = a.get('title', 'Untitled')
                        url = a.get('url', '')
                        if url:
                            lines.append(f"• [{title}]({url})")
                        else:
                            lines.append(f"• {title}")
                        if a.get('id'):
                            sent_article_ids.append(a['id'])
                    summary_text = '\n'.join(lines)
                    self._deliver_summary(summary_text, topic_articles, topic, interfaces, title_only=True)
                db_utils.mark_telegram_sent(sent_article_ids)
                return True

            # Process and save each article individually (IDs now present if DB save succeeded)
            processed_articles = self._process_articles(articles, processor)

            if not processed_articles:
                self.logger.warning("No articles were successfully processed.")
                return False

            # Group processed articles by topic for delivery
            articles_by_topic = {}
            for article in processed_articles:
                article_topic = article.get('topic', 'general')
                if article_topic not in articles_by_topic:
                    articles_by_topic[article_topic] = []
                articles_by_topic[article_topic].append(article)

            # Deliver summaries for each topic
            for topic, topic_articles in articles_by_topic.items():
                if topic.lower() not in [t.lower() for t in topics]:
                    continue

                self.logger.info(f"Delivering summary for topic: {topic} ({len(topic_articles)} articles)")

                try:
                    # Prepare combined summary from individual article summaries
                    summaries = [article.get('summary', '') for article in topic_articles]
                    combined_summary = "\n\n---\n\n".join(summaries)

                    # Deliver summary
                    self._deliver_summary(combined_summary, topic_articles, topic, interfaces, processor_mode=True)
                    # Mark as sent
                    ids_to_mark = [a['id'] for a in topic_articles if a.get('id')]
                    db_utils.mark_telegram_sent(ids_to_mark)

                except Exception as e:
                    self.logger.error(f"Error delivering topic {topic}: {e}", exc_info=True)
                    continue

            return True

        except Exception as e:
            self.logger.error(f"Fatal error in news runner: {e}", exc_info=True)
            return False
            
    def run_batch_process(self, hours: int = 6, processor: str = "mistral", 
                        interfaces: List[str] = None, article_limit: int = None) -> bool:
        """Process articles from database and generate summaries.
        
        This method is designed to be run periodically (e.g., every 6 hours) to process
        all articles collected during that time period. Each article is processed individually.
        """
        try:
            self.logger.info(f"Starting batch processing of articles from the last {hours} hours")
            
            # Get unprocessed articles from database
            articles = db_utils.get_unprocessed_articles(hours, article_limit)
            
            if not articles:
                self.logger.info("No unprocessed articles found. Exiting.")
                return True
                
            self.logger.info(f"Retrieved {len(articles)} articles for batch processing")
            
            # Process each article individually
            processed_articles = self._process_articles(articles, processor)
            
            if not processed_articles:
                self.logger.warning("No articles were successfully processed.")
                return False
            
            # Group processed articles by topic for delivery
            articles_by_topic = {}
            for article in processed_articles:
                article_topic = article.get('topic', 'general')
                if article_topic not in articles_by_topic:
                    articles_by_topic[article_topic] = []
                articles_by_topic[article_topic].append(article)
            
            # Deliver summaries for each topic
            for topic, topic_articles in articles_by_topic.items():
                self.logger.info(f"Delivering summary for topic: {topic} ({len(topic_articles)} articles)")
                
                try:
                    # Prepare combined summary from individual article summaries
                    summaries = [article.get('summary', '') for article in topic_articles]
                    combined_summary = "\n\n---\n\n".join(summaries)
                    
                    # Deliver summary
                    self._deliver_summary(combined_summary, topic_articles, topic, interfaces)
                    
                except Exception as e:
                    self.logger.error(f"Error delivering topic {topic}: {e}", exc_info=True)
                    continue
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fatal error in batch processing: {e}", exc_info=True)
            return False
