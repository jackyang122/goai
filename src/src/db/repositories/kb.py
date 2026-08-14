"""Knowledge-base + document repositories (pgvector search)."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, select

from ..models.kb import KbDocument, KnowledgeBase
from .base import BaseRepository


class KbRepository(BaseRepository[KnowledgeBase]):
    model = KnowledgeBase

    async def list_all(self, owner_id: Optional[str] = None) -> List[KnowledgeBase]:
        stmt = select(KnowledgeBase).order_by(KnowledgeBase.created_at.desc())
        if owner_id is not None:
            stmt = stmt.where(
                (KnowledgeBase.owner_learner_id == owner_id)
                | (KnowledgeBase.owner_learner_id.is_(None))
            )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, id_: str) -> Optional[KnowledgeBase]:
        return await self.session.get(KnowledgeBase, id_)

    async def increment_doc_count(self, kb_id: str, delta: int = 1) -> None:
        kb = await self.get(kb_id)
        if kb is not None:
            kb.document_count = max(0, kb.document_count + delta)
            kb.status = "ready"


class KbDocumentRepository(BaseRepository[KbDocument]):
    model = KbDocument

    async def search(
        self, kb_id: str, embedding: List[float], *, top_k: int = 4
    ) -> List[KbDocument]:
        if not embedding:
            return []
        stmt = (
            select(KbDocument)
            .where(KbDocument.kb_id == kb_id, KbDocument.embedding.isnot(None))
            .order_by(KbDocument.embedding.cosine_distance(embedding))
            .limit(top_k)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_chunks(self, chunks: List[KbDocument]) -> List[KbDocument]:
        self.session.add_all(chunks)
        await self.session.flush()
        return chunks

    async def count_by_kb(self, kb_id: str) -> int:
        stmt = select(func.count()).select_from(KbDocument).where(KbDocument.kb_id == kb_id)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())
