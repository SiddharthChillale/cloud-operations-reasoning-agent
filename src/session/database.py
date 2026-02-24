import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.session.models import Message, MessageRole, Session


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
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
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

            # Add agent_steps column if it doesn't exist (migration-safe)
            cursor = await db.execute("PRAGMA table_info(sessions)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            if "agent_steps" not in column_names:
                await db.execute(
                    "ALTER TABLE sessions ADD COLUMN agent_steps BLOB DEFAULT NULL"
                )

            # Create agent_run_metrics table for per-run token tracking
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_run_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    run_number INTEGER NOT NULL,
                    input_tokens INTEGER NOT NULL DEFAULT 0,
                    output_tokens INTEGER NOT NULL DEFAULT 0,
                    total_tokens INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                    UNIQUE(session_id, run_number)
                )
                """
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_run_metrics_session_id ON agent_run_metrics(session_id)"
            )

            await db.commit()

    async def create_session(self, title: str = "New Session") -> Session:
        if not title:
            title = "New Session"
        now = datetime.now().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO sessions (title, created_at, updated_at, is_active) VALUES (?, ?, ?, 1)",
                (title, now, now),
            )
            session_id = cursor.lastrowid
            await db.commit()
            return Session(
                id=session_id,
                title=title,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=True,
            )

    async def get_session(self, session_id: int) -> Optional[Session]:
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
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    is_active=bool(row["is_active"]),
                    messages=messages,
                    agent_steps=row["agent_steps"] if row["agent_steps"] else b"",
                )

    async def _get_messages_for_session(
        self, db: aiosqlite.Connection, session_id: int
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

    async def update_session_title(self, session_id: int, title: str) -> None:
        now = datetime.now().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
                (title, now, session_id),
            )
            await db.commit()

    async def update_session_timestamp(self, session_id: int) -> None:
        now = datetime.now().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, session_id),
            )
            await db.commit()

    async def save_agent_steps(self, session_id: int, agent_steps: bytes) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE sessions SET agent_steps = ? WHERE id = ?",
                (agent_steps, session_id),
            )
            await db.commit()

    async def set_active_session(self, session_id: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE sessions SET is_active = 0")
            await db.execute(
                "UPDATE sessions SET is_active = 1, updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), session_id),
            )
            await db.commit()

    async def add_message(
        self, session_id: int, role: MessageRole, content: str
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

    async def delete_session(self, session_id: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            await db.execute(
                "DELETE FROM agent_run_metrics WHERE session_id = ?", (session_id,)
            )
            await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            await db.commit()

    async def save_agent_run_metrics(
        self,
        session_id: int,
        run_number: int,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        now = datetime.now().isoformat()
        total_tokens = input_tokens + output_tokens
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO agent_run_metrics (session_id, run_number, input_tokens, output_tokens, total_tokens, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id, run_number) DO UPDATE SET
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

    async def get_agent_run_metrics(self, session_id: int) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM agent_run_metrics WHERE session_id = ? ORDER BY run_number ASC",
                (session_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "id": row["id"],
                        "session_id": row["session_id"],
                        "run_number": row["run_number"],
                        "input_tokens": row["input_tokens"],
                        "output_tokens": row["output_tokens"],
                        "total_tokens": row["total_tokens"],
                        "created_at": row["created_at"],
                    }
                    for row in rows
                ]

    async def get_latest_run_number(self, session_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT MAX(run_number) as max_run FROM agent_run_metrics WHERE session_id = ?",
                (session_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return 0
                return row[0] if row[0] is not None else 0
