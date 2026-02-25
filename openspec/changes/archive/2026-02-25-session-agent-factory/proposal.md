## Why

Currently, the smolagent system lacks support for multiple chat sessions. When users switch between sessions, the agent's memory (containing previous queries, thoughts, code executions, observations, and errors) is not properly managed. This prevents users from having persistent conversations across different sessions.

## What Changes

- Create a new `SessionAgentFactory` class that manages agent lifecycle per session
- Extend `SessionManager` with methods to save/load agent state (serialized memory steps)
- Store agent memory as serialized bytes in the existing `sessions.agent_steps` BLOB column
- Implement non-blocking state persistence after each step
- Support SSE streaming for real-time step updates to UI

## Capabilities

### New Capabilities

- `session-agent-factory`: Session-aware agent factory that creates agents with restored memory for specific sessions
- `session-state-persistence`: Non-blocking persistence of agent memory steps after each step execution
- `session-sse-streaming`: Server-Sent Events endpoint for streaming agent steps (thought, code, observations) in real-time

### Modified Capabilities

- None. The existing session/database layer already supports storing agent_steps as BLOB.

## Impact

- **New Files**: `src/agents/factory.py` - SessionAgentFactory class
- **Modified Files**: `src/session/manager.py` - Add save/load agent state methods
- **Database**: No schema changes required - existing `sessions.agent_steps` BLOB column is sufficient
- **Web API**: New FastAPI endpoints for SSE streaming (to be defined in separate spec)
