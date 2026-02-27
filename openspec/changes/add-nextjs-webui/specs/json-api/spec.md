## ADDED Requirements

### Requirement: JSON Response for Session List
The system SHALL return JSON response when `Accept: application/json` header is present on GET /sessions endpoint.

#### Scenario: JSON request returns JSON format
- **WHEN** client sends GET /sessions with header `Accept: application/json`
- **THEN** response contains JSON array of sessions with fields: id, title, status, created_at, updated_at

#### Scenario: HTMX request returns HTML format
- **WHEN** client sends GET /sessions with header `HX-Request: true`
- **THEN** response contains HTML fragment with session list

### Requirement: JSON Response for Session Creation
The system SHALL return JSON response when `Accept: application/json` header is present on POST /sessions endpoint.

#### Scenario: JSON request returns session ID
- **WHEN** client sends POST /sessions with header `Accept: application/json` and body `{"title": "My Session"}`
- **THEN** response contains JSON `{"session_id": "<uuid>", "redirect_url": "/sessions/<uuid>"}`

#### Scenario: Form request returns redirect
- **WHEN** client sends POST /sessions with form data `title=My Session`
- **THEN** response redirects (303) to /sessions/<uuid>

### Requirement: JSON Response for Chat Page
The system SHALL return JSON response when `Accept: application/json` header is present on GET /sessions/{id} endpoint.

#### Scenario: JSON request returns session data
- **WHEN** client sends GET /sessions/{id} with header `Accept: application/json`
- **THEN** response contains JSON with session object, messages array, and tokens object

#### Scenario: HTMX request returns HTML
- **WHEN** client sends GET /sessions/{id} with header `HX-Request: true`
- **THEN** response contains HTML fragment with chat interface

### Requirement: JSON Response for Session Update
The system SHALL return JSON response when `Accept: application/json` header is present on PATCH /sessions/{id} endpoint.

#### Scenario: JSON request returns success
- **WHEN** client sends PATCH /sessions/{id} with header `Accept: application/json` and body `{"title": "New Title"}`
- **THEN** response contains JSON `{"success": true}`

### Requirement: JSON Response for Session Deletion
The system SHALL return JSON response when `Accept: application/json` header is present on DELETE /sessions/{id} endpoint.

#### Scenario: JSON request returns success with redirect
- **WHEN** client sends DELETE /sessions/{id} with header `Accept: application/json`
- **THEN** response contains JSON `{"success": true, "redirect_url": "/"}`

### Requirement: JSON Response for Token Usage
The system SHALL return JSON response when `Accept: application/json` header is present on GET /sessions/{id}/tokens endpoint.

#### Scenario: JSON request returns token data
- **WHEN** client sends GET /sessions/{id}/tokens with header `Accept: application/json`
- **THEN** response contains JSON with tokens object containing input_tokens, output_tokens, total_tokens

### Requirement: CORS Configuration
The system SHALL allow cross-origin requests from localhost:3000 (Next.js development server).

#### Scenario: Preflight request succeeds
- **WHEN** client sends OPTIONS /sessions from origin http://localhost:3000
- **THEN** response includes CORS headers allowing localhost:3000
