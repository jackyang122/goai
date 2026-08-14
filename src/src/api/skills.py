"""Skill endpoints: list + invoke."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..app.deps import get_auth, get_session, get_token
from ..domain.learner_state import LearnerStateService
from ..domain.skills.base import SkillContext
from ..domain.skills.router import SkillRouter
from ..providers.auth import AuthProvider
from ..providers.registry import ProviderContainer
from ..app.deps import get_providers
from ..schemas.skill import SkillMeta, SkillRequest, SkillResult

router = APIRouter(tags=["skills"])
_skill_router = SkillRouter()


@router.get("/api/skills", response_model=List[SkillMeta])
async def list_skills() -> List[SkillMeta]:
    return _skill_router.list_meta()


@router.post("/api/skills/invoke", response_model=SkillResult)
async def invoke_skill(
    req: SkillRequest,
    session: AsyncSession = Depends(get_session),
    auth: AuthProvider = Depends(get_auth),
    providers: ProviderContainer = Depends(get_providers),
    authorization=Depends(get_token),
) -> SkillResult:
    lid = await auth.resolve_learner(authorization, req.learnerId)
    try:
        state = await LearnerStateService(session).get_state(lid)
    except Exception:  # noqa: BLE001
        state = None
    ctx = SkillContext(
        session=session,
        learner_id=lid,
        skill_id=req.skill,
        input=req.input or {},
        providers=providers,
        learner_state=state,
    )
    return await _skill_router.invoke(ctx)
