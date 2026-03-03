import logging
from typing import Callable, Optional

from smolagents import CodeAgent

from src.agents.aws_agent import cora_agent
from src.agents.manager_agent.agent import manager_agent
from src.session.manager import SessionManager
from src.models import DEFAULT_MODEL_ID

logger = logging.getLogger(__name__)


class SessionAgentFactory:
    """Factory for creating and managing CodeAgent instances per session."""

    def __init__(self, session_manager: SessionManager) -> None:
        self._session_manager = session_manager

    def create_aws_agent(
        self,
        step_callback: Optional[Callable] = None,
        model_id: str = DEFAULT_MODEL_ID,
    ) -> CodeAgent:
        """Create the original AWS agent (cora)."""
        agent = cora_agent(model_id=model_id)
        if step_callback:
            from smolagents.memory import ActionStep, PlanningStep, FinalAnswerStep

            agent.step_callbacks.register(PlanningStep, step_callback)
            agent.step_callbacks.register(ActionStep, step_callback)
            agent.step_callbacks.register(FinalAnswerStep, step_callback)
        return agent

    def create_manager_agent(
        self,
        step_callback: Optional[Callable] = None,
        model_id: str = DEFAULT_MODEL_ID,
    ) -> CodeAgent:
        """Create the manager agent (orchestrates AWS + Diagramer)."""
        agent = manager_agent(model_id=model_id)
        if step_callback:
            from smolagents.memory import ActionStep, PlanningStep, FinalAnswerStep

            agent.step_callbacks.register(PlanningStep, step_callback)
            agent.step_callbacks.register(ActionStep, step_callback)
            agent.step_callbacks.register(FinalAnswerStep, step_callback)
        return agent

    def create_fresh_agent(
        self,
        step_callback: Optional[Callable] = None,
        model_id: str = DEFAULT_MODEL_ID,
        use_manager: bool = False,
    ) -> CodeAgent:
        """Create a new CodeAgent with empty memory and optional step callback."""
        if use_manager:
            return self.create_manager_agent(step_callback, model_id)
        return self.create_aws_agent(step_callback, model_id)

    async def get_agent(
        self,
        session_id: str,
        step_callback: Optional[Callable] = None,
        model_id: str = DEFAULT_MODEL_ID,
        use_manager: bool = False,
    ) -> CodeAgent:
        """Get an agent for a session, restoring its memory state if available."""
        agent = self.create_fresh_agent(step_callback, model_id, use_manager)
        steps = await self._session_manager.load_agent_state(session_id)
        if steps and hasattr(agent, "memory") and agent.memory:
            agent.memory.steps = steps
            logger.info(f"Restored {len(steps)} steps for session {session_id}")
        return agent

    def save_agent(self, agent: CodeAgent, session_id: str, run_number: int) -> None:
        """Save an agent's memory state for a session (non-blocking)."""
        self._session_manager.save_agent_state(agent, session_id, run_number)
