"""Flashcard review request (FSRS rating 1..4) and due-card query."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .common import CamelModel
from .learner import FlashCard


class CardReviewRequest(CamelModel):
    rating: int = Field(..., ge=1, le=4)  # 1 again | 2 hard | 3 good | 4 easy
    learnerId: str


class CardReviewResult(CamelModel):
    card: FlashCard
    nextDue: str
    reps: int
    lapses: int
