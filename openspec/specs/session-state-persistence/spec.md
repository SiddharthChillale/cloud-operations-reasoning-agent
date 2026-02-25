# Session State Persistence

## Purpose

Provides mechanisms for persisting and restoring agent memory state across session switches and application restarts.

## ADDED Requirements

### Requirement: SessionManager saves agent state after each step
The SessionManager MUST provide a method to serialize and persist the agent's memory steps to the database after each agent step execution.

#### Scenario: Save agent state after action step
- **WHEN** an ActionStep completes (with thought, code, observation, or error)
- **THEN** the agent's memory steps are serialized using pickle and stored in the session's agent_steps field

#### Scenario: Save agent state after planning step
- **WHEN** a PlanningStep is generated (when planning is enabled)
- **THEN** the agent's memory steps including the planning step are serialized and stored

### Requirement: SessionManager saves agent state non-blocking
The SessionManager's save operation MUST NOT block the agent execution or UI streaming.

#### Scenario: Non-blocking save
- **WHEN** save_agent_state is called
- **THEN** the save operation MUST be performed asynchronously (fire-and-forget) to not impact response time

### Requirement: SessionManager loads agent state for session
The SessionManager MUST provide a method to retrieve and deserialize the agent's memory steps for a specific session ID.

#### Scenario: Load existing agent state
- **WHEN** loading a session with prior conversation
- **THEN** the stored agent_steps are retrieved and deserialized, returning a list of MemoryStep objects

#### Scenario: Load session with no agent state
- **WHEN** loading a session with no stored agent_steps
- **THEN** an empty list is returned

### Requirement: SessionManager maintains data integrity
The SessionManager MUST properly handle serialization errors and missing data.

#### Scenario: Handle corrupted agent_steps
- **WHEN** stored agent_steps cannot be deserialized (corrupted data)
- **THEN** the error is logged and an empty list is returned
