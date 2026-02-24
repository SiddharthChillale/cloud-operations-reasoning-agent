## ADDED Requirements

### Requirement: Welcome header shall fade out smoothly
When the user sends their first message, the welcome ASCII art header SHALL fade out smoothly instead of disappearing instantly.

#### Scenario: First query submitted
- **WHEN** `show_welcome` reactive changes from `True` to `False` after first query
- **THEN** the welcome header SHALL fade out over approximately 300ms using opacity animation

#### Scenario: Session restored with history
- **WHEN** a session is restored that has previous messages
- **THEN** the welcome header SHALL be hidden immediately without animation (already complete session)

### Requirement: Query section shall appear with fade-in effect
New query sections SHALL appear with a subtle fade-in animation to provide visual continuity.

#### Scenario: New user query added
- **WHEN** a new user query section is mounted to the chat history
- **THEN** it SHALL fade in with a brief animation over approximately 200ms

### Requirement: Loading indicator shall animate
The loading spinner SHALL display with proper animation to indicate activity.

#### Scenario: Agent starts processing
- **WHEN** `_agent_running` becomes `True`
- **THEN** the loading indicator SHALL become visible with any default Textual animation

#### Scenario: Agent completes processing
- **WHEN** `_agent_running` becomes `False`
- **THEN** the loading indicator SHALL hide with fade animation

### Requirement: Step tabs shall transition smoothly
When new planning or action steps appear, their tabs SHALL be added smoothly.

#### Scenario: New planning tab added
- **WHEN** a new planning tab is added to StepsTabbedContent
- **THEN** the tab SHALL appear without jarring layout shift

#### Scenario: New action step tab added
- **WHEN** a new action step tab is added during agent streaming
- **THEN** the tab SHALL be created and activated smoothly