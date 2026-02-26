import asyncio
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Optional

from smolagents import CodeAgent
from smolagents.memory import ActionStep, PlanningStep

from src.session.database import SessionDatabase
from src.session.models import Message, MessageRole, Session

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db = SessionDatabase(db_path)
        self._current_session: Optional[Session] = None
        self._sessions: list[Session] = []
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return
        await self.db.init_db()
        self._initialized = True
        await self.load_sessions()

    async def load_sessions(self) -> None:
        self._sessions = await self.db.get_all_sessions()
        logger.debug(f"Loaded {len(self._sessions)} sessions from database")

    async def create_session(self, title: Optional[str] = "New Session") -> Session:
        final_title = (
            title
            if title and title != "New Session"
            else f"Session {datetime.now().strftime('%H:%M')}"
        )
        logger.info(f"Creating new session: {final_title}")
        session = await self.db.create_session(final_title)
        self._current_session = session
        self._sessions.insert(0, session)
        logger.info(f"Created session {session.id}: {session.title}")
        return session

    async def get_or_create_session(self) -> Session:
        if self._current_session is not None:
            return self._current_session
        recent = await self.db.get_most_recent_session()
        if recent is not None:
            self._current_session = recent
            return recent
        return await self.create_session()

    async def switch_session(self, session_id: str) -> Optional[Session]:
        logger.info(f"Switching to session {session_id}")
        session = await self.db.get_session(session_id)
        if session is not None:
            await self.db.set_active_session(session_id)
            self._current_session = session

            if not any(s.id == session_id for s in self._sessions):
                self._sessions.append(session)

            logger.info(f"Switched to session {session_id}: {session.title}")
            return session
        logger.warning(f"Session {session_id} not found")
        return None

    async def get_session(self, session_id: str) -> Optional[Session]:
        return await self.db.get_session(session_id)

    async def add_message(
        self, role: MessageRole, content: str, session_id: Optional[str] = None
    ) -> Message:
        target_session_id = session_id or (
            self._current_session.id if self._current_session else None
        )
        if target_session_id is None:
            raise ValueError("No active session")
        message = await self.db.add_message(target_session_id, role, content)
        if self._current_session and self._current_session.id == target_session_id:
            self._current_session.messages.append(message)
        logger.debug(f"Added {role.value} message to session {target_session_id}")
        return message

    async def update_session_title(self, session_id: str, title: str) -> None:
        logger.info(f"Updating session {session_id} title to: {title}")
        await self.db.update_session_title(session_id, title)
        for session in self._sessions:
            if session.id == session_id:
                session.title = title
                break
        if self._current_session and self._current_session.id == session_id:
            self._current_session.title = title
        logger.info(f"Session {session_id} title updated to: {title}")

    def get_current_session(self) -> Optional[Session]:
        return self._current_session

    def get_all_sessions(self) -> list[Session]:
        return self._sessions

    async def save_session(self, session: Session) -> None:
        if session.id:
            await self.db.update_session_timestamp(session.id)

    async def save_agent_steps(self, session_id: str, agent_steps: bytes) -> None:
        await self.db.save_agent_steps(session_id, agent_steps)
        for session in self._sessions:
            if session.id == session_id:
                session.agent_steps = agent_steps
                break
        if self._current_session and self._current_session.id == session_id:
            self._current_session.agent_steps = agent_steps

    async def get_agent_steps(self, session_id: str) -> Optional[bytes]:
        for session in self._sessions:
            if session.id == session_id:
                return session.agent_steps if session.agent_steps else None

        session = await self.db.get_session(session_id)
        if session:
            return session.agent_steps if session.agent_steps else None
        return None

    def get_current_agent_steps(self) -> Optional[bytes]:
        if self._current_session:
            return (
                self._current_session.agent_steps
                if self._current_session.agent_steps
                else None
            )
        return None

    async def load_agent_state(self, session_id: str) -> list:
        """Load agent memory steps from database for a session."""
        agent_steps_bytes = self.get_current_agent_steps()
        if not agent_steps_bytes:
            agent_steps_bytes = await self.get_agent_steps(session_id)

        if not agent_steps_bytes:
            return []

        try:
            return pickle.loads(agent_steps_bytes)
        except (pickle.PickleError, EOFError, TypeError) as e:
            logger.warning(f"Failed to load agent state for session {session_id}: {e}")
            return []

    def extract_tokens_from_step(self, step, step_index: int = 0) -> Optional[dict]:
        """Extract token usage from an ActionStep or PlanningStep."""
        if not hasattr(step, "token_usage") or not step.token_usage:
            return None

        tu = step.token_usage
        step_type = type(step).__name__
        return {
            "step_number": step_index + 1,
            "step_type": step_type,
            "input_tokens": getattr(tu, "input_tokens", 0),
            "output_tokens": getattr(tu, "output_tokens", 0),
            "total_tokens": getattr(tu, "total_tokens", 0),
        }

    async def save_step_token_from_step(
        self, session_id: str, run_number: int, step_index: int, step
    ) -> None:
        """Extract and save token usage from a step (non-blocking)."""
        token_data = self.extract_tokens_from_step(step, step_index)
        if token_data:
            try:
                await self.db.save_step_token(
                    session_id,
                    run_number,
                    token_data["step_number"],
                    token_data["step_type"],
                    token_data["input_tokens"],
                    token_data["output_tokens"],
                )
            except Exception as e:
                logger.warning(
                    f"Failed to save step token for session {session_id}, run {run_number}: {e}"
                )

    def save_agent_state(
        self, agent: CodeAgent, session_id: str, run_number: int
    ) -> None:
        """Save agent memory steps and step tokens to database (non-blocking)."""
        try:
            steps = (
                agent.memory.steps if hasattr(agent, "memory") and agent.memory else []
            )

            pickled = pickle.dumps(steps)
            asyncio.create_task(self.save_agent_steps(session_id, pickled))

            for step_index, step in enumerate(steps):
                try:
                    if isinstance(step, (ActionStep, PlanningStep)):
                        token_usage = getattr(step, "token_usage", None)
                        if token_usage:
                            asyncio.create_task(
                                self.save_step_token_from_step(
                                    session_id, run_number, step_index, step
                                )
                            )
                except Exception:
                    pass
        except (pickle.PickleError, TypeError) as e:
            logger.warning(f"Failed to save agent state for session {session_id}: {e}")

    async def get_next_run_number(self, session_id: str) -> int:
        return await self.db.get_next_run_number(session_id)

    async def get_step_token(
        self, session_id: str, run_number: int, step_number: int
    ) -> Optional[dict]:
        return await self.db.get_step_token(session_id, run_number, step_number)

    async def get_run_tokens(self, session_id: str, run_number: int) -> dict:
        return await self.db.get_run_tokens(session_id, run_number)

    async def get_session_tokens(self, session_id: str) -> dict:
        return await self.db.get_session_tokens(session_id)

    async def get_all_run_tokens(self, session_id: str) -> list[dict]:
        return await self.db.get_all_run_tokens(session_id)

    async def save_agent_run_metrics(
        self,
        session_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        run_count = await self.get_agent_run_count(session_id)
        await self.db.save_agent_run_metrics(
            session_id, run_count + 1, input_tokens, output_tokens
        )
        logger.debug(
            f"Saved run {run_count + 1} metrics for session {session_id}: {input_tokens} in, {output_tokens} out"
        )

    async def get_agent_run_metrics(self, session_id: str) -> list[dict]:
        return await self.db.get_agent_run_metrics(session_id)

    async def get_agent_run_count(self, session_id: str) -> int:
        return await self.db.get_latest_run_number(session_id)

    async def get_session_cumulative_tokens(self, session_id: str) -> dict:
        runs = await self.get_agent_run_metrics(session_id)
        return {
            "input_tokens": sum(r["input_tokens"] for r in runs),
            "output_tokens": sum(r["output_tokens"] for r in runs),
        }
