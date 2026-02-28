import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiosqlite

from src.session.models import Message, MessageRole, Session, SessionStatus


class SessionDatabase:
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.home() / ".cora" / "sessions.db"
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def init_db(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'idle',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 0,
                    agent_steps BLOB DEFAULT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
                """
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON sessions(updated_at)"
            )

            # Agent step tokens table - stores per-step token usage
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_run_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    run_number INTEGER NOT NULL,
                    step_number INTEGER NOT NULL DEFAULT 1,
                    step_type TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL DEFAULT 0,
                    output_tokens INTEGER NOT NULL DEFAULT 0,
                    total_tokens INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                    UNIQUE(session_id, run_number, step_number)
                )
                """
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_run_metrics_session_id ON agent_run_metrics(session_id)"
            )

            await db.commit()

    def _generate_session_id(self) -> str:
        return str(uuid.uuid4())

    async def create_session(self, title: str = "New Session") -> Session:
        if not title:
            title = "New Session"
        now = datetime.now().isoformat()
        session_id = self._generate_session_id()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO sessions (id, title, status, created_at, updated_at, is_active) VALUES (?, ?, ?, ?, ?, 1)",
                (session_id, title, SessionStatus.IDLE.value, now, now),
            )
            await db.commit()
            return Session(
                id=session_id,
                title=title,
                status=SessionStatus.IDLE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=True,
            )

    async def get_session(self, session_id: str) -> Optional[Session]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None

                messages = await self._get_messages_for_session(db, session_id)

                return Session(
                    id=row["id"],
                    title=row["title"],
                    status=SessionStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    is_active=bool(row["is_active"]),
                    messages=messages,
                    agent_steps=row["agent_steps"] if row["agent_steps"] else b"",
                )

    async def _get_messages_for_session(
        self, db: aiosqlite.Connection, session_id: str
    ) -> list[Message]:
        messages = []
        async with db.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
            (session_id,),
        ) as cursor:
            async for row in cursor:
                messages.append(
                    Message(
                        id=row["id"],
                        session_id=row["session_id"],
                        role=MessageRole(row["role"]),
                        content=row["content"],
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                    )
                )
        return messages

    async def get_all_sessions(self) -> list[Session]:
        sessions = []
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM sessions ORDER BY updated_at DESC"
            ) as cursor:
                async for row in cursor:
                    messages = await self._get_messages_for_session(db, row["id"])
                    sessions.append(
                        Session(
                            id=row["id"],
                            title=row["title"],
                            status=SessionStatus(row["status"]),
                            created_at=datetime.fromisoformat(row["created_at"]),
                            updated_at=datetime.fromisoformat(row["updated_at"]),
                            is_active=bool(row["is_active"]),
                            messages=messages,
                            agent_steps=row["agent_steps"]
                            if row["agent_steps"]
                            else b"",
                        )
                    )
        return sessions

    async def get_most_recent_session(self) -> Optional[Session]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT 1"
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return await self.get_session(row["id"])

    async def update_session_title(self, session_id: str, title: str) -> None:
        now = datetime.now().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
                (title, now, session_id),
            )
            await db.commit()

    async def update_session_status(
        self, session_id: str, status: SessionStatus
    ) -> None:
        now = datetime.now().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE sessions SET status = ?, updated_at = ? WHERE id = ?",
                (status.value, now, session_id),
            )
            await db.commit()

    async def get_session_status(self, session_id: str) -> Optional[SessionStatus]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT status FROM sessions WHERE id = ?", (session_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return SessionStatus(row[0])

    async def update_session_timestamp(self, session_id: str) -> None:
        now = datetime.now().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, session_id),
            )
            await db.commit()

    async def save_agent_steps(self, session_id: str, agent_steps: bytes) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE sessions SET agent_steps = ? WHERE id = ?",
                (agent_steps, session_id),
            )
            await db.commit()

    async def set_active_session(self, session_id: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE sessions SET is_active = 0")
            await db.execute(
                "UPDATE sessions SET is_active = 1, updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), session_id),
            )
            await db.commit()

    async def add_message(
        self, session_id: str, role: MessageRole, content: str
    ) -> Message:
        now = datetime.now()
        timestamp = now.isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, role.value, content, timestamp),
            )
            message_id = cursor.lastrowid
            await db.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (timestamp, session_id),
            )
            await db.commit()
            return Message(
                id=message_id,
                session_id=session_id,
                role=role,
                content=content,
                timestamp=now,
            )

    async def delete_session(self, session_id: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            await db.execute(
                "DELETE FROM agent_run_metrics WHERE session_id = ?", (session_id,)
            )
            await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            await db.commit()

    async def get_next_run_number(self, session_id: str) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT MAX(run_number) as max_run FROM agent_run_metrics WHERE session_id = ?",
                (session_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if row is None or row[0] is None:
                    return 1
                return row[0] + 1

    async def get_next_step_number(self, session_id: str, run_number: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT MAX(step_number) as max_step FROM agent_run_metrics WHERE session_id = ? AND run_number = ?",
                (session_id, run_number),
            ) as cursor:
                row = await cursor.fetchone()
                if row is None or row[0] is None:
                    return 1
                return row[0] + 1

    async def save_step_token(
        self,
        session_id: str,
        run_number: int,
        step_number: int,
        step_type: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        now = datetime.now().isoformat()
        total_tokens = input_tokens + output_tokens
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO agent_run_metrics (session_id, run_number, step_number, step_type, input_tokens, output_tokens, total_tokens, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id, run_number, step_number) DO UPDATE SET
                    step_type = excluded.step_type,
                    input_tokens = excluded.input_tokens,
                    output_tokens = excluded.output_tokens,
                    total_tokens = excluded.total_tokens,
                    created_at = excluded.created_at
                """,
                (
                    session_id,
                    run_number,
                    step_number,
                    step_type,
                    input_tokens,
                    output_tokens,
                    total_tokens,
                    now,
                ),
            )
            await db.commit()

    async def get_step_token(
        self, session_id: str, run_number: int, step_number: int
    ) -> Optional[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM agent_run_metrics WHERE session_id = ? AND run_number = ? AND step_number = ?",
                (session_id, run_number, step_number),
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return {
                    "id": row["id"],
                    "session_id": row["session_id"],
                    "run_number": row["run_number"],
                    "step_number": row["step_number"],
                    "step_type": row["step_type"],
                    "input_tokens": row["input_tokens"],
                    "output_tokens": row["output_tokens"],
                    "total_tokens": row["total_tokens"],
                    "created_at": row["created_at"],
                }

    async def get_run_tokens(self, session_id: str, run_number: int) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM agent_run_metrics 
                   WHERE session_id = ? AND run_number = ?
                   ORDER BY step_number ASC""",
                (session_id, run_number),
            ) as cursor:
                rows = await cursor.fetchall()

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
                    "step_number": row["step_number"],
                    "step_type": row["step_type"],
                    "input_tokens": row["input_tokens"],
                    "output_tokens": row["output_tokens"],
                    "total_tokens": row["total_tokens"],
                }
                for row in rows
            ]

            return {
                "session_id": session_id,
                "run_number": run_number,
                "input_tokens": sum(row["input_tokens"] for row in rows),
                "output_tokens": sum(row["output_tokens"] for row in rows),
                "total_tokens": sum(row["total_tokens"] for row in rows),
                "steps": steps,
            }

    async def get_session_tokens(self, session_id: str) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT run_number, 
                          SUM(input_tokens) as input_tokens, 
                          SUM(output_tokens) as output_tokens, 
                          SUM(total_tokens) as total_tokens
                   FROM agent_run_metrics 
                   WHERE session_id = ?
                   GROUP BY run_number
                   ORDER BY run_number ASC""",
                (session_id,),
            ) as cursor:
                rows = await cursor.fetchall()

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
                    "run_number": row["run_number"],
                    "input_tokens": row["input_tokens"],
                    "output_tokens": row["output_tokens"],
                    "total_tokens": row["total_tokens"],
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

    async def get_all_run_tokens(self, session_id: str) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT run_number, 
                          SUM(input_tokens) as input_tokens, 
                          SUM(output_tokens) as output_tokens, 
                          SUM(total_tokens) as total_tokens
                   FROM agent_run_metrics 
                   WHERE session_id = ?
                   GROUP BY run_number
                   ORDER BY run_number ASC""",
                (session_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "run_number": row["run_number"],
                        "input_tokens": row["input_tokens"],
                        "output_tokens": row["output_tokens"],
                        "total_tokens": row["total_tokens"],
                    }
                    for row in rows
                ]

    async def save_agent_run_metrics(
        self,
        session_id: str,
        run_number: int,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        now = datetime.now().isoformat()
        total_tokens = input_tokens + output_tokens
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO agent_run_metrics (session_id, run_number, step_number, input_tokens, output_tokens, total_tokens, created_at)
                VALUES (?, ?, 0, ?, ?, ?, ?)
                ON CONFLICT(session_id, run_number, step_number) DO UPDATE SET
                    input_tokens = excluded.input_tokens,
                    output_tokens = excluded.output_tokens,
                    total_tokens = excluded.total_tokens,
                    created_at = excluded.created_at
                """,
                (
                    session_id,
                    run_number,
                    input_tokens,
                    output_tokens,
                    total_tokens,
                    now,
                ),
            )
            await db.commit()

    async def get_agent_run_metrics(self, session_id: str) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM agent_run_metrics WHERE session_id = ? ORDER BY run_number ASC, step_number ASC",
                (session_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "id": row["id"],
                        "session_id": row["session_id"],
                        "run_number": row["run_number"],
                        "step_number": row["step_number"],
                        "step_type": row["step_type"],
                        "input_tokens": row["input_tokens"],
                        "output_tokens": row["output_tokens"],
                        "total_tokens": row["total_tokens"],
                        "created_at": row["created_at"],
                    }
                    for row in rows
                ]

    async def get_latest_run_number(self, session_id: str) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT MAX(run_number) as max_run FROM agent_run_metrics WHERE session_id = ?",
                (session_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return 0
                return row[0] if row[0] is not None else 0
