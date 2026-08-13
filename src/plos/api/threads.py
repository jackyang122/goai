"""Thread endpoints: get one, send message (REST), upload attachment."""

from __future__ import annotations

import os
import tempfile
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from ..app.deps import get_auth, get_providers, get_session, get_token
from ..app.errors import forbidden, not_found
from ..db.repositories import MessageRepository, ThreadRepository
from ..domain.attachments import AttachmentService
from ..domain.chat import ChatTurnOrchestrator
from ..domain.mapping import thread_to_schema
from ..providers.auth import AuthProvider
from ..providers.registry import ProviderContainer
from ..schemas.chat import ChatMessage, ChatThread, SendMessageRequest

router = APIRouter(tags=["threads"])


@router.get("/api/threads/{thread_id}", response_model=ChatThread)
async def get_thread(
    thread_id: str,
    session: AsyncSession = Depends(get_session),
    auth: AuthProvider = Depends(get_auth),
    authorization: Optional[str] = Depends(get_token),
) -> ChatThread:
    lid = await auth.resolve_learner(authorization, "")
    thread = await ThreadRepository(session).get(thread_id)
    if thread is None:
        raise not_found("thread not found")
    if thread.learner_id != lid:
        raise forbidden("thread does not belong to learner")
    msgs = await MessageRepository(session).list_by_thread(thread_id)
    return thread_to_schema(thread, msgs)


@router.post("/api/threads/{thread_id}/messages", response_model=ChatMessage)
async def send_message(
    thread_id: str,
    body: SendMessageRequest,
    session: AsyncSession = Depends(get_session),
    auth: AuthProvider = Depends(get_auth),
    providers: ProviderContainer = Depends(get_providers),
    authorization: Optional[str] = Depends(get_token),
) -> ChatMessage:
    lid = await auth.resolve_learner(authorization, body.learnerId)
    orch = ChatTurnOrchestrator(session, providers)
    return await orch.run(lid, thread_id, body.content, body.persona)


@router.post("/api/threads/{thread_id}/attachments", status_code=202, tags=["threads"])
async def upload_attachment(
    thread_id: str,
    background: BackgroundTasks,
    learner_id: str = "",
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    auth: AuthProvider = Depends(get_auth),
    providers: ProviderContainer = Depends(get_providers),
    authorization: Optional[str] = Depends(get_token),
):
    lid = await auth.resolve_learner(authorization, learner_id)
    # Persist upload to a temp file (replace with object storage in production).
    suffix = os.path.splitext(file.filename or "")[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    content = await file.read()
    tmp.write(content)
    tmp.close()

    svc = AttachmentService(session, providers)
    att = await svc.create(
        thread_id=thread_id,
        learner_id=lid,
        filename=file.filename or "upload",
        mime=file.content_type or "application/octet-stream",
        size=len(content),
        storage_path=tmp.name,
    )
    # Commit metadata now; ingest runs after the response is sent.
    await session.commit()
    background.add_task(_ingest_attachment, providers, att.id, tmp.name)
    return {"id": att.id, "status": att.status, "threadId": thread_id}


async def _ingest_attachment(providers: ProviderContainer, attachment_id: str, path: str) -> None:
    from ..db.engine import get_session_factory

    factory = get_session_factory()
    async with factory() as session:
        try:
            await AttachmentService(session, providers).ingest(attachment_id, path)
            await session.commit()
        except Exception:  # noqa: BLE001
            await session.rollback()
