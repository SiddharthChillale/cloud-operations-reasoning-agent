## ADDED Requirements

### Requirement: ChatApp shall use reactive attributes for application state
The ChatApp class SHALL use Textual reactive attributes for managing application state instead of plain Python instance variables. This enables automatic UI updates when state changes.

#### Scenario: Agent running state changes
- **WHEN** `self._agent_running` reactive attribute changes from `False` to `True`
- **THEN** the loading spinner SHALL automatically display via a watch method

#### Scenario: Session ID changes
- **WHEN** `self._current_session_id` reactive attribute changes
- **THEN** the UI SHALL refresh to reflect the current session without manual updates

### Requirement: ChatScreen shall use reactive attributes for UI state
The ChatScreen class SHALL use Textual reactive attributes for managing chat interface state including query count, tab IDs, and visibility flags.

#### Scenario: Query count increment
- **WHEN** `self._query_count` reactive attribute increments
- **THEN** the UI SHALL automatically update any widgets observing this value

#### Scenario: Welcome header visibility
- **WHEN** `self.show_welcome` reactive attribute changes to `False`
- **THEN** the welcome header SHALL automatically hide with smooth fade transition

#### Scenario: Agent running state
- **WHEN** `self._agent_running` reactive attribute changes
- **THEN** the loading indicator SHALL show/hide automatically and input focus SHALL be managed

### Requirement: Reactive state shall trigger optimized refreshes
Textual's smart refresh SHALL batch multiple state changes into a single UI update to minimize performance overhead.

#### Scenario: Multiple rapid state changes
- **WHEN** multiple reactive attributes change in quick succession
- **THEN** Textual SHALL coalesce the updates into a single refresh cycle
