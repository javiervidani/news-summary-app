# Modular News Summary System (MCP Agent-Driven)

A flexible, modular news aggregation and summarization system that fetches articles from multiple sources, processes them with AI models (local or cloud), and delivers summaries through various channels. The design supports dynamic addition of providers (news sources), processors (summarizers), and delivery interfaces (like Telegram), with minimal code changes.

> **🚀 Quick Start**: See [QUICKSTART.md](QUICKSTART.md) for UV-based setup in under 5 minutes!

## 🧠 MCP Agent Integration

The MCP server acts as a **controller** and **autonomous agent** that manages and extends the news system.

### 🧩 Core Behaviors
- Accepts user requests via **CLI or UI** like:
  > "Add support for website X News"

- The agent will:
  1. Plan the implementation (decide: is it RSS/API/scrape?)
  2. Generate code (provider module)
  3. **Prompt user to select LLM provider** (e.g., Mistral, OpenAI, Anthropic) for the new flow
  4. Try running it up to **3 times** (auto-debug)
  5. If it returns data, validate **data quality with GPT**
  6. If valid: auto-register the module in `providers.json`
  7. Save the module as a new job/extension

## 🚀 Features

- **Modular Architecture**: Easily add new news sources, AI processors, and delivery channels
- **Fast Package Management**: Uses UV for lightning-fast dependency management
- **Multiple News Sources**: BBC, NYT, Reuters, and more via RSS feeds
- **AI Summarization**: Local models (Mistral via Ollama) or cloud APIs (OpenAI)
- **Multiple Delivery Channels**: Telegram, Email, and extensible for more
- **Scheduled Execution**: Automated runs with cron-like scheduling
- **Vector Database Support**: PostgreSQL with pgvector for article storage and search
- **Topic Filtering**: Process specific news categories
- **Fallback Mechanisms**: Graceful degradation when services are unavailable

## ⚡ Why UV?

This project uses [UV](https://docs.astral.sh/uv/) for package management, providing:

- **10-100x faster** than pip for dependency resolution and installation
- **Unified tool** for managing Python versions, virtual environments, and dependencies
- **Lock file support** for reproducible builds
- **Better dependency resolution** with conflict detection
- **Cross-platform compatibility** with consistent behavior
- **Zero configuration** virtual environment management

## 📁 Project Structure

```
news-summary-app/
├── config/                  # Configuration files
│   ├── providers.json       # News source configurations
│   ├── processors.json      # AI processor configurations
│   └── interfaces.json      # Delivery channel configurations
├── providers/               # News source modules
│   ├── base_provider.py     # Base provider class
│   ├── bbc.py              # BBC RSS provider
│   └── nyt.py              # NYT RSS provider
├── processors/              # AI summarization modules
│   ├── base_processor.py    # Base processor class
│   ├── mistral_summary.py   # Local Mistral LLM
│   └── openai_summary.py    # OpenAI API
├── interfaces/              # Delivery channel modules
│   ├── base_interface.py    # Base interface class
│   ├── telegram.py          # Telegram bot
│   └── email.py             # Email delivery
├── core/                    # Core system components
│   ├── runner.py            # Main orchestrator
│   ├── scheduler.py         # Automated scheduling
│   └── utils.py             # Utility functions
├── data/                    # Data storage
│   ├── logs/                # Application logs
│   └── vectors/             # Vector embeddings (optional)
├── models/                     # Handles summarization models
│   ├── mistral_client.py
│   ├── openai_client.py
│   └── ...
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
└── .env.example            # Environment variables template
```

## 🛠️ Installation

### 1. Install UV (Fast Python Package Manager)

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv
```

### 2. Clone and Setup

```bash
cd news-summary-app
cp .env.example .env
```

### 3. Install Dependencies with UV

```bash
# Install core dependencies
uv sync

# Or install with all optional dependencies
uv sync --extra all

# Or install specific extras
uv sync --extra database --extra openai
```

### Alternative: Traditional pip installation

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Edit `.env` file with your credentials:

```bash
# Telegram (required for Telegram delivery)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# OpenAI (optional, for OpenAI processor)
OPENAI_API_KEY=your_openai_key

# Email (optional, for email delivery)
SMTP_SERVER=smtp.gmail.com
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

### 4. Setup Local Mistral (Recommended)

Install and run Ollama with Mistral:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull Mistral model
ollama pull mistral

# Run Mistral (keep this running in background)
ollama run mistral
```

## 🚀 Usage

### Basic Usage

```bash
# Activate UV virtual environment (if needed)
uv venv
source .venv/bin/activate  # On Linux/Mac
# or .venv\Scripts\activate  # On Windows

# Run with default settings (general news, Mistral processor, all enabled interfaces)
python main.py

# Or run directly with uv
uv run python main.py

# Specify topics
uv run python main.py --topics general business technology

# Use specific processor
uv run python main.py --processor openai

# Use specific providers
uv run python main.py --providers bbc nyt

# Dry run (no actual delivery)
uv run python main.py --dry-run
```

### Advanced Usage

```bash
# Business news only, via Telegram
uv run python main.py --topics business --interfaces telegram

# Multiple topics with specific providers
uv run python main.py --topics general world --providers bbc --processor mistral

# Debug mode with verbose logging
uv run python main.py --log-level DEBUG
```

### Scheduled Execution

Create a cron job for automated runs:

```bash
# Edit crontab
crontab -e

# Add entries for scheduled runs
# Morning briefing at 8 AM
0 8 * * * cd /path/to/news-summary-app && uv run python main.py --topics general business

# Lunch update at 12:30 PM
30 12 * * * cd /path/to/news-summary-app && uv run python main.py --topics technology

# Evening summary at 6 PM
0 18 * * * cd /path/to/news-summary-app && uv run python main.py --topics general
```

## ⚙️ Configuration

### Generic LLM Configuration (`config/llm.json`)

This system supports multiple LLM backends through a unified configuration:

```json
{
  "active_model": "mistral",
  "models": {
    "mistral": {
      "type": "local",
      "endpoint": "http://localhost:11434/api/generate",
      "model_name": "mistral"
    },
    "openai": {
      "type": "cloud",
      "endpoint": "https://api.openai.com/v1/chat/completions",
      "api_key": "YOUR_OPENAI_KEY",
      "model_name": "gpt-4"
    },
    "anthropic": {
      "type": "cloud",
      "endpoint": "https://api.anthropic.com/v1/messages",
      "api_key": "YOUR_ANTHROPIC_KEY",
      "model_name": "claude-3"
    }
  }
}
```

The system reads this file and uses `active_model` without changing the core code.

### Adding a New News Provider

1. Create `providers/your_provider.py`:

```python
def fetch_articles():
    return [
        {
            "title": "Article Title",
            "content": "Article content...",
            "url": "https://example.com/article",
            "topic": "general"
        }
    ]
```

2. Add to `config/providers.json`:

```json
{
  "your_provider": {
    "module": "your_provider",
    "type": "rss",
    "url": "https://example.com/rss",
    "enabled": true,
    "topics": ["general"]
  }
}
```

### Adding a New Processor

1. Create `processors/your_processor.py`:

```python
def summarize(content, config=None):
    # Your summarization logic
    return "Generated summary..."
```

2. Add to `config/processors.json`:

```json
{
  "your_processor": {
    "module": "your_processor",
    "type": "api",
    "enabled": true,
    "max_tokens": 300
  }
}
```

### Adding a New Interface

1. Create `interfaces/your_interface.py`:

```python
def send(message, topic, config):
    # Your delivery logic
    return True  # or False if failed
```

2. Add to `config/interfaces.json`:

```json
{
  "your_interface": {
    "module": "your_interface",
    "type": "messaging",
    "enabled": true,
    "config": {
      "api_key": "${YOUR_API_KEY}"
    }
  }
}
```

## 🗄️ Database Setup (Optional)

For PostgreSQL with vector search:

```sql
-- Create database
CREATE DATABASE news_summary;

-- Install vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create articles table
CREATE TABLE articles (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  url TEXT,
  topic TEXT NOT NULL,
  provider TEXT NOT NULL,
  embedding vector(384),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_articles_topic ON articles(topic);
CREATE INDEX idx_articles_provider ON articles(provider);
```

## 🧪 Testing

```bash
# Test configuration
uv run python main.py --dry-run

# Test specific components
uv run python -c "from providers.bbc import fetch_articles; print(len(fetch_articles()))"
uv run python -c "from processors.mistral_summary import summarize; print(summarize('Test content'))"

# Run tests with pytest (if available)
uv run pytest

# Run with coverage
uv run pytest --cov=providers --cov=processors --cov=interfaces --cov=core
```

## 📋 Troubleshooting

### Common Issues

1. **Mistral Connection Error**: Ensure Ollama is running (`ollama run mistral`)
docker pull ollama/ollama
docker run -d --name ollama-mistral -p 11434:11434 ollama/ollama
docker exec -it ollama-mistral ollama pull mistral

2. **Telegram Bot Not Working**: Check bot token and chat ID in `.env`
3. **RSS Feed Errors**: Some feeds may be temporarily unavailable
4. **Import Errors**: Install missing dependencies
   - With UV: `uv sync --extra all`
   - With pip: `pip install -r requirements.txt`

## � Flow Logic (Autonomous Extension)

1. User request triggers agent
2. Planner decides provider type
3. User selects LLM from `llm.json`
4. Agent generates and tests provider code (up to 3 retries)
5. GPT validates data quality
6. New provider is saved and registered

## �🔧 Development with UV

### Managing Dependencies

```bash
# Add a new dependency
uv add requests

# Add a development dependency
uv add --dev pytest

# Add an optional dependency to a specific group
uv add --optional database psycopg2-binary

# Update dependencies
uv sync

# Update specific package
uv add requests@latest
```

### Virtual Environment Management

```bash
# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install project in development mode
uv pip install -e .

# Run commands in the environment
uv run python main.py
uv run pytest
```

### Building and Publishing

```bash
# Build the package
uv build

# Install from local build
uv pip install dist/news_summary_app-*.whl
```

### Logs

Check logs in `data/logs/` for detailed error information:

```bash
tail -f data/logs/news_summary_$(date +%Y%m%d).log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your provider/processor/interface
4. Update configuration files
5. Test thoroughly
6. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the logs in `data/logs/`
2. Verify configuration in `config/` files
3. Test individual components
4. Check environment variables in `.env`

---

**Happy News Summarizing! 📰🤖**
