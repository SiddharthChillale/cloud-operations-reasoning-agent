## 1. Project Setup

- [x] 1.1 Add FastAPI and dependencies to pyproject.toml (fastapi, jinja2, python-multipart, sse-starlette)
- [x] 1.2 Create clients/web-ui/ directory structure
- [x] 1.3 Create __init__.py and main app.py for web client
- [x] 1.4 Add uv run command for web server to pyproject.toml

## 2. Database Schema Updates

- [x] 2.1 Add status field to Session model (idle, running, completed)
- [x] 2.2 Update database migration to include status field
- [x] 2.3 Update SessionManager to handle status updates

## 3. FastAPI Application Setup

- [x] 3.1 Configure Jinja2 templates
- [x] 3.2 Add HX-Request header detection helper
- [x] 3.3 Create base template with DaisyUI and HTMX v4 CDN
- [x] 3.4 Create navbar component
- [x] 3.5 Create sidebar component

## 4. Landing Page Routes

- [x] 4.1 Implement GET / - returns full page with welcome screen
- [x] 4.2 Implement GET /sessions - returns sidebar fragment
- [x] 4.3 Implement GET /sessions/{uuid} - returns chat page or fragment

## 5. Session Management Routes

- [x] 5.1 Implement POST /sessions - create new session with default "New Chat" title
- [x] 5.2 Implement PATCH /sessions/{uuid} - update session title
- [x] 5.3 Implement DELETE /sessions/{uuid} - delete session and messages

## 6. Streaming Route

- [x] 6.1 Implement POST /sessions/{uuid}/stream with SSE streaming
- [x] 6.2 Connect to SessionAgentFactory for agent execution
- [x] 6.3 Stream each step as SSE event (message, step, error, final, done)
- [x] 6.4 Save user message to database before streaming
- [x] 6.5 Save agent state to database after each step
- [x] 6.6 Update session status (idle -> running -> completed)

## 7. Token Usage Route

- [x] 7.1 Implement GET /sessions/{uuid}/tokens - returns token usage HTML fragment

## 8. Templates

- [x] 8.1 Create base.html with HTML structure, DaisyUI, HTMX v4
- [x] 8.2 Create navbar.html component
- [x] 8.3 Create sidebar.html component with session list
- [x] 8.4 Create welcome.html for empty state
- [x] 8.5 Create chat.html for message history display
- [x] 8.6 Create message.html for individual message rendering
- [x] 8.7 Create token_usage.html fragment

## 9. Refresh Handling

- [x] 9.1 Add status check on GET /sessions/{uuid}
- [x] 9.2 Display "connection lost" message when status is running
- [ ] 9.3 Test page refresh during active streaming

## 10. Testing & Polish

- [ ] 10.1 Test full page loads vs HTMX requests
- [ ] 10.2 Test session creation and navigation
- [ ] 10.3 Test streaming with actual agent
- [ ] 10.4 Test refresh during streaming
- [x] 10.5 Run ruff linter and fix any issues
