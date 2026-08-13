"""RagOrchestrator — embed query → pgvector search over KB chunks → Citations.

pgvector IS the vector store for both the stub and real embedding paths; the LlamaIndex
path can be layered on later as an alternate ingestion/indexing engine. Ingestion chunks
text and writes embedded ``KbDocument`` rows.
"""

from __future__ import annotations

from typing import List, Optional

from ..core.ids import new_id
from ..core.time import now_utc
from ..db.models.kb import KbDocument
from ..db.repositories import KbDocumentRepository, KbRepository
from ..providers.parser import chunk_markdown
from ..providers.registry import ProviderContainer
from ..schemas.skill import Citation


class RagOrchestrator:
    def __init__(self, session, providers: ProviderContainer) -> None:
        self.session = session
        self.providers = providers
        self.docs = KbDocumentRepository(session)
        self.kbs = KbRepository(session)

    async def retrieve(
        self, query: str, kb_ids: List[str], *, top_k: int = 4
    ) -> List[Citation]:
        if not query.strip() or not kb_ids:
            return []
        emb = await self.providers.embedding.embed_one(query)
        citations: List[Citation] = []
        for kb_id in kb_ids:
            kb = await self.kbs.get(kb_id)
            kb_name = kb.name if kb else kb_id
            rows = await self.docs.search(kb_id, emb, top_k=top_k)
            for d in rows:
                locator = f" {d.locator}" if d.locator else ""
                citations.append(
                    Citation(
                        id=new_id("c"),
                        source=f"{kb_name} · {d.title}{locator}",
                        snippet=d.content[:240],
                        locator=d.locator,
                    )
                )
        return citations

    async def ingest_text(
        self, kb_id: str, title: str, text: str, *, chunk_size: int = 800
    ) -> int:
        chunks = chunk_markdown(text, target_chars=chunk_size)
        vectors = await self.providers.embedding.embed(chunks) if chunks else []
        rows = [
            KbDocument(
                id=new_id("kd"),
                kb_id=kb_id,
                title=title,
                chunk_index=i,
                embedding=vec,
                content=chunk,
                created_at=now_utc(),
            )
            for i, (chunk, vec) in enumerate(zip(chunks, vectors))
        ]
        await self.docs.add_chunks(rows)
        await self.kbs.increment_doc_count(kb_id, delta=len(rows))
        return len(rows)

    async def ingest_file(
        self, kb_id: str, path: str, mime: Optional[str] = None
    ) -> int:
        parsed = self.providers.parser.parse(path, mime=mime)
        return await self.ingest_text(kb_id, parsed.title or path, parsed.markdown)
