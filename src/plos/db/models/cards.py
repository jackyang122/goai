"""Flash cards scheduled by FSRS (py-fsrs). Columns are sufficient to reconstruct an
fsrs ``Card`` so scheduling state survives restarts."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class FlashCard(Base):
    __tablename__ = "flash_cards"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    learner_id: Mapped[str] = mapped_column(String, ForeignKey("learners.id"), index=True)
    front: Mapped[str] = mapped_column(Text)
    back: Mapped[str] = mapped_column(Text)
    topic: Mapped[str] = mapped_column(String, index=True)
    due: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    # ── FSRS scheduling state ───────────────────────────────────────────────
    stability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    difficulty: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    state: Mapped[int] = mapped_column(Integer, default=0)  # 0 new,1 learning,2 review,3 relearning
    reps: Mapped[int] = mapped_column(Integer, default=0)
    lapses: Mapped[int] = mapped_column(Integer, default=0)
    last_review: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    elapsed_days: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_days: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
