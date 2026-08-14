"""Thread + message + attachment repositories."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select

from ..models.chat import Attachment, Message, Thread
from .base import BaseRepository


class ThreadRepository(BaseRepository[Thread]):
    model = Thread

    async def list_by_learner(self, learner_id: str) -> List[Thread]:
        stmt = (
            select(Thread)
            .where(Thread.learner_id == learner_id)
            .order_by(Thread.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, id_: str) -> Optional[Thread]:
        return await self.session.get(Thread, id_)

    async def touch(self, id_: str, *, title: Optional[str] = None) -> None:
        thread = await self.get(id_)
        if thread is None:
            return
        from ...core.time import now_utc

        thread.updated_at = now_utc()
        if title:
            thread.title = title


class MessageRepository(BaseRepository[Message]):
    model = Message

    async def list_by_thread(self, thread_id: str) -> List[Message]:
        stmt = (
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.seq.asc(), Message.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, obj: Message) -> Message:  # type: ignore[override]
        # Assign an increasing seq within the thread for stable ordering.
        from sqlalchemy import func

        stmt = select(func.coalesce(func.max(Message.seq), -1)).where(Message.thread_id == obj.thread_id)
        result = await self.session.execute(stmt)
        obj.seq = int(result.scalar_one()) + 1
        return await super().add(obj)


class AttachmentRepository(BaseRepository[Attachment]):
    model = Attachment

    async def list_by_thread(self, thread_id: str) -> List[Attachment]:
        stmt = (
            select(Attachment)
            .where(Attachment.thread_id == thread_id)
            .order_by(Attachment.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
