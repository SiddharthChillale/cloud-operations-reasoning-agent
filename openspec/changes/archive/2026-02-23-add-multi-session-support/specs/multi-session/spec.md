## ADDED Requirements

### Requirement: User can create a new session while another session is active
The system SHALL allow users to create a new chat session without interrupting the currently executing agent or losing the current session's chat history.

#### Scenario: Create new session from status bar command
- **WHEN** user presses the key combination to create a new session (displayed in status bar)
- **THEN** a new session is created with an empty chat history
- **AND** the new session becomes the active session
- **AND** the previous session remains in memory with its complete chat history intact

#### Scenario: Agent execution continues after session switch
- **WHEN** an agent is executing in the current session and user creates/switches to a different session
- **THEN** the agent execution SHALL continue in the background
- **AND** the chat history of the original session is preserved
- **AND** results from the background agent are stored for the original session

### Requirement: User can open session picker to view all sessions
The system SHALL provide a session picker that displays all existing sessions sorted by most recent activity (newest first).

#### Scenario: Open session picker
- **WHEN** user presses the key combination to open session picker (displayed in status bar)
- **THEN** a modal/picker interface appears showing all sessions
- **AND** sessions are listed vertically with the most recently active session at the top
- **AND** each session displays its title (first query) and creation timestamp

#### Scenario: Navigate sessions with arrow keys
- **WHEN** the session picker is open and user presses Down Arrow
- **THEN** the selection moves to the next session in the list
- **AND** selection wraps from bottom to top (circular navigation)
- **AND** the previously selected session is visually deselected

- **WHEN** the session picker is open and user presses Up Arrow
- **THEN** the selection moves to the previous session in the list
- **AND** selection wraps from top to bottom (circular navigation)

### Requirement: User can switch to selected session by pressing Enter
The system SHALL allow users to open a selected session by pressing Enter key in the session picker.

#### Scenario: Open session with Enter key
- **WHEN** a session is selected in the picker and user presses Enter
- **THEN** the selected session becomes the active session
- **AND** the picker closes
- **AND** the full chat history of the selected session is displayed
- **AND** any background agent execution continues independently

#### Scenario: Enter key does not send query when picker is open
- **WHEN** the session picker is open
- **AND** user presses Enter (with or without text in input)
- **THEN** the query is NOT sent to the agent
- **AND** instead the selected session is opened

### Requirement: Session title is derived from first query
The system SHALL use the first user query as the session title.

#### Scenario: Session gets title from first query
- **WHEN** a user sends their first message in a new session
- **AND** the message text is non-empty
- **THEN** the session title is set to the first 50 characters of that query
- **AND** the title is truncated with "..." if longer than 50 characters

### Requirement: Sessions persist in SQLite database
The system SHALL store all session data in a SQLite database for persistence across application restarts.

#### Scenario: Sessions saved on exit
- **WHEN** the user exits the application
- **AND** there are active sessions with chat history
- **THEN** all sessions and their messages are saved to the SQLite database
- **AND** the application exits cleanly without data loss

#### Scenario: Sessions restored on startup
- **WHEN** the user starts the application
- **AND** there are saved sessions in the database
- **THEN** the most recently active session is loaded
- **AND** the full chat history is restored

### Requirement: Status bar displays session commands
The system SHALL display available session commands in the status bar below the query input.

#### Scenario: Status bar shows session commands
- **WHEN** the application is running
- **AND** the user has not focused the session picker
- **THEN** the status bar displays commands for:
  - Creating a new session
  - Opening the session picker
- **AND** the commands are shown as keyboard shortcuts (e.g., "Ctrl+N: New Session | Ctrl+P: Pick Session")
