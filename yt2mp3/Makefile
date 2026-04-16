# yt2mp3 - Makefile for development and testing
# Cross-platform: Works on Linux, macOS, and Windows (with make)

.PHONY: help setup test lint format typecheck clean all

# Default target
all: setup test

# Show help
help:
	@echo "yt2mp3 - YouTube to MP3 Converter"
	@echo ""
	@echo "Available targets:"
	@echo "  setup     - Install dependencies (runs setup.sh or setup.bat)"
	@echo "  test      - Run unit tests with pytest"
	@echo "  lint      - Run flake8 linter"
	@echo "  format    - Format code with black"
	@echo "  typecheck - Run mypy type checker"
	@echo "  clean     - Remove cache and build artifacts"
	@echo "  all       - Run setup and tests"
	@echo ""
	@echo "Quick start:"
	@echo "  make setup     # Install dependencies"
	@echo "  make test      # Run tests"
	@echo "  make all       # Setup + test"

# Setup dependencies
setup:
	@echo "Running setup script..."
	@if [ -f setup.sh ]; then \
		chmod +x setup.sh && ./setup.sh; \
	elif [ -f setup.bat ]; then \
		./setup.bat; \
	else \
		echo "Error: No setup script found"; \
		exit 1; \
	fi

# Run tests
test:
	@echo "Running unit tests..."
	@pytest tests/ -v

# Run tests with coverage
coverage:
	@echo "Running tests with coverage..."
	@pytest tests/ --cov=yt2mp3 --cov-report=term-missing --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

# Lint code
lint:
	@echo "Running flake8 linter..."
	@flake8 yt_to_mp3.py tests/ --max-line-length=100 --show-source --statistics

# Format code
format:
	@echo "Formatting code with black..."
	@black yt_to_mp3.py tests/ --line-length=100

# Type checking
typecheck:
	@echo "Running mypy type checker..."
	@mypy yt_to_mp3.py --ignore-missing-imports

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf yt2mp3/.cache/
	@rm -rf __pycache__/
	@rm -rf .pytest_cache/
	@rm -rf htmlcov/
	@rm -rf .mypy_cache/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean complete!"

# Install dev dependencies
dev-deps:
	@echo "Installing development dependencies..."
	@pip install -r requirements.txt

# Quick test conversion (for manual testing)
# Usage: make convert URL="https://youtube.com/watch?v=..."
convert:
	@python yt2mp3/yt_to_mp3.py "$(URL)"

# Quick test with trim
# Usage: make trim URL="https://..." START="1m0s" END="2m0s"
trim:
	@python yt2mp3/yt_to_mp3.py "$(URL)" "$(START)" "$(END)"
