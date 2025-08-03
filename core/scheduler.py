"""
Scheduler for automated news summary runs.
Supports cron-like scheduling and time-based triggers.
"""

import logging
import schedule
import time
import threading
from datetime import datetime, time as dt_time
from typing import List, Callable, Optional

from .runner import NewsRunner


class NewsScheduler:
    """Scheduler for automated news summary execution."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.thread = None
        
    def schedule_daily(self, times: List[str], topics: List[str] = None,
                      processor: str = "mistral") -> None:
        """
        Schedule daily runs at specified times.
        
        Args:
            times: List of time strings in HH:MM format (e.g., ["08:00", "12:00", "18:00"])
            topics: Topics to process
            processor: Processor to use
        """
        topics = topics or ["general"]
        
        for time_str in times:
            try:
                # Validate time format
                hour, minute = map(int, time_str.split(':'))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError(f"Invalid time: {time_str}")
                
                # Schedule the job
                schedule.every().day.at(time_str).do(
                    self._run_summary,
                    topics=topics,
                    processor=processor
                )
                
                self.logger.info(f"Scheduled daily run at {time_str} for topics: {topics}")
                
            except ValueError as e:
                self.logger.error(f"Invalid time format '{time_str}': {e}")
    
    def schedule_interval(self, hours: int, topics: List[str] = None,
                         processor: str = "mistral") -> None:
        """
        Schedule runs every N hours.
        
        Args:
            hours: Interval in hours
            topics: Topics to process
            processor: Processor to use
        """
        topics = topics or ["general"]
        
        schedule.every(hours).hours.do(
            self._run_summary,
            topics=topics,
            processor=processor
        )
        
        self.logger.info(f"Scheduled runs every {hours} hours for topics: {topics}")
    
    def schedule_weekday_morning(self, time_str: str = "08:00",
                                topics: List[str] = None,
                                processor: str = "mistral") -> None:
        """Schedule morning briefings on weekdays."""
        topics = topics or ["general", "business", "technology"]
        
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            getattr(schedule.every(), day).at(time_str).do(
                self._run_summary,
                topics=topics,
                processor=processor
            )
        
        self.logger.info(f"Scheduled weekday morning briefings at {time_str}")
    
    def _run_summary(self, topics: List[str], processor: str) -> None:
        """Execute a news summary run."""
        self.logger.info(f"Executing scheduled run for topics: {topics}")
        
        try:
            runner = NewsRunner(config_dir=self.config_dir)
            success = runner.run(topics=topics, processor=processor)
            
            if success:
                self.logger.info("Scheduled run completed successfully")
            else:
                self.logger.error("Scheduled run failed")
                
        except Exception as e:
            self.logger.error(f"Error in scheduled run: {e}", exc_info=True)
    
    def start(self) -> None:
        """Start the scheduler in a background thread."""
        if self.running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        self.logger.info("Scheduler started")
    
    def stop(self) -> None:
        """Stop the scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("Scheduler stopped")
    
    def _run_scheduler(self) -> None:
        """Main scheduler loop."""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                time.sleep(60)
    
    def list_jobs(self) -> List[str]:
        """List all scheduled jobs."""
        jobs = []
        for job in schedule.jobs:
            jobs.append(str(job))
        return jobs
    
    def clear_jobs(self) -> None:
        """Clear all scheduled jobs."""
        schedule.clear()
        self.logger.info("All scheduled jobs cleared")


def create_sample_schedule(scheduler: NewsScheduler) -> None:
    """Create a sample schedule configuration."""
    # Morning briefing
    scheduler.schedule_weekday_morning("08:00", ["general", "business"], "mistral")
    
    # Lunch update
    scheduler.schedule_daily(["12:30"], ["technology", "world"], "mistral")
    
    # Evening summary
    scheduler.schedule_daily(["18:00"], ["general"], "mistral")
    
    # Weekend summary
    schedule.every().saturday.at("10:00").do(
        scheduler._run_summary,
        topics=["general", "entertainment"],
        processor="mistral"
    )
