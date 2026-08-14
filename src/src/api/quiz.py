"""Quiz endpoints: generate + grade."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..app.deps import get_auth, get_providers, get_session, get_token
from ..domain.quiz import QuizService
from ..providers.auth import AuthProvider
from ..providers.registry import ProviderContainer
from ..schemas.quiz import GenerateQuizRequest, GradeRequest, Question, QuizResult

router = APIRouter(tags=["quiz"])


@router.post("/api/quiz/generate", response_model=List[Question])
async def generate_quiz(
    body: GenerateQuizRequest,
    session: AsyncSession = Depends(get_session),
    auth: AuthProvider = Depends(get_auth),
    providers: ProviderContainer = Depends(get_providers),
    authorization: Optional[str] = Depends(get_token),
) -> List[Question]:
    lid = await auth.resolve_learner(authorization, body.learnerId)
    return await QuizService(session, providers).generate(lid, body.topic, body.count)


@router.post("/api/quiz/grade", response_model=QuizResult)
async def grade_answer(
    body: GradeRequest,
    session: AsyncSession = Depends(get_session),
    auth: AuthProvider = Depends(get_auth),
    providers: ProviderContainer = Depends(get_providers),
    authorization: Optional[str] = Depends(get_token),
) -> QuizResult:
    lid = await auth.resolve_learner(authorization, body.learnerId)
    return await QuizService(session, providers).grade(lid, body.question, body.userAnswer)
