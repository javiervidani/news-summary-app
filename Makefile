# Makefile for News Summary App with UV

.PHONY: install install-all install-dev test lint format clean run run-dry setup help venv venv-activate venv-deactivate

# Default target
help:
	@echo "Available commands:"
	@echo "  setup        - Run initial setup (install UV, dependencies, create .env)"
	@echo "  venv         - Create virtual environment with UV"
	@echo "  venv-activate- Show command to activate virtual environment"
	@echo "  install      - Install core dependencies"
	@echo "  install-all  - Install all dependencies (including optional)"
	@echo "  install-dev  - Install development dependencies"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting and type checking"
	@echo "  format       - Format code with black"
	@echo "  run          - Run the news summary app"
	@echo "  run-dry      - Run in dry-run mode (no actual delivery)"
	@echo "  clean        - Clean cache and temporary files"

# Setup everything
setup: venv install-all
	@echo "🚀 Setting up News Summary App..."
	@./setup.sh

# Virtual environment management
venv:
	@echo "🐍 Creating virtual environment with UV..."
	uv venv
	@echo "✅ Virtual environment created in .venv/"
	@echo "💡 To activate: source .venv/bin/activate"
	@echo "💡 Or use 'make venv-activate' for the command"

venv-activate:
	@echo "To activate the virtual environment, run:"
	@echo "source .venv/bin/activate"

venv-check:
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Creating one..."; \
		make venv; \
	else \
		echo "✅ Virtual environment exists in .venv/"; \
	fi

# Install dependencies
install: venv-check
	@echo "📦 Installing core dependencies..."
	uv sync

install-all: venv-check
	@echo "📦 Installing all dependencies..."
	uv sync --extra all

install-dev: venv-check
	@echo "📦 Installing development dependencies..."
	uv sync --extra dev

# Development tasks
test:
	uv run pytest

lint:
	uv run flake8 .
	uv run mypy .

format:
	uv run black .

# Running the app
run:
	uv run python main.py

run-dry:
	uv run python main.py --dry-run

run-business:
	uv run python main.py --topics business

run-tech:
	uv run python main.py --topics technology

run-all-topics:
	uv run python main.py --topics general business technology world

# Cleanup
clean:
	@echo "🧹 Cleaning cache and temporary files..."
	uv cache clean
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

clean-all: clean
	@echo "🧹 Removing virtual environment..."
	rm -rf .venv
	@echo "✅ All cleaned up!"

# Development workflow
dev-setup: install-dev
	@echo "🔧 Setting up development environment..."
	uv run pre-commit install

dev-test: format lint test
	@echo "✅ All development checks passed!"

# Quick commands for different news categories
morning-briefing:
	uv run python main.py --topics general business

lunch-update:
	uv run python main.py --topics technology world

evening-summary:
	uv run python main.py --topics general

# Deployment helpers
check-config:
	uv run python main.py --dry-run

install-ollama:
	@echo "📥 Installing Ollama for local Mistral support..."
	curl -fsSL https://ollama.ai/install.sh | sh
	ollama pull mistral
	@echo "✅ Ollama and Mistral installed. Run 'ollama run mistral' to start."

# Environment management
create-env: venv
	@echo "✅ Virtual environment created (alias for venv)"

activate: venv-activate
	@echo "Use the command above to activate the environment"

# Project info
info:
	@echo "Project: News Summary App"
	@echo "UV version: $$(uv --version)"
	@if [ -d ".venv" ]; then \
		echo "Virtual env: ✅ Active (.venv/)"; \
		echo "Python version: $$(uv run python --version)"; \
		echo "Dependencies: $$(uv pip list 2>/dev/null | wc -l) packages"; \
	else \
		echo "Virtual env: ❌ Not created"; \
		echo "Run 'make venv' to create one"; \
	fi
