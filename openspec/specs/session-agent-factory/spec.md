# SessionAgentFactory

## Purpose

Provides factory methods for creating and managing CodeAgent instances per session with proper memory isolation.

## ADDED Requirements

### Requirement: SessionAgentFactory creates fresh agents
The SessionAgentFactory MUST provide a method to create a fresh CodeAgent with empty memory for new sessions.

#### Scenario: Create fresh agent for new session
- **WHEN** a new session is created and no prior conversation exists
- **THEN** the factory returns a CodeAgent with empty memory (no steps)

### Requirement: SessionAgentFactory restores agent memory for existing session
The SessionAgentFactory MUST provide a method to create a CodeAgent and restore its memory from the database for a specific session ID.

#### Scenario: Restore agent with session history
- **WHEN** an existing session with prior conversation is loaded
- **THEN** the factory returns a CodeAgent with agent.memory.steps restored from the session's stored state

#### Scenario: Restore agent with no stored steps
- **WHEN** an existing session has no stored agent steps (first query)
- **THEN** the factory returns a CodeAgent with empty memory (no steps)

### Requirement: SessionAgentFactory saves agent state for session
The SessionAgentFactory MUST provide a method to serialize and persist the agent's memory to the database for a specific session ID.

#### Scenario: Save agent state after query
- **WHEN** a user query completes (with or without errors)
- **THEN** the agent's memory steps are serialized and stored in the session's agent_steps field

### Requirement: SessionAgentFactory integrates with SessionManager
The SessionAgentFactory MUST use the existing SessionManager for database operations.

#### Scenario: Use existing SessionManager
- **WHEN** the factory performs any operation
- **THEN** it MUST use the provided SessionManager instance for database access
