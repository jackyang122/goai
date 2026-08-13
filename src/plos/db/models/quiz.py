"""Question bank + error book."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class Question(Base):
    """Topic-indexed question bank (seeded from web/lib/api/seed.ts QUESTION_BANK)."""

    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    type: Mapped[str] = mapped_column(String)  # choice | fill | open
    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    answer: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text, default="")
    topic: Mapped[str] = mapped_column(String, index=True)
    skill: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class ErrorBook(Base):
    __tablename__ = "error_book"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    learner_id: Mapped[str] = mapped_column(String, ForeignKey("learners.id"), index=True)
    question_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    question_snapshot: Mapped[dict] = mapped_column(JSONB)  # full Question at time of error
    user_answer: Mapped[str] = mapped_column(Text)
    error_type: Mapped[str] = mapped_column(String, default="待诊断")
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    reviewed: Mapped[bool] = mapped_column(default=False)
