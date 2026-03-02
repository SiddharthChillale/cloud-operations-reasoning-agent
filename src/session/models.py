from __future__ import annotations

import os
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    LargeBinary,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class MessageRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class SessionStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"


class Base(DeclarativeBase):
    pass


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # UUID
    title: Mapped[str] = mapped_column(String, default="New Session")
    status: Mapped[SessionStatus] = mapped_column(
        SQLEnum(SessionStatus), default=SessionStatus.IDLE
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    agent_steps: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)

    messages: Mapped[List[Message]] = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    metrics: Mapped[List[AgentRunMetrics]] = relationship(
        "AgentRunMetrics",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"))
    role: Mapped[MessageRole] = mapped_column(SQLEnum(MessageRole))
    content: Mapped[str] = mapped_column(String)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    session: Mapped[Session] = relationship("Session", back_populates="messages")


class AgentRunMetrics(Base):
    __tablename__ = "agent_run_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"))
    run_number: Mapped[int] = mapped_column(Integer)
    step_number: Mapped[int] = mapped_column(Integer, default=1)
    step_type: Mapped[str] = mapped_column(String)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    session: Mapped[Session] = relationship("Session", back_populates="metrics")
