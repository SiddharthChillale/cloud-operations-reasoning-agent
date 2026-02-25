## ADDED Requirements

### Requirement: SSE endpoint streams planning steps
The SSE endpoint MUST stream PlanningStep events to the client when the agent generates a plan.

#### Scenario: Stream planning step
- **WHEN** the agent generates a PlanningStep during execution
- **THEN** the step is sent to the client via SSE with event type "planning" containing the plan text

### Requirement: SSE endpoint streams action steps
The SSE endpoint MUST stream ActionStep events to the client, including thought, code, and observations.

#### Scenario: Stream action step with code execution
- **WHEN** the agent generates an ActionStep with code execution
- **THEN** the step is sent to the client via SSE with event type "action" containing model_output (thought), code_action, and observations

#### Scenario: Stream action step with error
- **WHEN** the agent generates an ActionStep with an error
- **THEN** the error is sent to the client via SSE with event type "error" containing the error message

### Requirement: SSE endpoint streams final answer
The SSE endpoint MUST stream the final answer when the agent completes its task.

#### Scenario: Stream final answer
- **WHEN** the agent completes with is_final_answer=True
- **THEN** the final answer is sent to the client via SSE with event type "final" containing the answer

### Requirement: SSE endpoint saves state after each step
The SSE endpoint MUST trigger a non-blocking save of agent state after each step is streamed.

#### Scenario: Save after step
- **WHEN** any step is streamed to the client
- **THEN** the agent state is saved to the database asynchronously without blocking the stream

### Requirement: SSE endpoint manages session lifecycle
The SSE endpoint MUST handle session loading and state restoration properly.

#### Scenario: Load session before streaming
- **WHEN** a request is made to the SSE endpoint with a session_id
- **THEN** the agent is created with memory restored from that session before streaming begins
