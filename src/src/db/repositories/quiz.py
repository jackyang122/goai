"""Question + error-book repositories."""

from __future__ import annotations

from typing import List

from sqlalchemy import select

from ..models.quiz import ErrorBook, Question
from .base import BaseRepository


class QuestionRepository(BaseRepository[Question]):
    model = Question

    async def list_by_topic(self, topic: str, limit: int = 10) -> List[Question]:
        stmt = (
            select(Question)
            .where(Question.topic == topic)
            .order_by(Question.id)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_any(self, limit: int = 20) -> List[Question]:
        stmt = select(Question).order_by(Question.topic).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ErrorBookRepository(BaseRepository[ErrorBook]):
    model = ErrorBook

    async def list_by_learner(self, learner_id: str, limit: int = 50) -> List[ErrorBook]:
        stmt = (
            select(ErrorBook)
            .where(ErrorBook.learner_id == learner_id)
            .order_by(ErrorBook.ts.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
