"""
Source Monitor for tracking health and reliability of news sources.
Monitors uptime, article frequency, and source quality.
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
import importlib
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class SourceHealth:
    """Data class for tracking source health metrics."""
    
    def __init__(self, name: str):
        self.name = name
        self.last_check = None
        self.last_success = None
        self.consecutive_failures = 0
        self.total_failures = 0
        self.total_checks = 0
        self.article_counts = []
        self.response_times = []
        
    def update(self, success: bool, article_count: int, response_time: float):
        """Update health metrics after a check."""
        self.last_check = datetime.now()
        self.total_checks += 1
        
        if success:
            self.last_success = self.last_check
            self.consecutive_failures = 0
            self.article_counts.append(article_count)
            self.response_times.append(response_time)
        else:
            self.consecutive_failures += 1
            self.total_failures += 1
    
    @property
    def availability(self) -> float:
        """Calculate source availability percentage."""
        if self.total_checks == 0:
            return 0.0
        return (self.total_checks - self.total_failures) / self.total_checks * 100
    
    @property
    def avg_article_count(self) -> float:
        """Calculate average article count."""
        if not self.article_counts:
            return 0.0
        return sum(self.article_counts) / len(self.article_counts)
    
    @property
    def avg_response_time(self) -> float:
        """Calculate average response time."""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    @property
    def status(self) -> str:
        """Get current status string."""
        if self.consecutive_failures >= 5:
            return "DOWN"
        elif self.consecutive_failures >= 2:
            return "WARNING"
        else:
            return "UP"
    
    def __str__(self) -> str:
        """String representation of source health."""
        status = self.status
        avail = self.availability
        avg_count = self.avg_article_count
        avg_time = self.avg_response_time
        
        return f"{self.name}: {status} (Avail: {avail:.1f}%, Avg Articles: {avg_count:.1f}, Avg Time: {avg_time:.2f}s)"


class SourceMonitor:
    """Monitor for news source health and reliability."""
    
    def __init__(self):
        """Initialize the source monitor."""
        logger.info("Initializing Source Monitor")
        self.sources = {}
        self.health_data = {}
        self.running = False
        self.check_interval = 30  # Minutes
        
    async def start(self, sources: Dict[str, Any]):
        """Start monitoring news sources."""
        logger.info(f"Starting source monitoring for {len(sources)} sources")
        self.sources = sources
        self.running = True
        
        # Initialize health data
        for name in sources:
            self.health_data[name] = SourceHealth(name)
        
        # Start the monitoring loop
        await self._monitoring_loop()
        
    async def stop(self):
        """Stop monitoring."""
        logger.info("Stopping source monitoring")
        self.running = False
        
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        logger.info(f"Monitoring loop started, checking every {self.check_interval} minutes")
        
        while self.running:
            try:
                # Check each enabled source
                for name, config in self.sources.items():
                    if config.get("enabled", True):
                        await self._check_source(name, config)
                
                # Wait for next check interval
                logger.debug(f"Sleeping for {self.check_interval} minutes until next check")
                for _ in range(self.check_interval * 60):  # Convert to seconds
                    if not self.running:
                        break
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Sleep for a minute on error
                
    async def _check_source(self, name: str, config: Dict[str, Any]):
        """Check a single news source."""
        logger.info(f"Checking source: {name}")
        
        try:
            # Get the module name
            module_name = config.get("module", name)
            
            # Start timing
            start_time = time.time()
            
            # Try to import the module
            try:
                module_path = f"providers.{module_name}"
                provider_module = importlib.import_module(module_path)
            except ImportError as e:
                logger.error(f"Could not import provider module {module_path}: {e}")
                self.health_data[name].update(False, 0, 0)
                return
            
            # Try to fetch articles
            try:
                articles = provider_module.fetch_articles()
                success = True
                article_count = len(articles)
            except Exception as e:
                logger.error(f"Error fetching articles from {name}: {e}")
                success = False
                article_count = 0
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Update health data
            self.health_data[name].update(success, article_count, response_time)
            
            # Log the result
            logger.info(f"Source check: {name} - Success: {success}, Articles: {article_count}, Time: {response_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Unexpected error checking source {name}: {e}")
            self.health_data[name].update(False, 0, 0)
            
    def get_health_report(self) -> Dict[str, Any]:
        """Get a report of all source health data."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "sources": {}
        }
        
        for name, health in self.health_data.items():
            report["sources"][name] = {
                "status": health.status,
                "availability": health.availability,
                "consecutive_failures": health.consecutive_failures,
                "avg_article_count": health.avg_article_count,
                "avg_response_time": health.avg_response_time,
                "last_check": health.last_check.isoformat() if health.last_check else None,
                "last_success": health.last_success.isoformat() if health.last_success else None
            }
            
        return report
