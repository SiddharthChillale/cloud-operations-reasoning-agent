## Why

The current web UI uses HTMX with Server-Side Rendering (SSR) for the smolagent chat interface. While functional, it lacks the modern developer experience and interactivity that Next.js provides. Adding a Next.js frontend will enable better client-side state management, improved streaming UX, and a more maintainable codebase for future enhancements.

## What Changes

1. **FastAPI JSON API Support**: Modify existing endpoints to return JSON when `Accept: application/json` header is present, while keeping HTML for HTMX requests.
2. **New SSE GET Endpoint**: Add a separate GET endpoint (`/sessions/{id}/stream?query=...`) that returns JSON SSE for Next.js compatibility.
3. **CORS Configuration**: Add CORS middleware to allow Next.js (localhost:3000) to call FastAPI (localhost:8000).
4. **Next.js Frontend**: Create a new Next.js application at `clients/web_ui/nextjs/` with chat interface, session management, and streaming support.

## Capabilities

### New Capabilities
- `json-api`: Add JSON response support to existing endpoints based on Accept header detection
- `sse-get-endpoint`: Add GET endpoint for SSE streaming that returns JSON format
- `nextjs-frontend`: Create Next.js frontend application with chat UI and session management

### Modified Capabilities
- (None - this is a net-new frontend, existing HTMX backend remains unchanged)

## Impact

- **Code Changes**:
  - `clients/web_ui/app.py` - Add CORS, JSON response support, new SSE endpoint
  - New directory `clients/web_ui/nextjs/` - Next.js application
- **Dependencies**: New npm packages for Next.js (ai, @tanstack/react-query, tailwindcss, etc.)
- **Systems**: FastAPI runs on port 8000, Next.js runs on port 3000 (local development)
