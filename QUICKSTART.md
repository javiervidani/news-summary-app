# Quick Start with UV

This guide will get you up and running with the News Summary App using UV package manager in under 5 minutes.

## ⚡ Super Quick Setup

```bash
# 1. Run the setup script
./setup.sh

# 2. Edit configuration
nano .env

# 3. Test the app
uv run python main.py --dry-run

# 4. Run a real summary
uv run python main.py
```

## 🔧 UV Commands Cheat Sheet

### Installation & Setup
```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync

# Install with all optional features
uv sync --extra all

# Install specific features only
uv sync --extra database --extra openai
```

### Running the App
```bash
# Basic run
uv run python main.py

# With specific options
uv run python main.py --topics business technology --processor mistral

# Test mode (no actual delivery)
uv run python main.py --dry-run
```

### Development
```bash
# Add new dependency
uv add requests

# Add development dependency
uv add --dev pytest

# Update all dependencies
uv sync

# Run tests
uv run pytest

# Format code
uv run black .

# Type checking
uv run mypy .
```

### Virtual Environment
```bash
# Create environment
uv venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Run in environment without activation
uv run python main.py
```

## 🎯 Common Tasks

### First Time Setup
```bash
git clone <your-repo>
cd news-summary-app
./setup.sh
# Edit .env file
uv run python main.py --dry-run
```

### Daily Usage
```bash
# Morning news
uv run python main.py --topics general business

# Tech news at lunch
uv run python main.py --topics technology

# Evening summary
uv run python main.py --topics general world
```

### Adding New Features
```bash
# Install development tools
uv sync --extra dev

# Add new dependency for your feature
uv add your-new-package

# Test your changes
uv run pytest

# Format and check code
uv run black .
uv run mypy .
```

## 🚨 Troubleshooting

### UV Not Found
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal
```

### Dependencies Not Installing
```bash
# Clear cache and reinstall
uv cache clean
uv sync --reinstall
```

### Python Version Issues
```bash
# Check Python version
uv python list

# Use specific Python version
uv venv --python 3.11
```

### Import Errors
```bash
# Make sure environment is activated
source .venv/bin/activate

# Or use uv run
uv run python main.py
```

## 📚 More Information

- [UV Documentation](https://docs.astral.sh/uv/)
- [Project README](README.md)
- [Configuration Guide](README.md#configuration)
