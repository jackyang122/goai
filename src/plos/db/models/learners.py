"""Learner + recent-activity models."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class Learner(Base):
    __tablename__ = "learners"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, default="同学")
    streak: Mapped[int] = mapped_column(Integer, default=0)
    study_time_today_min: Mapped[int] = mapped_column(Integer, default=0)
    study_time_today_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    study_time_total_min: Mapped[int] = mapped_column(Integer, default=0)
    weekly_change: Mapped[float] = mapped_column(default=0.0)
    session_count: Mapped[int] = mapped_column(Integer, default=0)
    weekly_question_count: Mapped[int] = mapped_column(Integer, default=0)
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Activity(Base):
    __tablename__ = "activity"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    learner_id: Mapped[str] = mapped_column(String, index=True)
    type: Mapped[str] = mapped_column(String)  # learn | practice | review | chat
    label: Mapped[str] = mapped_column(Text)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
