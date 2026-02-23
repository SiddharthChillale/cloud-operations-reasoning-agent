## Context

The current TUI application (`clients/tui/app.py`) uses a single `ChatScreen` that manages one chat session. The agent runs in a background worker thread, and all chat history is stored in-memory in the `ChatHistoryPanel` widget. Sessions are not persisted between application restarts.

### Current Architecture
- `ChatApp`: Main Textual app, manages screen stack
- `ChatScreen`: Main chat interface, handles input and agent execution
- `ChatHistoryPanel`: Widget for displaying messages
- Agent runs in `ThreadPoolExecutor`, streams results back to UI
- No persistence layer - all state lost on exit

### Constraints
- Must maintain backward compatibility with existing single-session behavior
- Agent execution in background must not be interrupted when switching sessions
- Must work with existing agent framework (smolagents)
- SQLite database stored locally (no external service)

## Goals / Non-Goals

**Goals:**
- Add SQLite-backed session storage
- Implement keyboard-driven session picker (arrow keys + Enter)
- Create new sessions without interrupting active agent
- Auto-save sessions on application exit
- Display session commands in status bar

**Non-Goals:**
- Session deletion (future enhancement)
- Session export/import (future enhancement)
- Cloud sync or cross-device sharing
- Multiple simultaneous agent executions in different sessions

## Decisions

### 1. Database Schema: SQLite with aiosqlite

**Decision**: Use `aiosqlite` for async SQLite operations.

**Rationale**:
- Python's stdlib `sqlite3` is synchronous and would block the event loop
- `aiosqlite` provides async API compatible with Textual's async model
- Lightweight - no additional daemon required

**Alternatives considered**:
- `sqlalchemy` with SQLite: Overkill for simple session storage
- JSON file storage: Less reliable, no ACID guarantees, harder to query
- `tinyDB`: NoSQL document store, but adds another dependency

### 2. Session Data Model

**Decision**: Two-table schema - `sessions` and `messages`.

**Rationale**:
- `sessions` table: id, title, created_at, updated_at, is_active
- `messages` table: id, session_id, role (user/agent/system), content, timestamp
- Allows efficient querying of sessions and their message history
- Enables future features like message search within sessions

### 3. Session Picker UI: Modal Overlay

**Decision**: Implement as a Textual modal/screen overlay.

**Rationale**:
- Textual's `Screen` class with modal behavior is well-suited
- Keeps picker UI separate from main chat interface
- Easy to implement keyboard navigation with `KeyListener` or custom key handlers
- Theme-compatible out of the box

**Alternatives considered**:
- Inline dropdown: More complex to implement, less flexible
- Separate screen: Requires navigation, less fluid

### 4. Session State Management

**Decision**: Centralized `SessionManager` class that holds current session state in memory, with async database sync.

**Rationale**:
- Fast in-memory access for active session
- Periodic or event-driven persistence to SQLite
- Clean separation of concerns

**Data flow**:
```
User Input → ChatScreen → SessionManager → SQLite (async)
                ↓
         Active Session
         (in-memory chat history)
```

### 5. Background Agent Preservation

**Decision**: Keep agent executor and running state in `ChatApp`, not per-screen.

**Rationale**:
- When switching sessions, the worker continues running
- ChatScreen can be swapped without stopping the worker
- Store pending agent results keyed by session_id

### 6. Session Title Derivation

**Decision**: Use first 50 characters of first user message as title.

**Rationale**:
- Simple heuristic that works well in practice
- Truncation with "..." provides clear visual indicator
- No additional UI needed for title editing (future enhancement)

## Risks / Trade-offs

### Risk: Race condition when saving on exit
**Mitigation**: Use `app.exit()` hook to ensure all async saves complete before process terminates. Use `asyncio.wait_for` with timeout.

### Risk: Large chat history impacts performance
**Mitigation**: 
- Paginate message loading (load last N messages on session switch)
- Store complete history but lazy-load older messages
- Add database indexes on session_id and timestamp

### Risk: Agent state not fully serializable
**Mitigation**: Agent memory/state is not persisted - only messages. When returning to a session with a partially-complete agent run, show "Session paused" indicator and allow re-running or continuing (future enhancement).

### Risk: Textual key binding conflicts
**Mitigation**: 
- Use `KeyListener` in session picker for arrow keys
- Ensure Enter in picker doesn't propagate to input field
- Test with existing bindings (Ctrl+C, Ctrl+T)

## Migration Plan

1. **Phase 1**: Create `src/session/` module with `SessionManager`, database schema, and models
2. **Phase 2**: Integrate session manager into `ChatApp` - load/create session on startup
3. **Phase 3**: Add session picker modal UI with keyboard navigation
4. **Phase 4**: Wire up status bar commands (Ctrl+N new session, Ctrl+P picker)
5. **Phase 5**: Add exit hook to persist sessions

**Rollback**: Feature flag disabled = original single-session behavior. No database migration needed for rollback (tables can be ignored).

## Open Questions

1. **Should session picker show timestamps or just titles?** - Spec says title is first query, but timestamps help identify sessions. Include both in picker.

2. **What happens if user exits while agent is running?** - Option A: Block exit until agent completes. Option B: Save partial state, mark session as "incomplete". Recommend Option B for UX.

3. **Maximum number of sessions to keep?** - Not specified in requirements. Default to unlimited, add setting if storage becomes concern.
