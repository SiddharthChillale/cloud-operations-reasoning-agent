## ADDED Requirements

### Requirement: Landing page displays full application layout
The system SHALL return a complete HTML page with navbar, sidebar, and main content area when `GET /` is requested without HX-Request header.

#### Scenario: Full page load
- **WHEN** user visits `GET /` without HTMX request
- **THEN** server returns full HTML page with navbar, sidebar, and welcome screen

#### Scenario: Full page load with session
- **WHEN** user visits `GET /sessions/{uuid}` without HTMX request
- **THEN** server returns full HTML page with navbar, sidebar, and chat screen for the session

### Requirement: HTMX requests return partial HTML
The system SHALL return only the relevant HTML fragment when `HX-Request` header is present.

#### Scenario: HTMX sidebar request
- **WHEN** `GET /sessions` is requested with `HX-Request: true` header
- **THEN** server returns HTML fragment containing only the session list

#### Scenario: HTMX chat page request
- **WHEN** `GET /sessions/{uuid}` is requested with `HX-Request: true` header
- **THEN** server returns HTML fragment containing only the main content area

### Requirement: User can create new session
The system SHALL create a new session with default title "New Chat" and navigate to its chat page.

#### Scenario: Create new session via form
- **WHEN** user submits form to `POST /sessions` with optional title
- **THEN** server creates session with title "New Chat" (or provided title)
- **AND** server returns redirect (303) to `/sessions/{uuid}`

#### Scenario: Create session via HTMX
- **WHEN** HTMX form submits to `POST /sessions`
- **THEN** server creates session with default title "New Chat"
- **AND** HTMX swaps the page to the new session URL

### Requirement: User can view session chat history
The system SHALL display all messages for a session when `GET /sessions/{uuid}` is requested.

#### Scenario: View existing session
- **WHEN** user visits `GET /sessions/{uuid}`
- **THEN** server loads all messages from database
- **AND** server renders chat history in main content area

#### Scenario: View session with running status
- **WHEN** user refreshes page during active streaming
- **AND** session status is "running"
- **THEN** server shows partial chat history
- **AND** server displays "connection lost. agent is running, check again later" message

### Requirement: User can send message with streaming response
The system SHALL accept a POST request with user query and stream agent response via SSE.

#### Scenario: Send message via HTMX form
- **WHEN** user submits form to `POST /sessions/{uuid}/stream` with query
- **THEN** server starts agent with restored memory (if exists)
- **AND** server saves user message to database
- **AND** server streams response steps via SSE with Content-Type: text/event-stream

#### Scenario: SSE streaming completes
- **WHEN** agent finishes processing
- **THEN** server sends "done" event
- **AND** server updates session status to "completed"

### Requirement: User can rename session
The system SHALL update the session title when `PATCH /sessions/{uuid}` is requested.

#### Scenario: Rename session via HTMX
- **WHEN** HTMX form submits to `PATCH /sessions/{uuid}` with new title
- **THEN** server updates session title in database
- **AND** server returns success response

### Requirement: User can delete session
The system SHALL delete a session and all its messages when `DELETE /sessions/{uuid}` is requested.

#### Scenario: Delete session
- **WHEN** user confirms deletion via `DELETE /sessions/{uuid}`
- **THEN** server deletes session from database
- **AND** server returns redirect to `/sessions`

### Requirement: Token usage displays in chat page
The system SHALL display token usage for a session.

#### Scenario: View token usage
- **WHEN** user views chat page
- **THEN** server includes token usage HTML fragment
- **AND** fragment shows input tokens, output tokens, total, and run count
