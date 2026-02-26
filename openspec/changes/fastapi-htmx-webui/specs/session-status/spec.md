## ADDED Requirements

### Requirement: Session status tracks agent state
The system SHALL track session status as "idle", "running", or "completed".

#### Scenario: New session starts idle
- **WHEN** a new session is created
- **THEN** session status is set to "idle"

#### Scenario: Session status changes to running
- **WHEN** user submits a query to start agent processing
- **THEN** session status is set to "running"

#### Scenario: Session status changes to completed
- **WHEN** agent finishes processing and sends "done" event
- **THEN** session status is set to "completed"

### Requirement: Page refresh shows appropriate message
The system SHALL display a warning message when user refreshes during active streaming.

#### Scenario: Refresh while agent running
- **WHEN** user refreshes page
- **AND** session status is "running"
- **THEN** server shows partial chat history from database
- **AND** server displays "connection lost. agent is running, check again later" message

#### Scenario: Refresh after agent completed
- **WHEN** user refreshes page
- **AND** session status is "completed"
- **THEN** server shows full chat history (normal behavior)

### Requirement: Session status persists in database
The system SHALL store session status in the database for persistence across restarts.

#### Scenario: Server restart preserves status
- **WHEN** server restarts
- **AND** there were running sessions
- **THEN** sessions retain their "running" or "completed" status
- **AND** new page loads show appropriate partial/complete history
