"""Learner endpoints: state, preferences, threads, errors."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..app.deps import get_auth, get_session, get_token
from ..db.repositories import ErrorBookRepository, MessageRepository, ThreadRepository
from ..domain.learner_state import LearnerStateService
from ..domain.mapping import errorbook_to_schema, thread_to_schema
from ..providers.auth import AuthProvider
from ..schemas.learner import LearnerState, UpdatePreferencesRequest
from ..schemas.chat import ChatThread
from ..schemas.quiz import ErrorBookItem

router = APIRouter(tags=["learners"])


@router.get("/api/learners/{learner_id}/state", response_model=LearnerState)
async def get_state(
    learner_id: str,
    session: AsyncSession = Depends(get_session),
    auth: AuthProvider = Depends(get_auth),
    authorization: Optional[str] = Depends(get_token),
) -> LearnerState:
    lid = await auth.resolve_learner(authorization, learner_id)
    return await LearnerStateService(session).get_state(lid)


@router.patch("/api/learners/{learner_id}/preferences", response_model=LearnerState)
async def update_preferences(
    learner_id: str,
    prefs: UpdatePreferencesRequest,
    session: AsyncSession = Depends(get_session),
    auth: AuthProvider = Depends(get_auth),
    authorization: Optional[str] = Depends(get_token),
) -> LearnerState:
    lid = await auth.resolve_learner(authorization, learner_id)
    svc = LearnerStateService(session)
    return await svc.update_preferences(lid, prefs.model_dump(exclude_none=True))


@router.get("/api/learners/{learner_id}/threads", response_model=List[ChatThread])
async def list_threads(
    learner_id: str,
    session: AsyncSession = Depends(get_session),
    auth: AuthProvider = Depends(get_auth),
    authorization: Optional[str] = Depends(get_token),
) -> List[ChatThread]:
    lid = await auth.resolve_learner(authorization, learner_id)
    threads = await ThreadRepository(session).list_by_learner(lid)
    msg_repo = MessageRepository(session)
    out: List[ChatThread] = []
    for t in threads:
        msgs = await msg_repo.list_by_thread(t.id)
        out.append(thread_to_schema(t, msgs))
    return out


@router.get("/api/learners/{learner_id}/errors", response_model=List[ErrorBookItem])
async def list_errors(
    learner_id: str,
    session: AsyncSession = Depends(get_session),
    auth: AuthProvider = Depends(get_auth),
    authorization: Optional[str] = Depends(get_token),
) -> List[ErrorBookItem]:
    lid = await auth.resolve_learner(authorization, learner_id)
    rows = await ErrorBookRepository(session).list_by_learner(lid)
    return [errorbook_to_schema(r) for r in rows]
