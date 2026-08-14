"""Mastery + BKT-parameter repositories.

SINGLE-WRITER RULE: ``mastery.level`` / ``mastery.trend`` are written only through
``MasteryRepository.commit_update``, which is invoked solely by ``MasteryEngine``. No
other code path writes these columns.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ...core.ids import new_id
from ..models.mastery import Mastery, MasteryParam
from .base import BaseRepository


class MasteryRepository(BaseRepository[Mastery]):
    model = Mastery

    async def list_by_learner(self, learner_id: str) -> List[Mastery]:
        stmt = select(Mastery).where(Mastery.learner_id == learner_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_topic(self, learner_id: str, topic: str) -> Optional[Mastery]:
        stmt = select(Mastery).where(
            Mastery.learner_id == learner_id, Mastery.topic == topic
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def lock_for_topic(self, learner_id: str, topic: str) -> Optional[Mastery]:
        """``SELECT … FOR UPDATE`` so concurrent evidence for the same topic serializes."""
        stmt = (
            select(Mastery)
            .where(Mastery.learner_id == learner_id, Mastery.topic == topic)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def commit_update(
        self,
        learner_id: str,
        topic: str,
        *,
        subject: str = "",
        level: Optional[float] = None,
        trend: Optional[str] = None,
        error_count_delta: int = 0,
        last_practiced_at: Optional[datetime] = None,
    ) -> Mastery:
        """The single write path for mastery. Upserts one (learner, topic) row.

        Callers MUST hold the row lock obtained via :meth:`lock_for_topic` when updating
        an existing row (the engine acquires locks in sorted-topic order to avoid
        deadlocks).
        """
        existing = await self.get_for_topic(learner_id, topic)
        if existing is None:
            row = Mastery(
                id=new_id("m"),
                learner_id=learner_id,
                topic=topic,
                subject=subject,
                level=level if level is not None else 0.0,
                trend=trend or "flat",
                error_count=max(0, error_count_delta),
                last_practiced_at=last_practiced_at,
            )
            self.session.add(row)
            await self.session.flush()
            return row
        if level is not None:
            existing.level = level
        if trend is not None:
            existing.trend = trend
        if subject:
            existing.subject = subject
        if error_count_delta:
            existing.error_count = max(0, existing.error_count + error_count_delta)
        if last_practiced_at is not None:
            existing.last_practiced_at = last_practiced_at
        await self.session.flush()
        return existing


class MasteryParamRepository(BaseRepository[MasteryParam]):
    model = MasteryParam

    async def get_for_topic(self, learner_id: str, topic: str) -> MasteryParam:
        stmt = select(MasteryParam).where(
            MasteryParam.learner_id == learner_id, MasteryParam.topic == topic
        )
        result = await self.session.execute(stmt)
        row = result.scalars().first()
        if row is not None:
            return row
        # Idempotent insert; defaults come from the model.
        stmt_i = (
            pg_insert(MasteryParam)
            .values(id=new_id("mp"), learner_id=learner_id, topic=topic)
            .on_conflict_do_nothing(index_elements=["learner_id", "topic"])
            .returning(MasteryParam)
        )
        result_i = await self.session.execute(stmt_i)
        row = result_i.scalars().first()
        if row is None:
            row = (await self.session.execute(stmt)).scalars().first()
        assert row is not None
        return row

    async def set_params(
        self, learner_id: str, topic: str, **params: float
    ) -> MasteryParam:
        row = await self.get_for_topic(learner_id, topic)
        for key in ("l0", "t_transit", "slip", "guess"):
            if key in params:
                setattr(row, key, float(params[key]))
        await self.session.flush()
        return row
