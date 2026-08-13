"""Goal + plan-task repositories."""

from __future__ import annotations

from typing import Dict, List

from sqlalchemy import select

from ..models.goals import Goal, PlanTask
from .base import BaseRepository


class GoalRepository(BaseRepository[Goal]):
    model = Goal

    async def list_by_learner(self, learner_id: str) -> List[Goal]:
        stmt = select(Goal).where(Goal.learner_id == learner_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class PlanTaskRepository(BaseRepository[PlanTask]):
    model = PlanTask

    async def list_for_goals(self, goal_ids: List[str]) -> Dict[str, List[PlanTask]]:
        if not goal_ids:
            return {}
        stmt = select(PlanTask).where(PlanTask.goal_id.in_(goal_ids)).order_by(PlanTask.ordering)
        result = await self.session.execute(stmt)
        out: Dict[str, List[PlanTask]] = {gid: [] for gid in goal_ids}
        for task in result.scalars().all():
            out.setdefault(task.goal_id, []).append(task)
        return out

    async def set_done(self, task_id: str, done: bool) -> None:
        task = await self.get(task_id)
        if task is not None:
            task.done = done
