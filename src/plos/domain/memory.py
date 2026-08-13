"""MemoryService — three-layer memory + retrieval injection.

L1 traces are written synchronously (same transaction, never lost). L2 facts are
extracted/deduped via the memory provider (mem0 or heuristic) and mirrored into the
``memory`` table with derived_from edges. L3 is an LLM synthesis run at session end.
Retrieval returns ``Citation`` rows so the frontend renders memory hits exactly like KB
hits (zero frontend change).
"""

from __future__ import annotations

from typing import List, Optional

from ..core.ids import new_id
from ..core.time import now_utc
from ..db.models.memory import Memory, MemoryEdge
from ..db.repositories import MemoryEdgeRepository, MemoryRepository
from ..providers.registry import ProviderContainer
from ..schemas.common import MemoryLayer
from ..schemas.skill import Citation
from ..schemas.memory import MemoryGraph, MemoryItem, WriteMemoryRequest
from .mapping import memory_edge_to_schema, memory_to_schema


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


class MemoryService:
    def __init__(self, session, providers: ProviderContainer) -> None:
        self.session = session
        self.providers = providers
        self.memories = MemoryRepository(session)
        self.edges = MemoryEdgeRepository(session)

    # ── L1 ──────────────────────────────────────────────────────────────────
    async def write_l1(
        self, learner_id: str, content: str, source: str, topic: Optional[str] = None
    ) -> Memory:
        row = Memory(
            id=new_id("mem"),
            learner_id=learner_id,
            layer="L1",
            content=content,
            source=source,
            topic=topic,
            confidence=1.0,
            created_at=now_utc(),
        )
        self.session.add(row)
        await self.session.flush()
        return row

    # ── L2 ──────────────────────────────────────────────────────────────────
    async def extract_and_store_l2(
        self, learner_id: str, text: str, source: str, *, evidence_ids: Optional[List[str]] = None
    ) -> List[Memory]:
        candidates = await self.providers.memory.extract(text, source)
        existing_l2 = await self.memories.list(learner_id, layer="L2", limit=200)
        existing_norm = {_norm(m.content) for m in existing_l2}

        emb = await self.providers.embedding.embed([c.content for c in candidates]) if candidates else []
        created: List[Memory] = []
        for cand, vec in zip(candidates, emb):
            if _norm(cand.content) in existing_norm:
                continue
            row = Memory(
                id=new_id("mem"),
                learner_id=learner_id,
                layer="L2",
                content=cand.content,
                source=f"synthesis:{source}",
                topic=cand.topic,
                confidence=cand.confidence,
                evidence={"derived_from": evidence_ids or [], "raw_source": source},
                embedding=vec,
                created_at=now_utc(),
            )
            self.session.add(row)
            await self.session.flush()
            created.append(row)
            existing_norm.add(_norm(cand.content))
            # Link to evidence only when a real L1 id is available.
            target = (evidence_ids or [None])[0]
            if target:
                self.session.add(
                    MemoryEdge(
                        id=new_id("medge"),
                        learner_id=learner_id,
                        src_memory_id=row.id,
                        dst_memory_id=target,
                        relation="derived_from",
                        weight=1.0,
                        created_at=now_utc(),
                    )
                )
        return created

    # ── L3 ──────────────────────────────────────────────────────────────────
    async def synthesize_l3(self, learner_id: str, source: str = "synthesis:cross-surface") -> Optional[Memory]:
        facts = await self.memories.list(learner_id, layer="L2", limit=50)
        if not facts:
            return None
        corpus = "\n".join(f"- {m.content}" for m in facts)
        if self.providers.llm.is_stub:
            content = "整体策略：先补「符号与正负号」类薄弱点，再推进函数综合应用。"
        else:
            msgs = [{"role": "user", "content": f"基于以下学生事实，用一句话提炼跨会话的学习策略：\n{corpus}"}]
            content = await self.providers.llm.complete(msgs, max_tokens=160)
        row = Memory(
            id=new_id("mem"),
            learner_id=learner_id,
            layer="L3",
            content=content,
            source=source,
            confidence=0.9,
            created_at=now_utc(),
        )
        self.session.add(row)
        await self.session.flush()
        return row

    # ── read / graph / retrieve ─────────────────────────────────────────────
    async def list(
        self,
        learner_id: str,
        *,
        layer: Optional[MemoryLayer] = None,
        topic: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> List[MemoryItem]:
        rows = await self.memories.list(
            learner_id, layer=layer, topic=topic, limit=limit, cursor=cursor
        )
        return [memory_to_schema(m) for m in rows]

    async def graph(self, learner_id: str) -> MemoryGraph:
        rows = await self.memories.list(learner_id, limit=500)
        edges = await self.edges.list_by_learner(learner_id)
        return MemoryGraph(
            nodes=[memory_to_schema(m) for m in rows],
            edges=[memory_edge_to_schema(e) for e in edges],
        )

    async def write(self, req: WriteMemoryRequest) -> MemoryItem:
        vec = await self.providers.embedding.embed_one(req.content)
        row = Memory(
            id=new_id("mem"),
            learner_id=req.learnerId,
            layer=req.layer,
            content=req.content,
            source=req.source,
            topic=req.topic,
            confidence=req.confidence,
            embedding=vec,
            created_at=now_utc(),
        )
        self.session.add(row)
        await self.session.flush()
        return memory_to_schema(row)

    async def retrieve_citations(
        self, learner_id: str, query: str, *, k: int = 4
    ) -> List[Citation]:
        """Top relevant memories as Citations (memory + DB embedding search merged)."""
        hits: List[Memory] = []
        if query.strip():
            emb = await self.providers.embedding.embed_one(query)
            hits = await self.memories.search_by_embedding(learner_id, emb, limit=k)
        out: List[Citation] = []
        seen = set()
        for m in hits:
            key = m.content
            if key in seen:
                continue
            seen.add(key)
            out.append(
                Citation(
                    id=new_id("c"),
                    source=f"Memory {m.layer} · {m.source}",
                    snippet=m.content,
                )
            )
        return out
