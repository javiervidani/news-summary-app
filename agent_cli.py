#!/usr/bin/env python3
"""
Command-line interface for the News Agent system.
Allows interaction with the MCP and other agent components.
"""

import os
import sys
import asyncio
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import MCP
from agent.mcp import MasterControlProgram

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

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

async def process_command(args):
    """Process a command using the MCP."""
    mcp = MasterControlProgram()
    response = await mcp.process_command(args.command)
    print(response)

async def add_source(args):
    """Add a new source."""
    mcp = MasterControlProgram()
    response = await mcp.add_new_source(args.name, args.url)
    print(response)

async def list_sources(args):
    """List available sources."""
    mcp = MasterControlProgram()
    response = await mcp.list_sources()
    print(response)

async def health_check(args):
    """Run a health check on sources."""
    from agent.monitor import SourceMonitor
    monitor = SourceMonitor()
    mcp = MasterControlProgram()
    
    # Start monitoring for a quick check
    await monitor.start(mcp.providers)
    
    # Stop after a short while
    await asyncio.sleep(5)
    await monitor.stop()
    
    # Get and print report
    report = monitor.get_health_report()
    
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("\nSource Health Report:")
        print(f"Time: {report['timestamp']}")
        print("\nSources:")
        for name, data in report['sources'].items():
            print(f"- {name}: {data['status']}")
            print(f"  Availability: {data['availability']:.1f}%")
            print(f"  Last check: {data['last_check']}")
            if data['status'] != 'UP':
                print(f"  Consecutive failures: {data['consecutive_failures']}")
            print()

async def list_tasks(args):
    """List scheduled tasks."""
    from agent.dispatcher import TaskDispatcher
    dispatcher = TaskDispatcher()
    
    # Initialize with providers
    mcp = MasterControlProgram()
    
    # Set up tasks without starting the loop
    dispatcher._setup_tasks(mcp.providers)
    
    # Get and print status
    status = dispatcher.get_tasks_status()
    
    if args.json:
        print(json.dumps(status, indent=2))
    else:
        print("\nScheduled Tasks:")
        for name, data in status.items():
            print(f"- {name}")
            print(f"  Interval: {data['interval_minutes']} minutes")
            print(f"  Last run: {data['last_run'] or 'Never'}")
            print(f"  Next run: {data['next_run'] or 'Now'}")
            print(f"  Status: {'Running' if data['running'] else 'Idle'}")
            print()

def main():
    """Main entry point."""
    # Load environment variables
    load_env_file()
    
    # Set up logging
    setup_logging()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='News Agent CLI')
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')
    
    # Command processor
    cmd_parser = subparsers.add_parser('command', help='Process a natural language command')
    cmd_parser.add_argument('command', help='The command to process')
    
    # Add source
    add_parser = subparsers.add_parser('add-source', help='Add a new news source')
    add_parser.add_argument('name', help='Name of the news source')
    add_parser.add_argument('--url', help='URL of the RSS feed')
    
    # List sources
    list_parser = subparsers.add_parser('list-sources', help='List available sources')
    
    # Health check
    health_parser = subparsers.add_parser('health-check', help='Run a health check on sources')
    health_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    # List tasks
    tasks_parser = subparsers.add_parser('list-tasks', help='List scheduled tasks')
    tasks_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    args = parser.parse_args()
    
    # Handle actions
    if args.action == 'command':
        asyncio.run(process_command(args))
    elif args.action == 'add-source':
        asyncio.run(add_source(args))
    elif args.action == 'list-sources':
        asyncio.run(list_sources(args))
    elif args.action == 'health-check':
        asyncio.run(health_check(args))
    elif args.action == 'list-tasks':
        asyncio.run(list_tasks(args))
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
