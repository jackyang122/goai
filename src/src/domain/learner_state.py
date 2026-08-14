"""LearnerStateService — aggregates every table into the ``LearnerState`` the Dashboard
renders. Derived fields (overallMastery, weakPoints) are computed live on every read,
fixing the mock's stale-at-construction bug."""

from __future__ import annotations

import asyncio
from statistics import mean
from typing import Optional

from ..app.errors import not_found
from ..core.time import now_utc, to_iso
from ..db.repositories import (
    ActivityRepository,
    CardRepository,
    GoalRepository,
    LearnerRepository,
    MasteryRepository,
    PlanTaskRepository,
)
from ..schemas.learner import LearnerPreferences, LearnerState
from .mapping import activity_to_schema, flashcard_to_schema, goal_to_schema, mastery_to_point
from .mastery.engine import derive_weak_points


class LearnerStateService:
    def __init__(self, session) -> None:
        self.session = session
        self.learners = LearnerRepository(session)
        self.mastery = MasteryRepository(session)
        self.goals = GoalRepository(session)
        self.tasks = PlanTaskRepository(session)
        self.cards = CardRepository(session)
        self.activity = ActivityRepository(session)

    async def get_state(self, learner_id: str) -> LearnerState:
        learner = await self.learners.get(learner_id)
        if learner is None:
            raise not_found(f"learner {learner_id} not found")

        mastery_rows, goal_rows, due_cards, activity_rows = await asyncio.gather(
            self.mastery.list_by_learner(learner_id),
            self.goals.list_by_learner(learner_id),
            self.cards.list_due(learner_id, now_utc(), 50),
            self.activity.list_recent(learner_id, 8),
        )
        task_map = await self.tasks.list_for_goals([g.id for g in goal_rows])

        mastery_pts = [mastery_to_point(m) for m in mastery_rows]
        weak_rows = derive_weak_points(mastery_rows)
        weak_pts = [mastery_to_point(m) for m in weak_rows]
        overall = round(mean([m.level for m in mastery_rows]), 2) if mastery_rows else 0.0

        return LearnerState(
            learnerId=learner.id,
            name=learner.name or "同学",
            streak=learner.streak or 0,
            studyTimeTodayMin=learner.study_time_today_min or 0,
            studyTimeTotalMin=learner.study_time_total_min or 0,
            overallMastery=overall,
            weeklyChange=learner.weekly_change or 0.0,
            sessionCount=learner.session_count or 0,
            weeklyQuestionCount=learner.weekly_question_count or 0,
            goals=[goal_to_schema(g, task_map.get(g.id, [])) for g in goal_rows],
            mastery=mastery_pts,
            weakPoints=weak_pts,
            dueCards=[flashcard_to_schema(c) for c in due_cards],
            recentActivity=[activity_to_schema(a) for a in activity_rows],
            preferences=LearnerPreferences.model_validate(learner.preferences or {}),
            updatedAt=to_iso(learner.updated_at) if learner.updated_at else now_iso_or_now(),
        )

    async def update_preferences(self, learner_id: str, prefs: dict) -> LearnerState:
        learner = await self.learners.get(learner_id)
        if learner is None:
            raise not_found(f"learner {learner_id} not found")
        merged = {**(learner.preferences or {}), **{k: v for k, v in prefs.items() if v is not None}}
        learner.preferences = merged
        learner.updated_at = now_utc()
        await self.session.flush()
        return await self.get_state(learner_id)


def now_iso_or_now() -> str:
    return to_iso(now_utc())
