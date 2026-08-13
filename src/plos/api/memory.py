"""Memory endpoints: list (filtered), write, graph."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..app.deps import get_auth, get_providers, get_session, get_token
from ..domain.memory import MemoryService
from ..providers.auth import AuthProvider
from ..providers.registry import ProviderContainer
from ..schemas.memory import MemoryGraph, MemoryItem, WriteMemoryRequest

router = APIRouter(tags=["memory"])


@router.get("/api/learners/{learner_id}/memory")
async def list_memory(
    learner_id: str,
    layer: Optional[str] = None,
    topic: Optional[str] = None,
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    auth: AuthProvider = Depends(get_auth),
    providers: ProviderContainer = Depends(get_providers),
    authorization: Optional[str] = Depends(get_token),
):
    from ._pagination import maybe_page

    lid = await auth.resolve_learner(authorization, learner_id)
    rows = await MemoryService(session, providers).list(
        lid, layer=layer, topic=topic, limit=limit or 100, cursor=cursor
    )
    return maybe_page(rows, limit, cursor)


@router.post("/api/memory", response_model=MemoryItem, status_code=201)
async def write_memory(
    body: WriteMemoryRequest,
    session: AsyncSession = Depends(get_session),
    auth: AuthProvider = Depends(get_auth),
    providers: ProviderContainer = Depends(get_providers),
    authorization: Optional[str] = Depends(get_token),
) -> MemoryItem:
    lid = await auth.resolve_learner(authorization, body.learnerId)
    body = body.model_copy(update={"learnerId": lid})
    return await MemoryService(session, providers).write(body)


@router.get("/api/learners/{learner_id}/memory/graph", response_model=MemoryGraph)
async def memory_graph(
    learner_id: str,
    session: AsyncSession = Depends(get_session),
    auth: AuthProvider = Depends(get_auth),
    providers: ProviderContainer = Depends(get_providers),
    authorization: Optional[str] = Depends(get_token),
) -> MemoryGraph:
    lid = await auth.resolve_learner(authorization, learner_id)
    return await MemoryService(session, providers).graph(lid)
