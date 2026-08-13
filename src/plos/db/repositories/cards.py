"""Flash-card repository (FSRS scheduling state lives on the row)."""

from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import select

from ..models.cards import FlashCard
from .base import BaseRepository


class CardRepository(BaseRepository[FlashCard]):
    model = FlashCard

    async def list_due(self, learner_id: str, now: datetime, limit: int = 50) -> List[FlashCard]:
        stmt = (
            select(FlashCard)
            .where(FlashCard.learner_id == learner_id, FlashCard.due <= now)
            .order_by(FlashCard.due.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_learner(self, learner_id: str, limit: int = 100) -> List[FlashCard]:
        stmt = (
            select(FlashCard)
            .where(FlashCard.learner_id == learner_id)
            .order_by(FlashCard.due.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
