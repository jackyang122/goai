"""MasteryEngine — the single writer of ``mastery`` / ``weakPoints``.

It is the only component that calls ``MasteryRepository.commit_update``. Evidence (quiz
grades, FSRS reviews, diagnosis confirmations, skill side-effects) flows in here as BKT
observations; derived fields (overallMastery, weakPoints) are computed at read time by
``LearnerStateService`` so they are never stale.
"""

from __future__ import annotations

from typing import List, Optional

from ...core.config import settings
from ...core.time import now_utc
from ...db.repositories import MasteryParamRepository, MasteryRepository
from .bkt import BktParams, forward, soft_forward, trend


class MasteryEngine:
    def __init__(self, session) -> None:
        self.session = session
        self.mastery = MasteryRepository(session)
        self.params = MasteryParamRepository(session)

    async def apply_evidence(
        self,
        learner_id: str,
        topic: str,
        observed_correct: bool,
        *,
        weight: float = 1.0,
        subject: str = "",
        error_count_delta: int = 0,
    ):
        """One BKT observation for a single topic (hard evidence when weight==1)."""
        params = await self.params.get_for_topic(learner_id, topic)
        p = BktParams(params.l0, params.t_transit, params.slip, params.guess)

        row = await self.mastery.lock_for_topic(learner_id, topic)  # SELECT … FOR UPDATE
        prev = row.level if row is not None else params.l0

        new = forward(prev, observed_correct, p) if weight >= 1.0 else soft_forward(prev, observed_correct, p, weight)
        new_trend = trend(prev, new)

        return await self.mastery.commit_update(
            learner_id,
            topic,
            subject=subject,
            level=new,
            trend=new_trend,
            error_count_delta=error_count_delta,
            last_practiced_at=now_utc(),
        )

    async def apply_soft_evidence(
        self, learner_id: str, topic: str, observed_correct: bool, *, weight: float = 0.3, subject: str = ""
    ):
        return await self.apply_evidence(
            learner_id, topic, observed_correct, weight=weight, subject=subject
        )

    async def apply_many(
        self,
        learner_id: str,
        observations: List[tuple],
    ) -> None:
        """Apply several (topic, observed_correct, weight) tuples, locking in sorted order."""
        for topic, observed, weight in sorted(observations, key=lambda x: x[0]):
            await self.apply_evidence(learner_id, topic, observed, weight=weight)

    async def recompute_trends(self, learner_id: str) -> int:
        """Offline maintenance: re-derive trend from stored level vs params prior.

        Real BKT re-fit (``pybkt.fit``) is invoked by the CLI on a snapshot; the serving
        path only refreshes derived labels here.
        """
        rows = await self.mastery.list_by_learner(learner_id)
        for row in rows:
            params = await self.params.get_for_topic(learner_id, row.topic)
            row.trend = trend(params.l0, row.level)
        return len(rows)

    async def overall_mastery(self, learner_id: str) -> float:
        rows = await self.mastery.list_by_learner(learner_id)
        if not rows:
            return 0.0
        return round(sum(r.level for r in rows) / len(rows), 2)


def derive_weak_points(rows) -> List:
    """Pure helper shared with LearnerStateService: level < threshold, ascending."""
    threshold = settings.weak_threshold
    return sorted([r for r in rows if r.level < threshold], key=lambda r: r.level)
