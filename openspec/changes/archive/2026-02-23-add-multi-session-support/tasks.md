## 1. Session Database Layer

- [x] 1.1 Create `src/session/` module with `__init__.py`
- [x] 1.2 Create `src/session/models.py` with `Session` and `Message` dataclasses
- [x] 1.3 Create `src/session/database.py` with SQLite schema using aiosqlite
- [x] 1.4 Create `src/session/manager.py` with `SessionManager` class (create, list, get, save methods)

## 2. Session Manager Integration

- [x] 2.1 Initialize `SessionManager` in `ChatApp.on_mount()`
- [x] 2.2 Load most recent session on startup or create new session if none exist
- [x] 2.3 Add exit hook to save all sessions before app exits

## 3. Chat Screen Session Support

- [x] 3.1 Update `ChatScreen` to hold current `session_id` instead of starting fresh
- [x] 3.2 Load session chat history into `ChatHistoryPanel` when switching sessions
- [x] 3.3 Update message sending to store messages in current session via `SessionManager`
- [x] 3.4 Set session title to first query text when first message is sent

## 4. Session Picker UI

- [x] 4.1 Create `clients/tui/session_picker.py` with `SessionPickerModal` screen
- [x] 4.2 Implement keyboard navigation (Up/Down arrows) with visual selection
- [x] 4.3 Handle Enter key to open selected session (prevent query submission)
- [x] 4.4 Implement Escape key to close picker without selection
- [x] 4.5 Sort sessions by most recent activity (newest first)

## 5. Slash Command Implementation

- [x] 5.1 Update _process_query() to detect / prefix and parse commands
- [x] 5.2 Implement /new - create new session
- [x] 5.3 Implement /sessions - open session picker
- [x] 5.4 Implement /theme - open theme picker
- [x] 5.5 Implement /quit - quit application
- [x] 5.6 Implement /help - show available commands
- [x] 5.7 Send unrecognized / commands to agent as queries
- [x] 5.8 Clear input after command execution

## 6. UI Updates

- [x] 6.1 Update status bar to show slash commands
- [x] 6.2 Remove Ctrl+N, Ctrl+P, Ctrl+T bindings from ChatApp

## 7. Testing

- [ ] 7.1 Test each slash command works
- [ ] 7.2 Test unrecognized commands go to agent
- [ ] 7.3 Verify status bar shows correct commands
