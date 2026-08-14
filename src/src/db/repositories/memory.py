"""Memory + memory-edge repositories (three-layer memory + graph)."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select

from ..models.memory import Memory, MemoryEdge
from .base import BaseRepository


class MemoryRepository(BaseRepository[Memory]):
    model = Memory

    async def list(
        self,
        learner_id: str,
        *,
        layer: Optional[str] = None,
        topic: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> List[Memory]:
        stmt = select(Memory).where(Memory.learner_id == learner_id)
        if layer:
            stmt = stmt.where(Memory.layer == layer)
        if topic:
            stmt = stmt.where(Memory.topic == topic)
        stmt = stmt.order_by(Memory.created_at.desc(), Memory.id.desc())
        if cursor:
            stmt = stmt.where(Memory.id < cursor)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_embedding(
        self, learner_id: str, embedding: List[float], *, limit: int = 5
    ) -> List[Memory]:
        if not embedding:
            return []
        stmt = (
            select(Memory)
            .where(Memory.learner_id == learner_id, Memory.embedding.isnot(None))
            .order_by(Memory.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class MemoryEdgeRepository(BaseRepository[MemoryEdge]):
    model = MemoryEdge

    async def list_by_learner(self, learner_id: str) -> List[MemoryEdge]:
        stmt = select(MemoryEdge).where(MemoryEdge.learner_id == learner_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
