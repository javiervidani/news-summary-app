"""
Task Dispatcher for scheduling and managing tasks in the news system.
Handles periodic fetching, processing, and other recurring tasks.
"""

import logging
import asyncio
import os
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List, Callable, Optional, Tuple

logger = logging.getLogger(__name__)

class Task:
    """Represents a scheduled task."""
    
    def __init__(self, name: str, interval_minutes: int, command: str, args: List[str] = None):
        self.name = name
        self.interval_minutes = interval_minutes
        self.command = command
        self.args = args or []
        self.last_run = None
        self.running = False
        self.consecutive_failures = 0
        
    @property
    def next_run(self) -> Optional[datetime]:
        """Calculate when the task should run next."""
        if self.last_run is None:
            return datetime.now()
        return self.last_run + timedelta(minutes=self.interval_minutes)
        
    @property
    def should_run(self) -> bool:
        """Check if the task should run now."""
        if self.running:
            return False
            
        if self.last_run is None:
            return True
            
        now = datetime.now()
        return now >= self.next_run


class TaskDispatcher:
    """Dispatcher for scheduling and executing tasks."""
    
    def __init__(self):
        """Initialize the task dispatcher."""
        logger.info("Initializing Task Dispatcher")
        self.tasks = {}
        self.running = False
        self.check_interval = 60  # Seconds
        
        # Set up Python executable
        self.python_executable = os.environ.get('PYTHON_EXECUTABLE', 'python3')
        
        # Get configuration from environment
        self.fetch_interval = int(os.environ.get('FETCH_INTERVAL_MINUTES', '30'))
        self.summary_interval = int(os.environ.get('SUMMARY_INTERVAL_HOURS', '6')) * 60  # Convert to minutes
        self.article_limit = os.environ.get('ARTICLE_LIMIT', '')
        
    async def start(self, sources: Dict[str, Any]):
        """Start task scheduling."""
        logger.info("Starting task scheduler")
        self.running = True
        
        # Initialize tasks
        self._setup_tasks(sources)
        
        # Start the scheduling loop
        await self._scheduling_loop()
        
    async def stop(self):
        """Stop the task scheduler."""
        logger.info("Stopping task scheduler")
        self.running = False
        
    def _setup_tasks(self, sources: Dict[str, Any]):
        """Set up default tasks."""
        logger.info("Setting up scheduled tasks")
        
        # Create fetch tasks for each enabled source
        for name, config in sources.items():
            if config.get('enabled', True):
                task_name = f"fetch_{name}"
                command = self.python_executable
                args = [
                    'main.py',
                    '--providers', name,
                    '--save-only'
                ]
                
                # Add article limit if specified
                if self.article_limit:
                    args.extend(['--limit', self.article_limit])
                    
                self.tasks[task_name] = Task(
                    name=task_name,
                    interval_minutes=self.fetch_interval,
                    command=command,
                    args=args
                )
                logger.info(f"Created fetch task for {name}")
        
        # Create summary task
        self.tasks['generate_summaries'] = Task(
            name='generate_summaries',
            interval_minutes=self.summary_interval,
            command=self.python_executable,
            args=[
                'main.py',
                '--batch-process',
                f'--hours={self.summary_interval // 60}'
            ]
        )
        logger.info("Created summary generation task")
        
        # Create health check task
        self.tasks['health_check'] = Task(
            name='health_check',
            interval_minutes=60,  # Hourly health check
            command=self.python_executable,
            args=[
                'agent_cli.py',  # We'll create this later
                'health-check'
            ]
        )
        logger.info("Created health check task")
        
    async def _scheduling_loop(self):
        """Main scheduling loop."""
        logger.info(f"Scheduling loop started, checking every {self.check_interval} seconds")
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check each task
                for task_name, task in self.tasks.items():
                    if task.should_run:
                        # Run the task in a separate coroutine
                        asyncio.create_task(self._run_task(task))
                        
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in scheduling loop: {e}")
                await asyncio.sleep(self.check_interval)
                
    async def _run_task(self, task: Task):
        """Run a task."""
        if task.running:
            return
            
        task.running = True
        task.last_run = datetime.now()
        
        logger.info(f"Running task: {task.name}")
        
        try:
            # Build the command
            cmd = [task.command] + task.args
            
            # Run the command
            logger.info(f"Executing: {' '.join(cmd)}")
            
            # Use asyncio subprocess
            proc = await asyncio.create_subprocess_exec(
                task.command,
                *task.args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for the command to finish
            stdout, stderr = await proc.communicate()
            
            # Process the result
            if proc.returncode != 0:
                logger.error(f"Task {task.name} failed with code {proc.returncode}")
                logger.error(f"Stderr: {stderr.decode()}")
                task.consecutive_failures += 1
            else:
                logger.info(f"Task {task.name} completed successfully")
                task.consecutive_failures = 0
                
        except Exception as e:
            logger.error(f"Error running task {task.name}: {e}")
            task.consecutive_failures += 1
            
        finally:
            task.running = False
            
    def add_task(self, name: str, interval_minutes: int, command: str, args: List[str] = None) -> bool:
        """Add a new task to the scheduler."""
        if name in self.tasks:
            logger.warning(f"Task {name} already exists")
            return False
            
        self.tasks[name] = Task(name, interval_minutes, command, args)
        logger.info(f"Added new task: {name}")
        return True
        
    def remove_task(self, name: str) -> bool:
        """Remove a task from the scheduler."""
        if name not in self.tasks:
            logger.warning(f"Task {name} not found")
            return False
            
        del self.tasks[name]
        logger.info(f"Removed task: {name}")
        return True
        
    def get_tasks_status(self) -> Dict[str, Any]:
        """Get status of all tasks."""
        status = {}
        now = datetime.now()
        
        for name, task in self.tasks.items():
            next_run = task.next_run
            time_to_next = (next_run - now).total_seconds() if next_run else 0
            
            status[name] = {
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "next_run": next_run.isoformat() if next_run else None,
                "interval_minutes": task.interval_minutes,
                "running": task.running,
                "failures": task.consecutive_failures,
                "minutes_to_next_run": round(time_to_next / 60, 1) if time_to_next > 0 else 0
            }
            
        return status
