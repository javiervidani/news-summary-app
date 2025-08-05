# 📰 News Summary MCP Agent - Installation & Usage Guide

A comprehensive guide for setting up, configuring, and using the Modular News Summary System with MCP Agent.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Installation with UV](#installation-with-uv)
3. [Configuration](#configuration)
4. [Running the System](#running-the-system)
5. [MCP Agent Commands](#mcp-agent-commands)
6. [Running as a Service](#running-as-a-service)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Configuration](#advanced-configuration)

## System Requirements

- **Operating System**: Linux (recommended), macOS, or Windows
- **Python**: 3.9+ (3.11 recommended)
- **RAM**: 2GB minimum (4GB+ recommended)
- **Disk Space**: 500MB for application + 2GB for Mistral model (if running locally)
- **Optional**: Docker for containerized deployment

## Installation with UV

### What is UV?

[UV](https://github.com/astral-sh/uv) is a new, extremely fast Python package installer and resolver built in Rust. It dramatically speeds up dependency installation (10-100x faster than pip) and provides better resolution logic.

### Automated Installation

The fastest way to get started is using our setup script:

```bash
# Clone the repository
git clone https://github.com/yourusername/news-summary-app.git
cd news-summary-app

# Run the setup script (installs UV if needed)
chmod +x setup.sh
./setup.sh
```

### Manual Installation

1. **Install UV**

   ```bash
   # Install UV globally
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Create Virtual Environment**

   ```bash
   # Navigate to project directory
   cd news-summary-app
   
   # Create a virtual environment with UV
   uv venv
   
   # Activate the environment (Linux/Mac)
   source .venv/bin/activate
   
   # Activate the environment (Windows)
   .venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   # Basic installation
   uv sync
   
   # With database support
   uv sync --extra database
   
   # With all optional features
   uv sync --extra all
   ```

4. **Create Environment File**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   nano .env
   ```

## Configuration

### Required Configuration

At minimum, you need to configure:

1. **Telegram Bot** (for notifications):
   - Create a bot with [@BotFather](https://t.me/BotFather)
   - Get your chat ID (use [@userinfobot](https://t.me/userinfobot))
   - Add to `.env`:
     ```
     # Basic configuration
     TELEGRAM_BOT_TOKEN=your_bot_token
     TELEGRAM_CHAT_ID=your_chat_id
     
     # Optional: Category-specific channels
     TELEGRAM_CHAT_ID_SPORTS=sports_channel_id
     TELEGRAM_CHAT_ID_POLITICS=politics_channel_id
     TELEGRAM_CHAT_ID_TECH=tech_channel_id
     
     # Optional: Title-only mode (true/false)
     TELEGRAM_TITLE_ONLY=false
     ```

2. **LLM Configuration** (for summarization):
   - For local Mistral:
     ```bash
     # Install Ollama
     curl -fsSL https://ollama.ai/install.sh | sh
     
     # Pull Mistral model
     ollama pull mistral
     
     # Run Mistral (keep running in a separate terminal)
     ollama run mistral
     ```
   - Or for OpenAI:
     ```
     OPENAI_API_KEY=your_api_key
     ```

### Database Setup (Optional)

For persistent storage with vector search capabilities:

```bash
# Run PostgreSQL with Docker
docker run -d \
  --name postgres-news \
  -e POSTGRES_DB=mcp \
  -e POSTGRES_USER=mcp_app \
  -e POSTGRES_PASSWORD=mcp_123456 \
  -p 5433:5432 \
  postgres:latest

# Install pgvector extension (connect to container)
docker exec -it postgres-news psql -U mcp_app -d mcp -c "CREATE SCHEMA news_summary; CREATE EXTENSION IF NOT EXISTS vector;"
```

## Running the System

### Basic Usage

```bash
# Run with default settings (fetches general news, uses Mistral)
uv run python main.py

# Fetch specific news topics
uv run python main.py --topics world business technology

# Use specific providers
uv run python main.py --providers bbc nyt

# Test run without sending notifications
uv run python main.py --dry-run
```

### Advanced Usage

```bash
# Fetch and save articles without processing
uv run python main.py --save-only

# Process articles from database in batch mode
uv run python main.py --batch-process --hours 12

# Limit the number of articles per provider
uv run python main.py --limit 5
```

## MCP Agent Commands

The MCP Agent provides an intelligent interface for managing news sources.

### Using the CLI Interface

```bash
# List available news sources
uv run python agent_cli.py list-sources

# Add a new source
uv run python agent_cli.py add-source "CNN" --url "http://rss.cnn.com/rss/edition.rss"

# Check health of sources
uv run python agent_cli.py health-check

# Process a natural language command
uv run python agent_cli.py command "Add Reuters as a news source"
```

### Using the Telegram Interface

The agent can also be controlled via Telegram:

1. Start the agent interface:
   ```bash
   uv run python agent_run.py
   ```

2. Send commands to your bot:
   - `/help` - Show available commands
   - `/sources` - List available sources
   - `/add CNN` - Add a new source
   - `/summarize politics` - Generate summary for a topic

## Running as a Service

### Creating a Systemd Service

1. Create service file:
   ```bash
   sudo nano /etc/systemd/system/news-agent.service
   ```

2. Add this content:
   ```ini
   [Unit]
   Description=News Summary MCP Agent
   After=network.target

   [Service]
   Type=simple
   User=your_username
   WorkingDirectory=/full/path/to/news-summary-app
   ExecStart=/full/path/to/news-summary-app/.venv/bin/python /full/path/to/news-summary-app/agent_run.py
   Restart=on-failure
   RestartSec=10
   Environment=PYTHONUNBUFFERED=1

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable news-agent
   sudo systemctl start news-agent
   sudo systemctl status news-agent
   ```

### Creating a Cron Schedule

For periodic news updates without running the full agent:

```bash
crontab -e
```

Add schedules:
```
# Morning briefing (8 AM)
0 8 * * * cd /path/to/news-summary-app && /path/to/news-summary-app/.venv/bin/python /path/to/news-summary-app/main.py --topics general world

# Technology update (noon)
0 12 * * * cd /path/to/news-summary-app && /path/to/news-summary-app/.venv/bin/python /path/to/news-summary-app/main.py --topics technology

# Evening summary (6 PM)
0 18 * * * cd /path/to/news-summary-app && /path/to/news-summary-app/.venv/bin/python /path/to/news-summary-app/main.py --topics general business
```

## Troubleshooting

### Common Issues

1. **UV Not Found**
   ```bash
   # Verify installation
   which uv
   # Reinstall if needed
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Mistral Connection Error**
   ```bash
   # Check if Ollama is running
   ps aux | grep ollama
   # Restart Ollama
   ollama run mistral
   ```

3. **Telegram Bot Not Working**
   ```bash
   # Test Telegram connection
   curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
     -d "chat_id=${TELEGRAM_CHAT_ID}" \
     -d "text=Test message from News Summary App"
   ```

4. **Database Connection Issues**
   ```bash
   # Check PostgreSQL container
   docker ps | grep postgres
   # Check logs
   docker logs postgres-news
   ```

### Logs

```bash
# Check application logs
tail -f data/logs/news_summary_$(date +%Y%m%d).log

# Check agent logs
tail -f data/logs/agent.log

# If running as a service
sudo journalctl -u news-agent -f
```

## Advanced Configuration

### Customizing the MCP Agent

The MCP Agent can be customized by editing:

- **Command Patterns**: Modify `agent/command_parser.py` to add new command patterns
- **Provider Templates**: Edit templates in `agent/templates/` to change how new providers are generated
- **Monitoring Settings**: Adjust source health checks in `agent/monitor.py`

### Telegram Channel Configuration

#### Category-Based Routing

You can send news articles to different Telegram channels based on their categories:

1. **Create multiple channels or groups** in Telegram
2. **Get chat IDs** for each channel (forward a message from the channel to [@userinfobot](https://t.me/userinfobot))
3. **Configure environment variables**:
   ```
   # Main default channel
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_default_chat_id
   
   # Category-specific channels
   TELEGRAM_CHAT_ID_SPORTS=sports_channel_id
   TELEGRAM_CHAT_ID_POLITICS=politics_channel_id
   TELEGRAM_CHAT_ID_TECH=tech_channel_id
   ```

4. **Customize categories** by editing `interfaces/telegram.py` if needed

#### Title-Only Mode

You can configure the system to send only article titles instead of full summaries:

1. **Enable globally** by setting `TELEGRAM_TITLE_ONLY=true` in your environment
2. **Configure in JSON** by adding to your interface config:
   ```json
   {
     "interfaces": {
       "telegram": {
         "config": {
           "title_only": true
         }
       }
     }
   }
   ```

### Performance Tuning

For better performance with multiple sources:

1. Edit `.env` file:
   ```
   # Increase timeout for large feeds
   RSS_TIMEOUT=60
   # Increase retries for unreliable sources
   RSS_RETRIES=5
   ```

2. Adjust database connections in `core/db_utils.py`

### Adding Custom Providers

To manually add a new provider:

1. Create file in `providers/` directory
2. Implement the provider class and `fetch_articles()` function
3. Add to `config/providers.json`

Example:
```python
# providers/custom_provider.py
from typing import List, Dict, Any
import requests
from .base_provider import BaseProvider

class CustomProvider(BaseProvider):
    def __init__(self, config):
        super().__init__(config)
        self.url = config.get('url')
        
    def fetch_articles(self):
        # Fetch and process articles
        return [{"title": "...", "content": "...", "url": "...", "topic": "..."}]

# Module entry point
def fetch_articles():
    config = {"url": "https://example.com/feed"}
    provider = CustomProvider(config)
    return provider.fetch_articles()
```

---

**For more information and updates, visit our GitHub repository.**
