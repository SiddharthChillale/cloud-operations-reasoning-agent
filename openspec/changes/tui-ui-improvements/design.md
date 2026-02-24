## Context

The CORA TUI application in `clients/tui/` provides an interactive chat interface with an AI agent. Currently, the UI state management uses plain Python instance variables with manual updates via `call_later()` and `widget.update()`. This approach requires explicit UI updates for every state change, leading to:
- Potential performance issues from unnecessary refreshes
- Scattered update logic throughout the codebase
- Abrupt UI transitions (instant scroll, no animations)

The affected files are:
- `clients/tui/app.py` - Main ChatApp class
- `clients/tui/screens/chat_screen.py` - ChatScreen with query handling
- `clients/tui/components/chat_history.py` - ChatHistoryPanel widget

## Goals / Non-Goals

**Goals:**
- Implement Textual reactive attributes for ChatApp and ChatScreen state management
- Replace manual `call_later()` + `update()` patterns with reactive `watch_` methods
- Add smooth scroll animations instead of instant `scroll_end()` calls
- Add fade animations for welcome header and content loading
- Improve overall UI responsiveness and perceived performance

**Non-Goals:**
- No changes to the agent communication layer or API
- No changes to session storage or data persistence
- No new features or capabilities - purely UI/UX improvements
- No changes to slash commands or user interaction patterns

## Decisions

### Decision 1: Use Textual's built-in reactivity over manual updates
**Rationale:** Textual's reactive attributes provide automatic UI refresh with smart batching, reducing boilerplate and improving performance. The `watch_` method pattern is idiomatic to Textual.

**Alternative considered:** Continue using `call_later()` with manual `update()` calls. Rejected because it requires explicit updates for every state change and doesn't benefit from Textual's optimization.

### Decision 2: Animate scroll using CSS transitions and scrollbar visibility
**Rationale:** Textual doesn't have a built-in smooth scroll animation API, but we can use CSS transitions on scrollbar visibility to create a smoother feel. For content scroll, we can use `animate()` method on styles.

**Alternative considered:** Using JavaScript-style requestAnimationFrame - not applicable in Textual's async model.

### Decision 3: Use CSS opacity transitions for welcome header
**Rationale:** Textual supports CSS transitions. We can use `transition: opacity 300ms` in the TCSS to animate the welcome header fade-out.

**Alternative considered:** Using Python `animate()` method on the styles object - works but CSS is cleaner for simple fade effects.

### Decision 4: Reactive attribute placement - App vs Screen level
**Rationale:** Application-wide state (`_agent_running`, `_current_session_id`) stays in ChatApp. Screen-specific state (`show_welcome`, `_query_count`, tab IDs) goes in ChatScreen. This follows Textual's component architecture.

**Alternative considered:** Moving all state to App - rejected because ChatScreen should manage its own UI state.

## Risks / Trade-offs

[Performance] → Mitigation: Textual's reactive system already batches updates. Avoid setting `layout=True` on reactives unless layout actually needs to change.

[Regressions] → Mitigation: The existing functionality is preserved. We're adding reactives alongside existing code and gradually replacing manual updates. Test each watch method individually.

[Scroll UX] → Mitigation: User scroll position should be preserved when reading history. Add flag to track if user has scrolled up manually.

## Open Questions

1. Should we use `@work` decorator on watch methods that do async operations? Currently watch methods are sync but may call async code via `call_later()`. Need to verify this doesn't cause issues.

2. What's the appropriate animation duration? Need to test with actual terminal to verify 300ms feels natural vs too slow.