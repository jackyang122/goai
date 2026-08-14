"""Card endpoints: due list + FSRS review."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..app.deps import get_auth, get_session, get_token
from ..domain.cards import FsrsCardService
from ..providers.auth import AuthProvider
from ..schemas.card import CardReviewRequest, CardReviewResult
from ..schemas.learner import FlashCard

router = APIRouter(tags=["cards"])


@router.get("/api/learners/{learner_id}/cards", response_model=List[FlashCard])
async def list_cards(
    learner_id: str,
    due: bool = True,
    session: AsyncSession = Depends(get_session),
    auth: AuthProvider = Depends(get_auth),
    authorization: Optional[str] = Depends(get_token),
) -> List[FlashCard]:
    lid = await auth.resolve_learner(authorization, learner_id)
    return await FsrsCardService(session).list_due(lid, due_only=due)


@router.post("/api/cards/{card_id}/review", response_model=CardReviewResult)
async def review_card(
    card_id: str,
    body: CardReviewRequest,
    session: AsyncSession = Depends(get_session),
    auth: AuthProvider = Depends(get_auth),
    authorization: Optional[str] = Depends(get_token),
) -> CardReviewResult:
    lid = await auth.resolve_learner(authorization, body.learnerId)
    return await FsrsCardService(session).review(card_id, body.rating, lid)
