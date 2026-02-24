## Why

The CORA TUI currently feels janky and slow during interactions. The chat interface uses manual widget updates via `call_later()` and `update()` instead of Textual's reactive system, causing unnecessary screen refreshes and poor performance. Additionally, instant scroll operations and lack of animations make the UI feel abrupt rather than polished.

## What Changes

- Convert plain Python instance variables to Textual reactive attributes for automatic UI updates
- Replace `call_later()` + manual `update()` patterns with reactive `watch_` methods
- Add smooth scroll animations instead of instant `scroll_end()` calls
- Implement CSS transitions and fade animations for welcome header and content loading
- Add visual polish with animated loading indicators and smooth content appearance

## Capabilities

### New Capabilities
- `tui-reactivity`: Implement Textual reactive attributes for state management in ChatApp and ChatScreen
- `tui-scroll-ux`: Add animated scrolling and improved scroll behavior in chat history
- `tui-animations`: Add fade animations for welcome header, content loading, and UI transitions

### Modified Capabilities
- None - this is a pure enhancement with no existing spec behavior changes

## Impact

- **Affected Code**: `clients/tui/app.py`, `clients/tui/screens/chat_screen.py`, `clients/tui/components/chat_history.py`, `clients/tui/widgets/step_tabs.py`
- **No API Changes**: External interfaces remain the same
- **No Dependencies**: Only uses existing Textual framework features
- **Performance**: Reduced unnecessary refresh cycles, smoother UI interactions
