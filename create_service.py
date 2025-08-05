#!/usr/bin/env python3
"""
Script to create and install a systemd service for the MCP agent.
"""

import os
import subprocess
import argparse
from pathlib import Path

def create_service_file(app_dir, user, python_path=None, service_name="news-agent"):
    """Create the systemd service file content"""
    
    # Use provided python path or default to virtual environment
    if not python_path:
        python_path = f"{app_dir}/.venv/bin/python"
    
    service_content = f"""[Unit]
Description=News Summary MCP Agent Service
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={app_dir}
ExecStart={python_path} {app_dir}/agent_run.py
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
    return service_content

def main():
    parser = argparse.ArgumentParser(description="Create a systemd service for the MCP agent")
    parser.add_argument('--user', default=os.getenv('USER'), help='User to run the service as')
    parser.add_argument('--python', help='Path to Python executable (default: uses virtualenv)')
    parser.add_argument('--install', action='store_true', help='Install the service file')
    parser.add_argument('--name', default="news-agent", help='Name of the service')
    args = parser.parse_args()
    
    # Get the absolute path to the app directory
    app_dir = str(Path(__file__).resolve().parent)
    
    # Create service file content
    service_content = create_service_file(app_dir, args.user, args.python, args.name)
    
    # Service filename
    service_filename = f"{args.name}.service"
    
    # Write service file
    service_path = Path(app_dir) / service_filename
    with open(service_path, "w") as f:
        f.write(service_content)
    
    print(f"Service file created at: {service_path}")
    
    # Install service if requested
    if args.install:
        if os.geteuid() != 0:
            print("Installing service requires root privileges. Please run with sudo.")
            return
            
        try:
            # Copy to systemd directory
            subprocess.run(["cp", service_path, f"/etc/systemd/system/{service_filename}"], check=True)
            
            # Reload systemd
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            
            print(f"Service {args.name} installed successfully!")
            print(f"To enable and start: sudo systemctl enable --now {args.name}")
            
        except subprocess.CalledProcessError as e:
            print(f"Error installing service: {e}")
    else:
        print("\nTo install the service, run with sudo:")
        print(f"sudo python3 {__file__} --install --user {args.user}")
        print("\nOr manually install with these commands:")
        print(f"sudo cp {service_path} /etc/systemd/system/")
        print("sudo systemctl daemon-reload")
        print(f"sudo systemctl enable {args.name}.service")
        print(f"sudo systemctl start {args.name}.service")
        print("\nTo check status:")
        print(f"sudo systemctl status {args.name}.service")

if __name__ == "__main__":
    main()
