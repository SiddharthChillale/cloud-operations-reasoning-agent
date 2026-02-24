## ADDED Requirements

### Requirement: Chat history shall scroll with smooth animation
When new content is added to the chat history, the scroll SHALL animate smoothly to reveal the new content instead of jumping instantly.

#### Scenario: New query section added
- **WHEN** a new query section is mounted to the chat history
- **THEN** the view SHALL smoothly scroll to reveal the new content over approximately 300ms

#### Scenario: Agent step added
- **WHEN** an agent planning or action step is added during streaming
- **THEN** the chat SHALL automatically scroll to show the new step with smooth animation

### Requirement: Scroll position shall be preserved during content updates
The system SHALL maintain scroll position when content updates occur, unless new content requires revealing.

#### Scenario: Token count update
- **WHEN** token counts are updated in the status bar
- **THEN** the current scroll position of the chat history SHALL NOT change

#### Scenario: User scrolls up to read history
- **WHEN** the user manually scrolls up to read previous messages
- **THEN** new content appearing SHALL NOT automatically scroll down, allowing the user to read uninterrupted

### Requirement: Final answer shall appear with visual feedback
When the agent completes a response with a final answer, the content SHALL appear smoothly rather than instantly.

#### Scenario: Final answer rendered
- **WHEN** the agent's final answer markdown is mounted
- **THEN** it SHALL fade in with a brief animation to provide visual confirmation of completion