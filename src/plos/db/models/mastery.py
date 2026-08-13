"""Mastery (BKT-tracked) + per-topic BKT parameters.

``Mastery`` is the *read* model surfaced to the frontend. The **only** writer of its
``level`` / ``trend`` columns is :class:`MasteryEngine <plos.domain.mastery.MasteryEngine>`
(via :class:`MasteryRepository._upsert`). Skills never write here directly.

``MasteryParam`` holds the BKT prior/transition/guess/slip per topic; online inference
uses the closed-form forward filter, ``pybkt.fit()`` runs offline only.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class Mastery(Base):
    __tablename__ = "mastery"
    __table_args__ = (UniqueConstraint("learner_id", "topic", name="uq_mastery_learner_topic"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    learner_id: Mapped[str] = mapped_column(String, ForeignKey("learners.id"), index=True)
    topic: Mapped[str] = mapped_column(String, index=True)
    subject: Mapped[str] = mapped_column(String, default="")
    level: Mapped[float] = mapped_column(Float, default=0.0)  # CHECK (level BETWEEN 0 AND 1)
    trend: Mapped[str] = mapped_column(String, default="flat")  # up | down | flat
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    last_practiced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class MasteryParam(Base):
    """BKT parameters {L0, T, S, G} per (learner, topic). Defaults seedable."""

    __tablename__ = "mastery_params"
    __table_args__ = (UniqueConstraint("learner_id", "topic", name="uq_mastery_params_topic"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    learner_id: Mapped[str] = mapped_column(String, ForeignKey("learners.id"), index=True)
    topic: Mapped[str] = mapped_column(String, index=True)
    l0: Mapped[float] = mapped_column(Float, default=0.5)  # P(known) prior
    t_transit: Mapped[float] = mapped_column("t_transit", Float, default=0.1)  # P(learn)
    slip: Mapped[float] = mapped_column(Float, default=0.2)  # P(wrong | known)
    guess: Mapped[float] = mapped_column(Float, default=0.2)  # P(correct | unknown)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
