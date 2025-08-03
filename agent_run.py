#!/usr/bin/env python3
"""
Start the Master Control Program (MCP) Agent for autonomous operation.
This script starts the core components of the agent system.
"""

import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import components
from agent.mcp import MasterControlProgram
from agent.monitor import SourceMonitor
from agent.dispatcher import TaskDispatcher
from interfaces.telegram_command import TelegramCommandInterface

def load_env_file(env_file='.env'):
    """Load environment variables from .env file."""
    if not os.path.exists(env_file):
        return False
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('\'"')
    
    return True

def setup_logging(log_level='INFO'):
    """Set up logging configuration."""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/logs/agent.log')
        ]
    )

async def run_agent(telegram=True, monitor=True, scheduler=True):
    """
    Run the MCP agent system.
    
    Args:
        telegram: Whether to start the Telegram interface
        monitor: Whether to start the source monitor
        scheduler: Whether to start the task scheduler
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting MCP Agent System")
    
    try:
        # Initialize MCP
        mcp = MasterControlProgram()
        
        # Start components
        tasks = []
        
        if telegram:
            logger.info("Starting Telegram interface")
            telegram_bot = TelegramCommandInterface()
            tasks.append(asyncio.create_task(telegram_bot.start_polling()))
        
        if monitor:
            logger.info("Starting source monitor")
            source_monitor = SourceMonitor()
            tasks.append(asyncio.create_task(source_monitor.start(mcp.providers)))
        
        if scheduler:
            logger.info("Starting task scheduler")
            task_dispatcher = TaskDispatcher()
            tasks.append(asyncio.create_task(task_dispatcher.start(mcp.providers)))
        
        # Wait for all tasks to complete (they should run indefinitely)
        await asyncio.gather(*tasks)
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Error in agent system: {e}")
        return 1
    
    return 0

def main():
    """Main entry point."""
    # Load environment variables
    load_env_file()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='MCP Agent System')
    parser.add_argument('--no-telegram', action='store_true', help='Disable Telegram interface')
    parser.add_argument('--no-monitor', action='store_true', help='Disable source monitor')
    parser.add_argument('--no-scheduler', action='store_true', help='Disable task scheduler')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                      help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level)
    
    # Run the agent system
    return asyncio.run(run_agent(
        telegram=not args.no_telegram,
        monitor=not args.no_monitor,
        scheduler=not args.no_scheduler
    ))

if __name__ == '__main__':
    sys.exit(main())
