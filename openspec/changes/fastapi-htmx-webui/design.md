## Context

The smolagents trial project currently has a Textual TUI client (`clients/tui/`) for local interaction. The goal is to add a web-based interface using FastAPI with HTMX v4 and DaisyUI for:
- Remote agent interaction (running on servers/Docker)
- Lightweight SSR without separate frontend framework
- Real-time streaming via Server-Sent Events (SSE)

The API specification is already documented in `docs/api.md` with endpoints for sessions, streaming, and token usage.

## Goals / Non-Goals

**Goals:**
- Create FastAPI server with SSR pages using Jinja2 templates
- Implement HTMX v4 for progressive enhancement (full page loads + HTMX partial updates)
- Use DaisyUI for consistent, responsive UI components
- Support SSE streaming for real-time agent responses
- Handle page refresh gracefully during active streaming
- Maintain session state with sidebar navigation

**Non-Goals:**
- Mobile-responsive design (desktop-first)
- Authentication/authorization
- WebSocket fallback (SSE is uni-directional)
- Persistent SSE across page refreshes

## Decisions

### 1. FastAPI + HTMX v4 + DaisyUI Stack

**Decision:** Use FastAPI for the web server, HTMX v4 for progressive enhancement, and DaisyUI for UI components.

**Rationale:**
- FastAPI provides native async support, easy SSE via `StreamingResponse`, and Jinja2 template support
- HTMX v4 uses fetch() API which enables POST requests with streaming (unlike v2's EventSource which is GET-only)
- DaisyUI provides pre-built components (modals, alerts, cards) on top of Tailwind CSS

**Alternatives Considered:**
- Next.js: Overkill for this use case, requires separate frontend build
- HTMX v2 + GET only: Would limit query length to ~2KB
- Pure vanilla JS: More code to maintain

### 2. Session State via Database (Not Server Memory)

**Decision:** Each step of agent execution is saved to the database, not just server memory.

**Rationale:**
- Enables page refresh to show partial results
- Agent can resume from database state on server restart
- Separates display data (messages) from agent working memory (agent_steps)

**Alternatives Considered:**
- In-memory state: Lost on server restart or refresh
- Redis: Adds external dependency

### 3. HX-Request Header Detection

**Decision:** All endpoints detect HTMX requests via `HX-Request` header.

**Rationale:**
- Full page loads (direct URL access) return full HTML with navbar
- HTMX requests return partial HTML fragments for swapping
- Single template can serve both full page and fragments

### 4. Default Session Title "New Chat"

**Decision:** New sessions start with title "New Chat", user can rename via PATCH endpoint.

**Rationale:**
- Simple default that can be immediately understood
- Easy to implement - no AI title generation
- User can rename anytime

## Risks / Trade-offs

- [Risk] SSE connection limits (6 per domain in HTTP/1.1)
  - [Mitigation] Use HTTP/2 if possible; modern browsers support more connections

- [Risk] Long-running agents may timeout
  - [Mitigation] Use appropriate timeout settings; agent saves state incrementally

- [Risk] HTMX v4 is in beta/alpha
  - [Mitigation] Monitor for breaking changes; v2 is stable fallback if needed

- [Risk] DaisyUI via CDN may not work in air-gapped environments
  - [Mitigation] Can be bundled locally for production

## Migration Plan

1. Add FastAPI and dependencies to `pyproject.toml`
2. Create `clients/web-ui/` directory with FastAPI app
3. Implement routes matching `docs/api.md`
4. Create Jinja2 templates with DaisyUI styling
5. Update session database to include status field
6. Test SSE streaming and page refresh handling

## Open Questions

- Should we support dark/light theme toggle?
- How to handle very long agent outputs (pagination)?
- Should we add any caching for performance?
