## ADDED Requirements

### Requirement: Session List Page
The Next.js application SHALL display a list of all sessions on the home page.

#### Scenario: Display all sessions
- **WHEN** user visits root URL (/) 
- **THEN** page displays list of sessions sorted by updated_at descending
- **AND** each session shows title, truncated preview, and timestamp
- **AND** "New Chat" button is visible

#### Scenario: Create new session
- **WHEN** user clicks "New Chat" button
- **THEN** POST request sent to /sessions with default title "New Chat"
- **AND** user is redirected to new session page

#### Scenario: Empty state
- **WHEN** no sessions exist
- **THEN** page displays "No sessions yet" message with CTA to create one

### Requirement: Chat Page
The Next.js application SHALL display the chat interface for a specific session.

#### Scenario: Display chat history
- **WHEN** user visits /sessions/{id}
- **THEN** page displays all messages in the session
- **AND** messages show role (user/agent) and content
- **AND** agent steps are expandable to show reasoning

#### Scenario: Session not found
- **WHEN** user visits /sessions/{invalid-id}
- **THEN** page redirects to home or shows error message

### Requirement: Send Message with Streaming
The Next.js application SHALL send user messages and stream agent responses in real-time.

#### Scenario: Send message and receive streaming response
- **WHEN** user types message and presses Enter
- **THEN** GET request sent to /sessions/{id}/stream?query=...
- **AND** response streams via SSE
- **AND** messages appear incrementally as they arrive
- **AND** loading indicator shown during streaming

#### Scenario: Message input disabled during streaming
- **WHEN** agent is processing a message
- **THEN** input field is disabled
- **AND** user cannot send another message until streaming completes

### Requirement: Token Usage Display
The Next.js application SHALL display token usage information for the session.

#### Scenario: Show token usage
- **WHEN** session has token data
- **THEN** page displays input tokens, output tokens, and total tokens
- **AND** token count updates after each agent run

### Requirement: Delete Session
The Next.js application SHALL allow users to delete a session.

#### Scenario: Delete session
- **WHEN** user clicks delete button on a session
- **THEN** DELETE request sent to /sessions/{id}
- **AND** user is redirected to home page

### Requirement: Update Session Title
The Next.js application SHALL allow users to rename a session.

#### Scenario: Rename session
- **WHEN** user edits session title
- **THEN** PATCH request sent to /sessions/{id} with new title
- **AND** UI updates to show new title

### Requirement: API Client
The Next.js application SHALL provide a client library for calling the FastAPI backend.

#### Scenario: Fetch sessions
- **WHEN** calling getSessions()
- **THEN** request sent to GET /sessions with Accept: application/json
- **AND** Promise resolves with session array

#### Scenario: Stream chat
- **WHEN** calling streamChat(sessionId, query)
- **THEN** SSE connection opened to GET /sessions/{id}/stream?query=...
- **AND** events yielded as they arrive
- **AND** connection closed on completion or error
