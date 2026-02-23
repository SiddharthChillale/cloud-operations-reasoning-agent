from datetime import datetime
from pathlib import Path
from typing import Optional

import logging

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

    async def switch_session(self, session_id: int) -> Optional[Session]:
        logger.info(f"Switching to session {session_id}")
        session = await self.db.get_session(session_id)
        if session is not None:
            await self.db.set_active_session(session_id)
            self._current_session = session
            logger.info(f"Switched to session {session_id}: {session.title}")
            return session
        logger.warning(f"Session {session_id} not found")
        return None

    async def get_session(self, session_id: int) -> Optional[Session]:
        return await self.db.get_session(session_id)

    async def add_message(
        self, role: MessageRole, content: str, session_id: Optional[int] = None
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

    async def update_session_title(self, session_id: int, title: str) -> None:
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

    async def save_agent_steps(self, session_id: int, agent_steps: bytes) -> None:
        await self.db.save_agent_steps(session_id, agent_steps)
        for session in self._sessions:
            if session.id == session_id:
                session.agent_steps = agent_steps
                break
        if self._current_session and self._current_session.id == session_id:
            self._current_session.agent_steps = agent_steps

    async def get_agent_steps(self, session_id: int) -> Optional[bytes]:
        for session in self._sessions:
            if session.id == session_id:
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
