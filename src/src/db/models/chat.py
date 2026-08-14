"""Threads, messages, attachments (assistant-ui compatible)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class Thread(Base):
    __tablename__ = "threads"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    learner_id: Mapped[str] = mapped_column(String, ForeignKey("learners.id"), index=True)
    title: Mapped[str] = mapped_column(Text, default="")
    persona: Mapped[str] = mapped_column(String, default="teacher")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    seq: Mapped[int] = mapped_column(Integer, default=0)  # message ordering guard


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    thread_id: Mapped[str] = mapped_column(String, ForeignKey("threads.id"), index=True)
    learner_id: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String)  # user | assistant | system | tool
    content: Mapped[str] = mapped_column(Text, default="")
    skill: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="complete")  # streaming|complete|error
    citations: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # 8-scenario rich content
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    seq: Mapped[int] = mapped_column(Integer, default=0)


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    thread_id: Mapped[str] = mapped_column(String, ForeignKey("threads.id"), index=True)
    learner_id: Mapped[str] = mapped_column(String, index=True)
    filename: Mapped[str] = mapped_column(Text)
    mime: Mapped[str] = mapped_column(String, default="application/octet-stream")
    size: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kb_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # ingested into this KB
    status: Mapped[str] = mapped_column(String, default="indexing")  # indexing|ready|error
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
