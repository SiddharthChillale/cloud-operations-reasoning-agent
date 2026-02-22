# AGENTS.md - Developer Guide for This Project

This file provides guidelines for agentic coding agents operating in this repository.

## Project Overview

This is a Python project using smolagents, FastAPI, and Textual TUI. It provides an interactive chat interface with a CodeAgent that can create AWS boto3 clients.

## Package Manager

This project uses **uv** as the package manager.

```bash
# Install dependencies
uv sync

# Add a new dependency
uv add <package>

# Add a dev dependency
uv add --dev <package>

# Run the application
uv run python main.py
uv run python tui_agent.py
```

## Build, Lint, and Test Commands

### Running the Application

```bash
# Run the main CLI chat interface
python main.py

# Run the Textual TUI application
python tui_agent.py
```

### Linting and Type Checking

This project uses **ruff** for linting (evidenced by `.ruff_cache` directory).

```bash
# Run ruff linter
ruff check .

# Run ruff with auto-fix
ruff check --fix .

# Format with ruff
ruff format .
```

### Testing

No formal tests exist yet in this project. When adding tests:

```bash
# Run all tests with pytest
pytest

# Run a single test file
pytest tests/test_file.py

# Run a single test function
pytest tests/test_file.py::test_function_name

# Run tests matching a pattern
pytest -k "test_pattern"
```

## Code Style Guidelines

### General Principles

- Python 3.12+ (see `.python-version`)
- Use type hints for all function signatures
- Use `from __future__ import annotations` for forward references if needed

### Imports

- Standard library imports first
- Third-party imports second
- Local imports last
- Use explicit relative imports for local modules
- Group imports with blank lines between groups
- Sort imports alphabetically within groups

Example:
```python
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import boto3
from dotenv import load_dotenv
from rich.console import Console
from smolagents import CodeAgent, tool

from .local_module import LocalClass
```

### Formatting

- Line length: 88 characters (ruff default)
- Use 4 spaces for indentation (no tabs)
- Use trailing commas for multi-line collections
- Use parentheses for line continuations

### Naming Conventions

- `snake_case` for functions, variables, and methods
- `PascalCase` for classes and types
- `UPPER_SNAKE_CASE` for constants
- Prefix private methods with underscore: `_private_method`
- Use descriptive names - avoid single letters except in short loops

### Type Hints

- Always include return types
- Use `Optional[X]` instead of `X | None`
- Use `object` sparingly - prefer specific types
- Example:
```python
def create_boto_client(service_name: str) -> object:
    """Create a boto3 client with a specified AWS profile."""
    session = boto3.Session(profile_name="notisphere")
    return session.client(service_name)
```

### Error Handling

- Use try/except blocks for expected errors
- Catch specific exceptions rather than broad `Exception`
- Use `logger.exception()` for logging errors with tracebacks
- Provide meaningful error messages
- Example:
```python
try:
    self.agent = CodeAgent(tools=[...], model=...)
except Exception as e:
    logger.exception("Failed to initialize agent")
    chat_history.add_system_message(f"Error: {str(e)}")
```

### Docstrings

- Use Google-style or NumPy-style docstrings
- Include Args, Returns, and Raises sections for functions
- Keep brief one-line summaries for simple functions

### Code Patterns Used in This Project

#### Defining Tools with smolagents
```python
from smolagents import tool

@tool
def create_boto_client(service_name: str) -> object:
    """Create a boto3 client with a specified AWS profile."""
    session = boto3.Session(profile_name="notisphere")
    return session.client(service_name)
```

#### Textual TUI Components
- Use `ComposeResult` for layout composition
- Use `@on()` decorators for event handlers
- Use `call_later()` for UI updates from background threads

#### Rich Console Output
```python
from rich.console import Console
from rich.panel import Panel

console = Console()
console.print(Panel("[bold cyan]Title[/bold cyan]", expand=False))
```

### Environment Variables

- Use `os.getenv()` to read environment variables
- Use `dotenv` for local development: `load_dotenv()`
- Never commit secrets - use `.env` file (already gitignored)

### Logging

- Use Python's `logging` module
- Set appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Use `logger.exception()` for error logging with tracebacks

## Project Structure

```
.
├── main.py          # CLI chat interface
├── tui_agent.py     # Textual TUI application
├── pyproject.toml   # Project configuration
├── .env             # Environment variables (gitignored)
└── scripts/         # Utility scripts (empty)
```

## Dependencies

Key dependencies (from `pyproject.toml`):
- `smolagents` - AI agent framework
- `fastapi` - Web framework
- `textual` - TUI framework
- `typer` - CLI framework
- `boto3` - AWS SDK
- `rich` - Rich console output
- `langfuse` - Observability

## Additional Notes

- The project uses OpenRouter API for LLM calls (requires `OPENROUTER_KEY`)
- AWS profile "notisphere" is hardcoded for boto3 sessions
- The agent is configured with `additional_authorized_imports=["botocore.exceptions"]`
