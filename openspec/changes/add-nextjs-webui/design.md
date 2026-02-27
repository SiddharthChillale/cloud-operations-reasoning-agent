## Context

The current web UI at `clients/web_ui/app.py` uses HTMX for Server-Side Rendering with SSE streaming. The application is a FastAPI backend that provides:
- Session management (create, list, delete sessions)
- Chat functionality with agent streaming
- HTML templates rendered via Jinja2

The smolagent backend is Python-based, running at localhost:8000. The new Next.js frontend will run at localhost:3000 and call the FastAPI backend directly.

## Goals / Non-Goals

**Goals:**
- Add JSON API support to FastAPI endpoints via `Accept: application/json` header detection
- Create a new GET endpoint for SSE streaming that returns JSON format
- Add CORS middleware to allow Next.js (localhost:3000) to communicate with FastAPI (localhost:8000)
- Build a functional Next.js chat interface with session management
- Ensure existing HTMX/SSR functionality continues to work unchanged

**Non-Goals:**
- Authentication/authorization (local hackathon project)
- Deployment to production
- Replacing the HTMX backend - both frontends coexist
- Real-time collaboration features

## Decisions

### 1. JSON Response Detection via Accept Header

**Decision:** Use `Accept: application/json` header to determine response format.

**Rationale:**
- Industry standard pattern (REST API convention)
- Works seamlessly with fetch API and axios
- Alternative `HX-Request` would require HTMX-specific logic

**Alternative Considered:** Use query parameter `?format=json` - rejected because it's less RESTful and pollutes URLs.

### 2. Separate GET Endpoint for SSE

**Decision:** Add `GET /sessions/{id}/stream?query=...` in addition to existing POST endpoint.

**Rationale:**
- GET is more idiomatic for streaming (works with Vercel AI SDK, EventSource)
- Simpler client implementation - no form data handling needed
- Query parameter allows encoding the message in URL

**Alternative Considered:** Use same POST endpoint with JSON body - rejected because GET is cleaner for streaming.

### 3. CORS Configuration

**Decision:** Configure FastAPI CORS to allow localhost:3000.

**Rationale:**
- Simple local development setup
- No proxy configuration needed in Next.js
- Clear origin separation between frontend and backend

### 4. SSE Format: JSON Lines (NDJSON)

**Decision:** Each SSE event is a JSON object on its own line.

**Rationale:**
- Industry standard for SSE with modern frameworks
- Works with Vercel AI SDK out of the box
- Easy to parse on client side

**Format:**
```
data: {"type": "message", "role": "user", "content": "..."}
data: {"type": "step", "step_type": "action", ...}
data: {"type": "done"}
```

### 5. Direct API Calls from Next.js

**Decision:** Next.js client calls FastAPI directly (not via Next.js API routes).

**Rationale:**
- Simpler architecture for local development
- No need to proxy requests through Next.js
- Easier debugging - can test API directly with curl

### 6. Next.js Stack

**Decision:** 
- Next.js 14+ with App Router
- TailwindCSS for styling
- Vercel AI SDK for streaming
- TanStack Query for state management

**Rationale:**
- AI SDK simplifies SSE streaming implementation
- TailwindCSS is already familiar (used in existing project via textual)
- TanStack Query provides caching and state management

## Risks / Trade-offs

- **[Risk] CORS issues during development** → Mitigation: Test locally with both servers running, ensure CORS is properly configured
- **[Risk] SSE connection handling** → Mitigation: Use AI SDK which handles reconnection gracefully
- **[Risk] Port conflicts** → Mitigation: FastAPI on 8000, Next.js on 3000 (default)
- **[Risk] Session state not synced between frontends** → Mitigation: Both use same SQLite database, state persisted properly

## Migration Plan

1. Start FastAPI server on port 8000 (existing)
2. Start Next.js dev server on port 3000 (new)
3. Next.js calls FastAPI directly for all operations
4. No migration needed - both frontends coexist

## Open Questions

- Should the Next.js app be in a separate git repository? → **No, same repo per user request**
- Should we add a landing page to choose between HTMX and Next.js? → **Optional, can add later**
