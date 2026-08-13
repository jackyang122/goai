"""Knowledge-base endpoints: list, create, upload document, search (RAG)."""

from __future__ import annotations

import os
import tempfile
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from ..app.deps import get_auth, get_providers, get_session, get_token
from ..app.errors import not_implemented
from ..core.config import settings
from ..core.ids import new_id
from ..core.time import now_utc
from ..db.models.kb import KnowledgeBase
from ..db.repositories import KbRepository
from ..domain.mapping import kb_to_schema
from ..domain.rag import RagOrchestrator
from ..providers.auth import AuthProvider
from ..providers.registry import ProviderContainer
from ..schemas.kb import CreateKbRequest, KnowledgeBase, SearchKbRequest
from ..schemas.skill import Citation

router = APIRouter(tags=["kbs"])


@router.get("/api/kbs", response_model=List[KnowledgeBase])
async def list_kbs(
    session: AsyncSession = Depends(get_session),
    auth: AuthProvider = Depends(get_auth),
    authorization: Optional[str] = Depends(get_token),
) -> List[KnowledgeBase]:
    lid = await auth.resolve_learner(authorization, "")
    rows = await KbRepository(session).list_all(lid)
    return [kb_to_schema(r) for r in rows]


@router.post("/api/kbs", response_model=KnowledgeBase, status_code=201)
async def create_kb(
    body: CreateKbRequest,
    session: AsyncSession = Depends(get_session),
    auth: AuthProvider = Depends(get_auth),
    authorization: Optional[str] = Depends(get_token),
) -> KnowledgeBase:
    lid = await auth.resolve_learner(authorization, body.ownerLearnerId or "")
    row = KnowledgeBase(
        id=new_id("kb"),
        owner_learner_id=lid,
        name=body.name,
        engine=body.engine,
        document_count=0,
        status="ready",
        created_at=now_utc(),
    )
    session.add(row)
    await session.flush()
    return kb_to_schema(row)


@router.post("/api/kbs/{kb_id}/documents", status_code=202, tags=["kbs"])
async def upload_document(
    kb_id: str,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    auth: AuthProvider = Depends(get_auth),
    providers: ProviderContainer = Depends(get_providers),
    authorization: Optional[str] = Depends(get_token),
):
    await auth.resolve_learner(authorization, "")
    suffix = os.path.splitext(file.filename or "")[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    content = await file.read()
    tmp.write(content)
    tmp.close()
    background.add_task(_ingest_doc, providers, kb_id, tmp.name, file.filename or "doc")
    return {"kbId": kb_id, "status": "indexing", "filename": file.filename}


@router.post("/api/kbs/{kb_id}/search", response_model=List[Citation])
async def search_kb(
    kb_id: str,
    body: SearchKbRequest,
    session: AsyncSession = Depends(get_session),
    auth: AuthProvider = Depends(get_auth),
    providers: ProviderContainer = Depends(get_providers),
    authorization: Optional[str] = Depends(get_token),
) -> List[Citation]:
    await auth.resolve_learner(authorization, "")
    # Only the llamaindex/pgvector path is implemented here; other engines 501.
    kb = await KbRepository(session).get(kb_id)
    if kb and kb.engine not in ("llamaindex", "pageindex"):
        raise not_implemented(f"engine '{kb.engine}' retrieval not implemented; use llamaindex")
    return await RagOrchestrator(session, providers).retrieve(body.query, [kb_id], top_k=body.topK)


async def _ingest_doc(providers: ProviderContainer, kb_id: str, path: str, title: str) -> None:
    from ..db.engine import get_session_factory

    factory = get_session_factory()
    async with factory() as session:
        try:
            await RagOrchestrator(session, providers).ingest_file(kb_id, path)
            await session.commit()
        except Exception:  # noqa: BLE001
            await session.rollback()
