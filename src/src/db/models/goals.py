"""Goals + plan tasks (learning-plan output)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    learner_id: Mapped[str] = mapped_column(String, ForeignKey("learners.id"), index=True)
    title: Mapped[str] = mapped_column(Text)
    subject: Mapped[str] = mapped_column(String, default="")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    source: Mapped[str] = mapped_column(String, default="learning-plan")
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class PlanTask(Base):
    __tablename__ = "plan_tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    goal_id: Mapped[str] = mapped_column(String, ForeignKey("goals.id"), index=True)
    title: Mapped[str] = mapped_column(Text)
    est_minutes: Mapped[int] = mapped_column(Integer, default=0)
    type: Mapped[str] = mapped_column(String, default="learn")  # learn | practice | review
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    ref: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ordering: Mapped[int] = mapped_column(Integer, default=0)
