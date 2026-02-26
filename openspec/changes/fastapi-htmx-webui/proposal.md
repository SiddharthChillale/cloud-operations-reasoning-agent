## Why

The smolagents trial project currently has a CLI-based TUI client but lacks a web-based interface. Users need a web UI to interact with the agent remotely, especially when running on remote servers or Docker containers. The FastAPI + HTMX v4 + DaisyUI stack provides a lightweight, SSR-based solution that supports real-time streaming without the complexity of a separate frontend framework.

## What Changes

- Create a new FastAPI-based web server
- Implement SSR with HTMX v4 for dynamic page updates
- Use DaisyUI for pre-built UI components (modals, alerts, cards)
- Support SSE streaming for real-time agent responses
- Implement session management with sidebar navigation
- Handle page refresh during active streaming gracefully

## Capabilities

### New Capabilities

- `web-server`: FastAPI server with HTMX v4 and DaisyUI frontend
  - Landing page with navbar and session sidebar
  - Chat interface with real-time SSE streaming
  - Session management (create, rename, delete)
  - Token usage display
  - Refresh handling during active streaming

- `session-status`: Track and display session running state
  - Show "connection lost" message when refreshing during streaming
  - Display partial results saved to database
  - Status states: idle, running, completed

### Modified Capabilities

- None at this time. is a net-new capability.

## Impact

- New `clients/web-ui/` directory for FastAPI application
- Dependencies: `fastapi`, `jinja2`, `python-multipart`, `sse-starlette`
- New routes added to handle SSR pages and SSE streaming
- Database schema updated to include session status tracking
