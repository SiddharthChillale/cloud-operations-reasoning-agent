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
```

## Build, Lint, and Test Commands

### Running the Application

```bash
# Run the application (TUI mode - default)
uv run python main.py

# Run via module syntax
uv run python -m clients.tui.app
```

### Linting and Type Checking

This project uses **ruff** for linting.

```bash
# Run ruff linter (via uv)
uv run ruff check .

# Run ruff with auto-fix
uv run ruff check --fix .

# Format with ruff
uv run ruff format .
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

# Run tests with verbose output
pytest -v

# Run tests and stop on first failure
pytest -x
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

from src.agents import cora_agent
from src.models import openrouter_model
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
    self.agent = cora_agent()
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

#### Creating Agents
```python
from smolagents import CodeAgent
from src.models import openrouter_model
from src.tools import create_boto_client

def cora_agent() -> CodeAgent:
    return CodeAgent(
        tools=[create_boto_client],
        model=openrouter_model,
        additional_authorized_imports=["botocore.exceptions"],
    )
```

#### Textual TUI Components
- Use `ComposeResult` for layout composition
- Use `@on()` decorators for event handlers (REQUIRED for events to work)
- Use `call_later()` for UI updates from background threads
- Use `run_worker()` for async background tasks

Example:
```python
from textual.app import App, ComposeResult
from textual.widgets import Input, Button
from textual import on

class ChatScreen(Screen):
    @on(Input.Submitted, "#query-input")
    def handle_submit(self, event: Input.Submitted) -> None:
        self._process_query()

    def _process_query(self) -> None:
        self.run_worker(self._run_agent(), exclusive=True)
```

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
- Use `src.utils.logging.setup_logger()` for consistent logging
- Set appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Use `logger.exception()` for error logging with tracebacks

## Project Structure

```
.
├── main.py                  # Entry point - routes to clients
├── pyproject.toml           # Project configuration
├── .env                     # Environment variables (gitignored)
├── src/                    # Core application code
│   ├── agents/             # Agent implementations
│   │   ├── __init__.py
│   │   └── aws_agent.py
│   ├── tools/              # Tool definitions
│   │   ├── __init__.py
│   │   └── aws_tools.py
│   ├── models/             # Model configurations
│   │   ├── __init__.py
│   │   └── openrouter_model.py
│   └── utils/              # Utilities
│       ├── __init__.py
│       └── logging.py
├── clients/                # Client interfaces
│   ├── cli/               # CLI chat interface
│   │   ├── __init__.py
│   │   └── app.py
│   └── tui/               # Textual TUI interface
│       ├── __init__.py
│       └── app.py
└── tests/                 # Test files (when added)
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
- `pyfiglet` - ASCII art

## Additional Notes

- The project uses OpenRouter API for LLM calls (requires `OPENROUTER_KEY`)
- AWS profile "notisphere" is hardcoded for boto3 sessions
- The agent is configured with `additional_authorized_imports=["botocore.exceptions"]`
- Use `uv run` prefix for all commands to ensure dependencies are available

## Textual App Development Skill

When working with Textual TUI applications:

1. **Event Handling**: Always use `@on()` decorators for event handlers. Without the decorator, the handler will NOT be called.
   ```python
   # CORRECT
   @on(Button.Pressed, "#send-btn")
   def handle_press(self, event: Button.Pressed) -> None:
       ...

   # WRONG - will not work
   def handle_press(self, event: Button.Pressed) -> None:
       ...
   ```

2. **Background Tasks**: Use `run_worker()` for background tasks and `call_later()` to update UI from worker threads.
   ```python
   self.run_worker(self._async_task(), exclusive=True)

   def _async_task(self) -> None:
       # Do work
       self.call_later(self._update_ui)
   ```

3. **Thread Safety**: Textual UI updates must happen on the main thread. Use `call_later()` to schedule UI updates from background threads.

4. **Screen Management**: Use `self.push_screen()` to navigate to new screens and `self.pop_screen()` to go back.

5. **CSS Styling**: Define CSS in the `CSS` class attribute. Use Textual's color system (`$surface`, `$text`, etc.) for theme compatibility.
