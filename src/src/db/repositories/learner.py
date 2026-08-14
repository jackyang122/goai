"""Learner + activity repositories."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy import select, update

from ..models.learners import Activity, Learner
from .base import BaseRepository


class LearnerRepository(BaseRepository[Learner]):
    model = Learner

    async def get(self, id_: str) -> Optional[Learner]:
        return await self.session.get(Learner, id_)

    async def update_preferences(self, id_: str, prefs: dict) -> None:
        await self.session.execute(
            update(Learner).where(Learner.id == id_).values(preferences=prefs)
        )

    async def bump(self, id_: str, *, questions: int = 0, session: bool = False) -> None:
        values: dict = {}
        if questions:
            values["weekly_question_count"] = Learner.weekly_question_count + questions
        if session:
            values["session_count"] = Learner.session_count + 1
        if values:
            await self.session.execute(update(Learner).where(Learner.id == id_).values(**values))

    async def add_study_time(self, id_: str, minutes: int, today: date) -> None:
        """Accrue minutes; reset the 'today' bucket if the calendar day rolled over."""
        learner = await self.get(id_)
        if learner is None:
            return
        if learner.study_time_today_date != today:
            learner.study_time_today_date = today
            learner.study_time_today_min = 0
        learner.study_time_today_min += minutes
        learner.study_time_total_min += minutes


class ActivityRepository(BaseRepository[Activity]):
    model = Activity

    async def list_recent(self, learner_id: str, limit: int = 8) -> List[Activity]:
        stmt = (
            select(Activity)
            .where(Activity.learner_id == learner_id)
            .order_by(Activity.ts.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
