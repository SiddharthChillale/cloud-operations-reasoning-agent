## 1. Session State Persistence (SessionManager)

- [x] 1.1 Add `load_agent_state(session_id)` method to SessionManager
  - Retrieve agent_steps bytes from database
  - Deserialize using pickle
  - Return list of MemoryStep objects
  - Handle missing/corrupted data gracefully

- [x] 1.2 Add `save_agent_state(agent, session_id)` method to SessionManager
  - Serialize agent.memory.steps using pickle
  - Store in database using existing save_agent_steps method
  - Make it non-blocking (fire-and-forget asyncio task)

## 2. SessionAgentFactory Implementation

- [x] 2.1 Create `src/agents/factory.py` file
  - Import cora_agent from src.agents.aws_agent
  - Import SessionManager from src.session
  - Import pickle for serialization

- [x] 2.2 Implement `SessionAgentFactory.__init__(session_manager)`
  - Store SessionManager reference

- [x] 2.3 Implement `SessionAgentFactory.create_fresh_agent()`
  - Return new CodeAgent with empty memory

- [x] 2.4 Implement `SessionAgentFactory.get_agent(session_id)`
  - Create fresh agent using cora_agent()
  - Load agent state using SessionManager.load_agent_state()
  - Restore agent.memory.steps with loaded steps
  - Return configured agent

- [x] 2.5 Implement `SessionAgentFactory.save_agent(agent, session_id)`
  - Delegate to SessionManager.save_agent_state()

## 3. Integration & Testing

- [x] 3.1 Verify database schema compatibility
  - Confirm sessions.agent_steps BLOB column exists
  - No migration needed

- [x] 3.2 Add type hints to new methods
  - Use CodeAgent type from smolagents
  - Use list[MemoryStep] for step collections

- [x] 3.3 Run linting and type checking
  - Execute ruff check
  - Execute ruff format
  - Fix any issues

## 4. Documentation

- [x] 4.1 Document SessionAgentFactory usage
  - Explain how to create factory
  - Explain agent lifecycle methods
  - Show example code

- [x] 4.2 Update AGENTS.md if needed
  - Add factory to project structure
  - Document new session management approach
