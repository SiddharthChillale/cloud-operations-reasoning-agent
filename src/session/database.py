import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.config import get_config
from src.session.models import (
    Base,
    Message,
    MessageRole,
    Session,
    SessionStatus,
    AgentRunMetrics,
)


class SessionDatabase:
    def __init__(self, db_url: Optional[str] = None):
        if db_url is None:
            # Strictly use config which enforces DATABASE_URL presence
            db_url = get_config().database_url

        # Ensure we use the asyncpg driver
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def init_db(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def _generate_session_id(self) -> str:
        return str(uuid.uuid4())

    async def create_session(self, title: str = "New Session") -> Session:
        if not title:
            title = "New Session"

        session_id = self._generate_session_id()
        async with self.async_session() as session:
            new_session = Session(
                id=session_id,
                title=title,
                status=SessionStatus.IDLE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=True,
            )
            # Deactivate other sessions
            await session.execute(update(Session).values(is_active=False))

            session.add(new_session)
            await session.commit()
            return new_session

    async def get_session(self, session_id: str) -> Optional[Session]:
        async with self.async_session() as session:
            stmt = select(Session).where(Session.id == session_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_all_sessions(self) -> List[Session]:
        async with self.async_session() as session:
            stmt = select(Session).order_by(Session.updated_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_most_recent_session(self) -> Optional[Session]:
        async with self.async_session() as session:
            stmt = select(Session).order_by(Session.updated_at.desc()).limit(1)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def update_session_title(self, session_id: str, title: str) -> None:
        async with self.async_session() as session:
            stmt = (
                update(Session)
                .where(Session.id == session_id)
                .values(title=title, updated_at=datetime.now())
            )
            await session.execute(stmt)
            await session.commit()

    async def update_session_status(
        self, session_id: str, status: SessionStatus
    ) -> None:
        async with self.async_session() as session:
            stmt = (
                update(Session)
                .where(Session.id == session_id)
                .values(status=status, updated_at=datetime.now())
            )
            await session.execute(stmt)
            await session.commit()

    async def get_session_status(self, session_id: str) -> Optional[SessionStatus]:
        async with self.async_session() as session:
            stmt = select(Session.status).where(Session.id == session_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def update_session_timestamp(self, session_id: str) -> None:
        async with self.async_session() as session:
            stmt = (
                update(Session)
                .where(Session.id == session_id)
                .values(updated_at=datetime.now())
            )
            await session.execute(stmt)
            await session.commit()

    async def save_agent_steps(self, session_id: str, agent_steps: bytes) -> None:
        async with self.async_session() as session:
            stmt = (
                update(Session)
                .where(Session.id == session_id)
                .values(agent_steps=agent_steps, updated_at=datetime.now())
            )
            await session.execute(stmt)
            await session.commit()

    async def set_active_session(self, session_id: str) -> None:
        async with self.async_session() as session:
            await session.execute(update(Session).values(is_active=False))
            stmt = (
                update(Session)
                .where(Session.id == session_id)
                .values(is_active=True, updated_at=datetime.now())
            )
            await session.execute(stmt)
            await session.commit()

    async def add_message(
        self, session_id: str, role: MessageRole, content: str
    ) -> Message:
        async with self.async_session() as session:
            new_message = Message(
                session_id=session_id,
                role=role,
                content=content,
                timestamp=datetime.now(),
            )
            session.add(new_message)
            # Update session timestamp
            await session.execute(
                update(Session)
                .where(Session.id == session_id)
                .values(updated_at=datetime.now())
            )
            await session.commit()
            return new_message

    async def delete_session(self, session_id: str) -> None:
        async with self.async_session() as session:
            # Cascade delete is handled by SQLAlchemy relationship or DB constraints
            await session.execute(delete(Session).where(Session.id == session_id))
            await session.commit()

    async def get_next_run_number(self, session_id: str) -> int:
        async with self.async_session() as session:
            stmt = select(func.max(AgentRunMetrics.run_number)).where(
                AgentRunMetrics.session_id == session_id
            )
            result = await session.execute(stmt)
            max_run = result.scalar()
            return (max_run or 0) + 1

    async def get_next_step_number(self, session_id: str, run_number: int) -> int:
        async with self.async_session() as session:
            stmt = select(func.max(AgentRunMetrics.step_number)).where(
                AgentRunMetrics.session_id == session_id,
                AgentRunMetrics.run_number == run_number,
            )
            result = await session.execute(stmt)
            max_step = result.scalar()
            return (max_step or 0) + 1

    async def save_step_token(
        self,
        session_id: str,
        run_number: int,
        step_number: int,
        step_type: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        total_tokens = input_tokens + output_tokens
        async with self.async_session() as session:
            # Check if exists to emulate ON CONFLICT
            stmt = select(AgentRunMetrics).where(
                AgentRunMetrics.session_id == session_id,
                AgentRunMetrics.run_number == run_number,
                AgentRunMetrics.step_number == step_number,
            )
            result = await session.execute(stmt)
            metric = result.scalar_one_or_none()

            if metric:
                metric.step_type = step_type
                metric.input_tokens = input_tokens
                metric.output_tokens = output_tokens
                metric.total_tokens = total_tokens
                metric.created_at = datetime.now()
            else:
                metric = AgentRunMetrics(
                    session_id=session_id,
                    run_number=run_number,
                    step_number=step_number,
                    step_type=step_type,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    created_at=datetime.now(),
                )
                session.add(metric)

            await session.commit()

    async def get_step_token(
        self, session_id: str, run_number: int, step_number: int
    ) -> Optional[dict]:
        async with self.async_session() as session:
            stmt = select(AgentRunMetrics).where(
                AgentRunMetrics.session_id == session_id,
                AgentRunMetrics.run_number == run_number,
                AgentRunMetrics.step_number == step_number,
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row:
                return {
                    "id": row.id,
                    "session_id": row.session_id,
                    "run_number": row.run_number,
                    "step_number": row.step_number,
                    "step_type": row.step_type,
                    "input_tokens": row.input_tokens,
                    "output_tokens": row.output_tokens,
                    "total_tokens": row.total_tokens,
                    "created_at": row.created_at.isoformat(),
                }
            return None

    async def get_run_tokens(self, session_id: str, run_number: int) -> dict:
        async with self.async_session() as session:
            stmt = (
                select(AgentRunMetrics)
                .where(
                    AgentRunMetrics.session_id == session_id,
                    AgentRunMetrics.run_number == run_number,
                )
                .order_by(AgentRunMetrics.step_number.asc())
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()

            if not rows:
                return {
                    "session_id": session_id,
                    "run_number": run_number,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "steps": [],
                }

            steps = [
                {
                    "step_number": row.step_number,
                    "step_type": row.step_type,
                    "input_tokens": row.input_tokens,
                    "output_tokens": row.output_tokens,
                    "total_tokens": row.total_tokens,
                }
                for row in rows
            ]

            return {
                "session_id": session_id,
                "run_number": run_number,
                "input_tokens": sum(row.input_tokens for row in rows),
                "output_tokens": sum(row.output_tokens for row in rows),
                "total_tokens": sum(row.total_tokens for row in rows),
                "steps": steps,
            }

    async def get_session_tokens(self, session_id: str) -> dict:
        async with self.async_session() as session:
            stmt = (
                select(
                    AgentRunMetrics.run_number,
                    func.sum(AgentRunMetrics.input_tokens).label("input_tokens"),
                    func.sum(AgentRunMetrics.output_tokens).label("output_tokens"),
                    func.sum(AgentRunMetrics.total_tokens).label("total_tokens"),
                )
                .where(AgentRunMetrics.session_id == session_id)
                .group_by(AgentRunMetrics.run_number)
                .order_by(AgentRunMetrics.run_number.asc())
            )
            result = await session.execute(stmt)
            rows = result.all()

            if not rows:
                return {
                    "session_id": session_id,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "runs": [],
                }

            runs = [
                {
                    "run_number": row.run_number,
                    "input_tokens": row.input_tokens,
                    "output_tokens": row.output_tokens,
                    "total_tokens": row.total_tokens,
                }
                for row in rows
            ]

            return {
                "session_id": session_id,
                "input_tokens": sum(r["input_tokens"] for r in runs),
                "output_tokens": sum(r["output_tokens"] for r in runs),
                "total_tokens": sum(r["total_tokens"] for r in runs),
                "runs": runs,
            }

    async def get_all_run_tokens(self, session_id: str) -> List[dict]:
        res = await self.get_session_tokens(session_id)
        return res["runs"]

    async def save_agent_run_metrics(
        self,
        session_id: str,
        run_number: int,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        await self.save_step_token(
            session_id, run_number, 0, "summary", input_tokens, output_tokens
        )

    async def get_agent_run_metrics(self, session_id: str) -> List[dict]:
        async with self.async_session() as session:
            stmt = (
                select(AgentRunMetrics)
                .where(AgentRunMetrics.session_id == session_id)
                .order_by(
                    AgentRunMetrics.run_number.asc(), AgentRunMetrics.step_number.asc()
                )
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()
            return [
                {
                    "id": row.id,
                    "session_id": row.session_id,
                    "run_number": row.run_number,
                    "step_number": row.step_number,
                    "step_type": row.step_type,
                    "input_tokens": row.input_tokens,
                    "output_tokens": row.output_tokens,
                    "total_tokens": row.total_tokens,
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ]

    async def get_latest_run_number(self, session_id: str) -> int:
        async with self.async_session() as session:
            stmt = select(func.max(AgentRunMetrics.run_number)).where(
                AgentRunMetrics.session_id == session_id
            )
            result = await session.execute(stmt)
            max_run = result.scalar()
            return max_run if max_run is not None else 0
