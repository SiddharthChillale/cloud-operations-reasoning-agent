## ADDED Requirements

### Requirement: GET Endpoint for SSE Streaming
The system SHALL provide a GET endpoint at `/sessions/{id}/stream` that accepts a query parameter and returns SSE with JSON format.

#### Scenario: GET request streams agent response
- **WHEN** client sends GET /sessions/{id}/stream?query=List+S3+buckets
- **THEN** response is Content-Type: text/event-stream with JSON events

#### Scenario: Missing query parameter returns error
- **WHEN** client sends GET /sessions/{id}/stream without query parameter
- **THEN** response is JSON error: `{"error": "Query parameter is required"}`

#### Scenario: Invalid session returns error
- **WHEN** client sends GET /sessions/invalid-id/stream?query=test
- **THEN** response is JSON error: `{"error": "Session not found"}`

### Requirement: JSON SSE Event Format
All SSE events SHALL be formatted as JSON objects (NDJSON/JSON Lines format).

#### Scenario: Message event format
- **WHEN** agent receives user message
- **THEN** SSE sends: `{"type": "message", "role": "user", "content": "<query>", "timestamp": "<iso-date>"}`

#### Scenario: Planning step event format
- **WHEN** agent starts planning step
- **THEN** SSE sends: `{"type": "step", "step_type": "planning", "step_number": 1, "plan": "<plan-text>"}`

#### Scenario: Action step event format
- **WHEN** agent executes action step
- **THEN** SSE sends: `{"type": "step", "step_type": "action", "step_number": 2, "model_output": "...", "code_action": "...", "observations": "...", "error": null}`

#### Scenario: Final answer event format
- **WHEN** agent completes with final answer
- **THEN** SSE sends: `{"type": "final", "step_number": 3, "output": "<final-output>"}`

#### Scenario: Done event format
- **WHEN** agent stream completes
- **THEN** SSE sends: `{"type": "done"}`

#### Scenario: Error event format
- **WHEN** agent encounters error
- **THEN** SSE sends: `{"type": "error", "error": "<error-message>"}`

### Requirement: Token Usage in SSE Events
The system SHALL include token usage information in step events when available.

#### Scenario: Token usage included in action step
- **WHEN** action step has token usage data
- **THEN** SSE event includes: `{"token_usage": {"input_tokens": 150, "output_tokens": 50, "total_tokens": 200}}`
