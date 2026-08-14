"""AttachmentService — accept an upload, store metadata, then ingest into a thread-scoped
KB as a background task (returns 202 immediately with status=indexing)."""

from __future__ import annotations

from typing import Optional

from ..core.ids import new_id
from ..core.time import now_utc
from ..db.models.chat import Attachment
from ..db.models.kb import KnowledgeBase
from ..db.repositories import AttachmentRepository, KbRepository
from ..providers.registry import ProviderContainer
from .rag import RagOrchestrator


class AttachmentService:
    def __init__(self, session, providers: ProviderContainer) -> None:
        self.session = session
        self.providers = providers
        self.attachments = AttachmentRepository(session)
        self.kbs = KbRepository(session)

    async def create(
        self,
        thread_id: str,
        learner_id: str,
        filename: str,
        mime: str,
        size: int,
        storage_path: Optional[str] = None,
    ) -> Attachment:
        row = Attachment(
            id=new_id("att"),
            thread_id=thread_id,
            learner_id=learner_id,
            filename=filename,
            mime=mime,
            size=size,
            storage_path=storage_path,
            status="indexing",
            created_at=now_utc(),
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def ingest(self, attachment_id: str, path: str) -> None:
        """Background ingest: parse + embed into a per-thread KB. Swallows parse errors."""
        att = await self.attachments.get(attachment_id)
        if att is None:
            return
        try:
            kb_id = att.kb_id or f"kb_thread_{att.thread_id}"
            if await self.kbs.get(kb_id) is None:
                self.session.add(
                    KnowledgeBase(
                        id=kb_id,
                        owner_learner_id=att.learner_id,
                        name=f"Thread {att.thread_id} attachments",
                        engine="llamaindex",
                        document_count=0,
                        status="indexing",
                        created_at=now_utc(),
                    )
                )
                await self.session.flush()
            att.kb_id = kb_id
            rag = RagOrchestrator(self.session, self.providers)
            await rag.ingest_file(kb_id, path, mime=att.mime)
            att.status = "ready"
        except Exception:  # noqa: BLE001
            att.status = "error"
        await self.session.flush()
