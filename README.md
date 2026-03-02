# CORA - Cloud Operations Reasoning Agent

CORA stands for Cloud Operations Reasoning Agent. Cora helps developers and architects query their AWS architecture for resources and reason about the resource configurations.

## Features

- Interactive CLI and TUI chat interfaces
- AI-powered agent that understands AWS infrastructure
- Query AWS resources using natural language
- Uses smolagents framework with CodeAgent
- Textual-based terminal UI with rich formatting

## Installation

```bash
# Install dependencies
uv sync
```

## Usage

```bash
# Run CLI mode (default)
uv run python main.py

# Run TUI mode
uv run python main.py --tui
```

## Project Structure

```
.
├── main.py                  # Entry point - routes to clients
├── pyproject.toml           # Project configuration
├── README.md               # This file
├── src/                    # Core application code
│   ├── agents/             # Agent implementations
│   ├── tools/              # Tool definitions
│   ├── models/             # Model configurations
│   └── utils/              # Utilities
├── clients/                # Client interfaces
│   ├── cli/               # CLI chat interface
│   └── tui/               # Textual TUI interface
└── .env                   # Environment variables (create from template)
```

## Environment Variables

Create a `.env` file with the following:

```
OPENROUTER_KEY=your_openrouter_key
LANGFUSE_SECRET_KEY=your_langfuse_secret
LANGFUSE_PUBLIC_KEY=your_langfuse_public
LANGFUSE_BASE_URL=your_langfuse_base_url
```

## Dependencies

- `smolagents` - AI agent framework
- `textual` - TUI framework
- `boto3` - AWS SDK
- `rich` - Rich console output
- `langfuse` - Observability
- `pyfiglet` - ASCII art

## Modal Deployment

Deploy CORA FastAPI to Modal cloud platform.

### Prerequisites

```bash
# Install and authenticate Modal CLI
pip install modal-client
modal token set
```

### Setup Secrets

Create Modal secrets from your `.env` file:

```bash
uv run python modal_setup.py
```

### Deploy

```bash
# Deploy to Modal
modal deploy modal_app.py

# For local testing with Modal
modal serve modal_app.py
```

### Verify Deployment

```bash
# Check health endpoint
curl https://cora-fastapi--fastapi-app.modal.run/health

# View logs
modal logs cora-fastapi
```

### Required Secrets

| Secret Key | Required | Description |
|------------|----------|-------------|
| `OPENROUTER_KEY` | Yes | OpenRouter API key |
| `LANGFUSE_SECRET_KEY` | No | Langfuse secret for observability |
| `LANGFUSE_PUBLIC_KEY` | No | Langfuse public key |
| `LANGFUSE_BASE_URL` | No | Langfuse base URL |

## License

MIT
