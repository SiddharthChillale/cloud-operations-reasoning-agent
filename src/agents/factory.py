import logging
from typing import Callable, Optional

from smolagents import CodeAgent

from src.agents.aws_agent import cora_agent
from src.session.manager import SessionManager

logger = logging.getLogger(__name__)


class SessionAgentFactory:
    """Factory for creating and managing CodeAgent instances per session."""

    def __init__(self, session_manager: SessionManager) -> None:
        self._session_manager = session_manager

    def create_fresh_agent(self, step_callback: Optional[Callable] = None) -> CodeAgent:
        """Create a new CodeAgent with empty memory and optional step callback."""
        agent = cora_agent()
        if step_callback:
            from smolagents.memory import ActionStep, PlanningStep, FinalAnswerStep

            agent.step_callbacks.register(PlanningStep, step_callback)
            agent.step_callbacks.register(ActionStep, step_callback)
            agent.step_callbacks.register(FinalAnswerStep, step_callback)
        return agent

    async def get_agent(
        self, session_id: str, step_callback: Optional[Callable] = None
    ) -> CodeAgent:
        """Get an agent for a session, restoring its memory state if available."""
        agent = self.create_fresh_agent(step_callback)
        steps = await self._session_manager.load_agent_state(session_id)
        if steps and hasattr(agent, "memory") and agent.memory:
            agent.memory.steps = steps
            logger.info(f"Restored {len(steps)} steps for session {session_id}")
        return agent

    def save_agent(self, agent: CodeAgent, session_id: str, run_number: int) -> None:
        """Save an agent's memory state for a session (non-blocking)."""
        self._session_manager.save_agent_state(agent, session_id, run_number)
