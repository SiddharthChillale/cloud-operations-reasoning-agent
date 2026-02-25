## Context

The current smolagent system in this project uses smolagents' CodeAgent for AWS-related tasks. The existing `src/session/` layer provides:
- SQLite-based session storage (`SessionDatabase`)
- Session management (`SessionManager`) for creating/switching sessions
- Message storage for conversation history
- Agent run metrics tracking

However, the agent memory (steps with thoughts, code, observations, errors) is not properly managed across sessions. When switching sessions, the agent carries over memory from the previous session.

The existing TUI client has bugs around session switching and agent memory restoration. A new web-ui is planned that will use FastAPI with SSE for streaming.

## Goals / Non-Goals

**Goals:**
- Enable multiple isolated chat sessions, each with its own agent memory
- Support session switching with proper memory restoration
- Stream agent steps (thoughts, code, observations) to UI in real-time via SSE
- Persist agent state after each step (non-blocking)

**Non-Goals:**
- Concurrent agent execution (one agent at a time)
- Cross-session memory sharing
- Real-time WebSocket communication (using SSE instead)
- Multi-agent orchestration

## Decisions

### 1. Serialization: pickle over JSON

**Decision:** Use Python's `pickle` module for serializing agent memory steps.

**Rationale:**
- No official smolagents serialization exists (GitHub issue #1216 is open)
- `agent.memory.steps` contains complex objects (ActionStep, PlanningStep, TaskStep) that are not trivially reconstructible from dicts
- The existing TUI already uses pickle successfully
- Local desktop app (not exposed to untrusted input) - security risk is acceptable

**Alternatives Considered:**
- JSON via `get_full_steps()`: Would require custom reconstruction logic for ActionStep/PlanningStep objects
- cloudpickle: Handles more edge cases but same security concerns

### 2. State Persistence: Non-blocking after each step

**Decision:** Save agent state after each step using fire-and-forget async task.

**Rationale:**
- User requirement: "agent state must be stored after every step in async manner"
- Prevents data loss if app crashes mid-run
- SSE streaming continues without waiting for I/O

**Alternatives Considered:**
- Save only at end: Simpler but risks losing progress on crash

### 3. Streaming: SSE over WebSockets

**Decision:** Use Server-Sent Events (SSE) for streaming agent steps to UI.

**Rationale:**
- User preference: "I prefer SSE, no need for WebSockets"
- Simpler implementation than WebSockets
- Unidirectional (server → client) fits our use case

### 4. Database: No Schema Changes

**Decision:** Use existing `sessions.agent_steps` BLOB column.

**Rationale:**
- Already stores pickled agent memory
- Stores everything needed: queries, thoughts, code, observations, errors, final answers
- No migration needed

## Risks / Trade-offs

- **[Risk]** pickle security: Using pickle could be a security concern if untrusted data is deserialized.
  - **Mitigation:** This is a local desktop app. User is the only input source. Acceptable risk.

- **[Risk]** Version compatibility: Pickled objects may break across smolagents version upgrades.
  - **Mitigation:** Document dependency on smolagents version. Test migration path when upgrading.

- **[Risk]** Large memory: Storing full step history may grow large.
  - **Mitigation:** Could implement truncation later. For now, store everything.

## Migration Plan

1. **Deploy new code:**
   - Add `save_agent_state()`, `load_agent_state()` to `SessionManager`
   - Create new `SessionAgentFactory` class

2. **Verify:**
   - Test session creation, switching, memory restoration
   - Verify SSE streaming works

3. **Rollback:** Revert code changes if issues occur. No database migration to revert.

## Open Questions

- Should we implement memory truncation for very long sessions?
- What smolagents version should we document as supported?
