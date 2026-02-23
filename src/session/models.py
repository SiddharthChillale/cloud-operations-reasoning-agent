from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class MessageRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


@dataclass
class Message:
    id: Optional[int] = None
    session_id: int = 0
    role: MessageRole = MessageRole.USER
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Session:
    id: Optional[int] = None
    title: str = "New Session"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = False
    messages: list[Message] = field(default_factory=list)
    agent_steps: bytes = b""  # Serialized agent.memory.steps
