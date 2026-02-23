## Why

The current TUI application only supports a single chat session. Users need the ability to have multiple concurrent chat sessions without losing context when switching between them. This is essential for power users who work on multiple tasks simultaneously and need quick access to different conversation histories.

## What Changes

- Add SQLite database backend for persistent session storage
- Implement session management (create, list, switch, delete)
- Create a session picker UI with keyboard navigation (arrow keys + Enter)
- Add session title based on first query
- Save sessions automatically on application exit
- Add status bar commands for creating new sessions and opening session picker
- Ensure agent execution continues in background when switching sessions

## Capabilities

### New Capabilities
- `multi-session`: Enable multiple concurrent chat sessions with persistent storage, session switching via keyboard-driven picker, and automatic session saving.

### Modified Capabilities
- None (this is a net-new feature)

## Impact

- New dependency: `sqlite3` (Python stdlib) or `aiosqlite` for async SQLite
- Affected files: TUI app components, session management module
- No breaking changes to existing functionality
