## 1. Reactivity Implementation

- [x] 1.1 Add reactive import to ChatApp (`from textual.reactive import reactive`)
- [x] 1.2 Convert `_agent_running` to reactive attribute in ChatApp
- [x] 1.3 Convert `_current_session_id` to reactive attribute in ChatApp  
- [x] 1.4 Add `watch__agent_running` method to ChatApp for spinner control
- [x] 1.5 Add reactive import to ChatScreen (`from textual.reactive import reactive`)
- [x] 1.6 Convert `show_welcome` to reactive attribute in ChatScreen
- [x] 1.7 Convert `_query_count` to reactive attribute in ChatScreen
- [x] 1.8 Add `watch_show_welcome` method for welcome header fade-out
- [x] 1.9 Add `watch__query_count` method to trigger scroll on new queries

## 2. Scroll UX Improvements

- [x] 2.1 Add user scroll position tracking variable
- [x] 2.2 Detect user-initiated scroll (scroll_up event)
- [x] 2.3 Modify scroll to bottom logic to respect user scroll position
- [x] 2.4 Add smooth scroll using `animate()` method or keep simple scroll with reduced frequency
- [x] 2.5 Update final answer section to use opacity animation

## 3. Animation Implementation

- [x] 3.1 Add CSS transition to welcome header in styles.tcss
- [x] 3.2 Update `_hide_welcome` to use opacity instead of display:none
- [x] 3.3 Add fade-in animation class for query sections in styles.tcss
- [x] 3.4 Apply animation class when mounting new query sections
- [x] 3.5 Add loading indicator animation via CSS if needed

## 4. Code Cleanup (After Testing)

- [x] 4.1 Remove redundant `call_later()` calls replaced by reactives
- [x] 4.2 Remove redundant manual `update()` calls in watch methods
- [x] 4.3 Run ruff linter to verify code quality
- [ ] 4.4 Verify all functionality still works correctly