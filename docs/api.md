# Web UI API Documentation

This document describes the API endpoints for the smolagent chat interface. The UI is Server-Side Rendered (SSR) using HTMX with Server-Sent Events (SSE) for real-time streaming.

## Base URL

```
http://localhost:8000
```

## Page Structure

The application is a single-page app (SPA) with the following layout:

```
┌─────────────────────────────────────────────────────────────────┐
│  NAVBAR (fixed top)                                             │
│  [App Name] ─────────────────────────────── [New +]             │
├────────────────┬────────────────────────────────────────────────┤
│                │                                                 │
│   SIDEBAR      │              MAIN CONTENT                      │
│   (250px)      │                                                 │
│                │   ┌─────────────────────────────────────────┐   │
│  Sessions      │   │                                         │   │
│  - Session A   │   │   Welcome Screen (no session)         │   │
│  - Session B   │   │   OR                                    │   │
│  - Session C   │   │   Chat Screen (session selected)      │   │
│                │   │                                         │   │
│  [+ New Chat]  │   │   - Message History                   │   │
│                │   │   - Input Form                         │   │
│                │   └─────────────────────────────────────────┘   │
└────────────────┴────────────────────────────────────────────────┘
```

## HTMX Request Detection

All endpoints detect HTMX requests using the `HX-Request` header:

- **Full page load**: No `HX-Request` header → Return full HTML page
- **HTMX request**: `HX-Request: true` header → Return HTML fragment

```python
# Example (pseudo-code)
if request.headers.get("HX-Request"):
    return render_template("partial.html")  # Fragment only
else:
    return render_template("full_page.html")  # Full page with navbar
```
http://localhost:8000
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser                                 │
│                                                                  │
│  ┌─────────────┐    ┌─────────────────────────────────────────┐ │
│  │  Sidebar    │    │              Chat Area                  │ │
│  │             │    │                                          │ │
│  │ Sessions    │    │  ┌─────────────────────────────────────┐ │ │
│  │ - Session A │    │  │ Message History                    │ │ │
│  │ - Session B │    │  │ (rendered by server)               │ │ │
│  │ - Session C │    │  └─────────────────────────────────────┘ │ │
│  │             │    │                                          │ │
│  │ [New Chat]  │    │  ┌─────────────────────────────────────┐ │ │
│  └─────────────┘    │  │ Input Box                           │ │ │
│       │             │  │ hx-post="/sessions/{id}"            │ │ │
│       │             │  │ hx-trigger="submit"                 │ │ │
│       │             │  └─────────────────────────────────────┘ │ │
│       │             │                    │                     │ │
│       │             │                    │ SSE Stream          │ │
│       │             │                    ▼                     │ │
│       └─────────────┴──────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Session IDs

All session identifiers are **UUIDs** (not integers):

```
Example: 550e8400-e29b-41d4-a716-446655440000
```

---

## Endpoints

### 0. Landing Page

The root endpoint returns the full application page. If no session is selected, shows welcome screen. If a session is selected, shows that session's chat.

**Endpoint:** `GET /`

**Returns:** Full HTML page with:
- Navbar (app name + "New +" button)
- Sidebar (session list with current session highlighted)
- Main content area (welcome screen OR chat screen)

**Behavior:**
- If `HX-Request` header is present, returns fragment only (for HTMX swaps)
- Otherwise returns full page
- URL in browser history updated via HTMX

**Navbar Behavior:**
- App name links to `GET /` - shows welcome screen
- "New +" button creates new session and navigates to it

**Sidebar:**
- Lists all sessions sorted by `updated_at` descending
- Current session is highlighted
- Clicking a session navigates to `/sessions/{uuid}`

---

### 1. Sidebar - List All Sessions

Retrieve all sessions for the sidebar, sorted by most recent.

**Endpoint:** `GET /sessions`

**Returns:** HTML (HTMX template)

**Behavior:**
- Returns HTML fragment for the sidebar
- Sessions ordered by `updated_at` descending (newest first)
- Includes session title and truncated preview

**HTMX Usage:**
```html
<div hx-get="/sessions" hx-trigger="load" hx-swap="innerHTML">
    Loading sessions...
</div>
```

---

### 2. Create New Session

Create a new session and redirect to its chat page. This endpoint is triggered by the "New +" button in the navbar.

**Endpoint:** `POST /sessions`

**Request Body (form or JSON):**
```json
{
  "title": "My AWS Debug Session"
}
```

**Default Behavior:**
- If no `title` is provided, defaults to `"New Chat"`
- Session status starts as `"idle"`

**Returns:** Redirect (303) to `/sessions/{session_id}`

**HTMX Usage:**
```html
<form hx-post="/sessions" hx-swap="none">
    <button type="submit">New Chat</button>
</form>
```

---

### 3. Chat Page (SSR)

Render the chat page for a specific session, showing message history.

**Endpoint:** `GET /sessions/{session_id}`

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string (UUID) | The session ID |

**Returns:** HTML page with:
- Message history (user queries + agent responses)
- Input form for new messages
- Token usage (HTMX embedded)

**Behavior:**
- Loads **messages only** from database (not agent memory)
- Does NOT restore agent memory - that's done during streaming
- Updates `updated_at` timestamp

**Example URL:**
```
/sessions/550e8400-e29b-41d4-a716-446655440000
```

---

### 4. Stream Chat Response (SSE)

Send a message to the agent and stream the response via SSE using POST.

> **Note:** HTMX v4 uses the fetch() API (instead of XMLHttpRequest), which supports streaming responses via ReadableStream. This means any HTMX request (GET, POST, etc.) that returns `Content-Type: text/event-stream` will automatically stream the SSE response. This works with POST, allowing longer queries to be sent in the request body.

**Endpoint:** `POST /sessions/{session_id}/stream`

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string (UUID) | The session ID |

**Request Body (form or JSON):**
```json
{
  "query": "List my S3 buckets"
}
```

**Returns:** `text/event-stream` (SSE)

**Behavior:**
1. Restores agent memory for this session (if exists)
2. Saves user message to database
3. Streams agent response steps via SSE
4. After each step, saves agent state (non-blocking)
5. After completion, saves final agent memory

**HTMX v4 Usage:**
```html
<!-- HTMX v4 intercepts any response with text/event-stream and streams it -->
<form hx-post="/sessions/550e8400-e29b-41d4-a716-446655440000/stream" 
      hx-swap="beforeend" 
      hx-target="#messages">
    <input type="text" name="query" placeholder="Ask something..." required>
    <button type="submit">Send</button>
</form>
```

---

### 5. Update Session Title

Update the title of a session.

**Endpoint:** `PATCH /sessions/{session_id}`

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string (UUID) | The session ID |

**Request Body:**
```json
{
  "title": "New Title"
}
```

**Returns:** HTML fragment or redirect

**HTMX Usage:**
```html
<input type="text" 
       name="title" 
       value="Current Title"
       hx-patch="/sessions/550e8400-e29b-41d4-a716-446655440000"
       hx-trigger="change">
```

---

### 6. Delete Session

Delete a session and its messages.

**Endpoint:** `DELETE /sessions/{session_id}`

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string (UUID) | The session ID |

**Returns:** Redirect (303) to `/sessions`

**HTMX Usage:**
```html
<button hx-delete="/sessions/550e8400-e29b-41d4-a716-446655440000"
        onclick="return confirm('Delete this session?')">
    Delete
</button>
```

---

### 7. Token Usage (HTMX Embedded)

Display token usage for a session, embedded in the chat page.

**Endpoint:** `GET /sessions/{session_id}/tokens`

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string (UUID) | The session ID |

**Returns:** HTML fragment

**HTMX Usage:**
```html
<div hx-get="/sessions/550e8400-e29b-41d4-a716-446655440000/tokens"
     hx-trigger="load, sessionTokensChanged from:body">
    Loading tokens...
</div>
```

**Response HTML Example:**
```html
<div class="token-usage">
    <span>Input: 1,250 tokens</span>
    <span>Output: 450 tokens</span>
    <span>Total: 1,700 tokens</span>
    <span>Runs: 3</span>
</div>
```

---

## SSE Event Reference

### Event Types

| Event | Description |
|-------|-------------|
| `message` | User message to add to UI |
| `step` | Agent step (thinking, acting) |
| `error` | Error occurred |
| `final` | Agent completed with final answer |
| `done` | Stream completed |

### Event Payloads

#### User Message (event: message)

```json
{
  "type": "message",
  "role": "user",
  "content": "List my S3 buckets",
  "timestamp": "2025-02-25T10:30:00"
}
```

#### Planning Step (event: step)

```json
{
  "type": "step",
  "step_type": "planning",
  "step_number": 1,
  "plan": "I need to:\n1. Create boto3 S3 client\n2. List buckets\n3. Return results"
}
```

#### Action Step (event: step)

```json
{
  "type": "step",
  "step_type": "action",
  "step_number": 2,
  "model_output": "I'll list the S3 buckets in your account.",
  "code_action": "import boto3\ns3 = boto3.client('s3')\nresponse = s3.list_buckets()\nprint([b['Name'] for b in response['Buckets']])",
  "observations": "Found 3 buckets:\n- my-bucket\n- data-archive\n- logs-bucket",
  "token_usage": {
    "input_tokens": 150,
    "output_tokens": 50,
    "total_tokens": 200
  }
}
```

#### Error Step (event: error)

```json
{
  "type": "step",
  "step_type": "error",
  "step_number": 3,
  "error": "AccessDeniedException: User is not authorized to perform s3:GetObject"
}
```

#### Final Answer (event: final)

```json
{
  "type": "final",
  "step_number": 4,
  "output": "I found 3 S3 buckets in your account:\n1. my-bucket\n2. data-archive\n3. logs-bucket"
}
```

#### Done (event: done)

```json
{
  "type": "done"
}
```

---

## Messages vs Agent Memory

### Messages (`messages` table)

- **What:** User queries and agent final answers
- **Purpose:** Chat history for display in UI
- **Example:** `"User: List S3 buckets"`, `"Agent: Found 3 buckets"`

### Agent Memory (`sessions.agent_steps` - pickled)

- **What:** Full ReAct step data: thoughts, code, observations, errors, token usage
- **Purpose:** Agent's working memory to continue conversation context
- **Example:** Each step contains `model_output`, `code_action`, `observations`, `token_usage`

### Why Separate?

1. **Messages** = Display to user (UI)
2. **Agent Memory** = Internal state for agent to function (not shown to user directly)

When loading `/sessions/{id}`: Shows Messages only
When streaming in session: Restores Agent Memory for context

---

## Data Models

### Session

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Unique identifier |
| `title` | string | Session title (default: "New Chat") |
| `status` | string | "idle", "running", "completed" |
| `created_at` | ISO datetime | Creation timestamp |
| `updated_at` | ISO datetime | Last activity timestamp |

### Message

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique identifier |
| `session_id` | string (UUID) | Parent session |
| `role` | string | "user" or "agent" |
| `content` | string | Message text |
| `timestamp` | ISO datetime | When message was sent |

### Token Usage

| Field | Type | Description |
|-------|------|-------------|
| `input_tokens` | integer | Tokens sent to model |
| `output_tokens` | integer | Tokens received from model |
| `total_tokens` | integer | Sum of input + output |

---

## HTMX Integration Patterns

### Sidebar Auto-Refresh

```html
<!-- Refresh sidebar after session changes -->
<div hx-get="/sessions" 
     hx-trigger="sessionCreated, sessionDeleted from:body"
     hx-swap="innerHTML">
</div>
```

### Token Refresh After Stream

```javascript
// Dispatch event after SSE completes
const eventSource = new EventSource(`/sessions/${sessionId}?query=${query}`);
eventSource.addEventListener('done', () => {
    document.body.dispatchEvent(new CustomEvent('sessionTokensChanged'));
    eventSource.close();
});
```

### Optimistic UI Updates

```html
<form hx-post="/sessions/{id}" hx-swap="beforeend">
    <input type="text" name="query" required>
    <!-- Show loading state -->
    <button type="submit" hx-indicator=".loading">
        Send
    </button>
    <span class="loading" style="display:none">Thinking...</span>
</form>
```

---

## Refresh Handling During SSE

When a user refreshes the page while an agent is running (SSE streaming in progress):

### Server Behavior

1. **Agent continues running** on the server (SSE connection terminated on client side)
2. Each step continues to be saved to the database (non-blocking)
3. Session status remains "running" until agent completes

### Page Reload Behavior

When user reloads the page:

1. Server loads session from database
2. Checks session `status`:
   - **"completed"** → Show full chat history (normal)
   - **"running"** → Show partial chat history + warning message

### Warning Message for Running Sessions

```html
<div class="warning-message">
    <span>Connection lost. Agent is running, check again later.</span>
</div>
```

This message is displayed when:
- Session status is "running"
- There are partial results in the database
- User can refresh the page to check again

### Status Updates

| Status | When Set | Description |
|--------|----------|-------------|
| `idle` | Session created, no active query | Waiting for user input |
| `running` | User submits query, streaming starts | Agent is processing |
| `completed` | SSE sends "done" event | Agent finished |

---

## Error Handling

### HTTP Status Codes

| Status | Description |
|--------|-------------|
| `200` | Success |
| `303` | Redirect |
| `400` | Invalid request (missing query) |
| `404` | Session not found |
| `500` | Server error |

### Error Responses

```html
<!-- HTML error page -->
<html>
<body>
    <div class="error">Session not found</div>
</body>
</html>
```

---

## Recommended Flow

### 1. Initial Load
```
GET /sessions
```
→ Render sidebar with all sessions

### 2. Create New Session
```
POST /sessions
```
→ Redirect to `/sessions/{new_uuid}`

### 3. View Existing Session
```
GET /sessions/{uuid}
```
→ Render chat page with message history

### 4. Send Message (HTMX v4 with POST)
```
POST /sessions/{uuid}/stream
Body: {"query": "..."}
```
→ Save user message to database
→ SSE stream with steps (via HTMX v4 fetch() API)
→ Each step saved to agent memory

### 5. Delete Session
```
DELETE /sessions/{uuid}
```
→ Delete session, messages, tokens
→ Redirect to `/sessions`
