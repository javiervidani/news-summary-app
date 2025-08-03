#!/bin/bash

# News Summary App Setup Script with UV
# This script sets up the news summary application using UV package manager

set -e  # Exit on any error

echo "🚀 Setting up News Summary App with UV..."

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "📦 UV not found. Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "✅ UV version: $(uv --version)"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "� Creating virtual environment with UV..."
    uv venv
    echo "✅ Virtual environment created in .venv/"
else
    echo "✅ Virtual environment already exists"
fi

# Install dependencies
echo "📚 Installing all dependencies..."
uv sync --extra all

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your actual credentials"
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/logs
mkdir -p data/vectors

# Make main script executable
chmod +x main.py

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials:"
echo "   - Telegram bot token and chat ID"
echo "   - OpenAI API key (if using OpenAI processor)"
echo "   - Email SMTP settings (if using email interface)"
echo ""
echo "2. Install and run Mistral (recommended for local processing):"
echo "   curl -fsSL https://ollama.ai/install.sh | sh"
echo "   ollama pull mistral"
echo "   ollama run mistral"
echo ""
echo "3. Test the application:"
echo "   uv run python main.py --dry-run"
echo ""
echo "4. Run a real summary:"
echo "   uv run python main.py --topics general"
echo ""
echo "📖 See README.md for detailed usage instructions"
