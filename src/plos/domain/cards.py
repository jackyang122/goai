"""FsrsCardService — due-card listing + FSRS review (with soft mastery evidence).

Uses py-fsrs when installed; otherwise a simple interval scheduler so the feature works
dependency-free. A review also feeds a *soft* BKT observation to the MasteryEngine
(correct recall nudges the topic up, lapse nudges it down)."""

from __future__ import annotations

from datetime import timedelta
from typing import List, Optional

from ..core.time import now_utc
from ..db.models.cards import FlashCard
from ..db.repositories import CardRepository
from ..schemas.card import CardReviewResult
from ..schemas.learner import FlashCard as FlashCardSchema
from .mapping import flashcard_to_schema
from .mastery.engine import MasteryEngine

# Fallback intervals (days) by rating 1..4 when py-fsrs is unavailable.
_FALLBACK_DAYS = {1: 0, 2: 1, 3: 3, 4: 7}


class FsrsCardService:
    def __init__(self, session) -> None:
        self.session = session
        self.cards = CardRepository(session)
        self.engine = MasteryEngine(session)

    async def list_due(self, learner_id: str, *, due_only: bool = True, limit: int = 50) -> List[FlashCardSchema]:
        rows = (
            await self.cards.list_due(learner_id, now_utc(), limit)
            if due_only
            else await self.cards.list_by_learner(learner_id, limit)
        )
        return [flashcard_to_schema(r) for r in rows]

    async def review(self, card_id: str, rating: int, learner_id: str) -> CardReviewResult:
        card = await self.cards.get(card_id)
        if card is None:
            from ..app.errors import not_found

            raise not_found(f"card {card_id} not found")

        new_due = self._schedule(card, rating)
        card.due = new_due
        card.last_review = now_utc()
        card.reps += 1
        if rating == 1:
            card.lapses += 1
        await self.session.flush()

        # Soft mastery evidence: good/easy = recall, again/hard = lapse.
        await self.engine.apply_soft_evidence(
            learner_id, card.topic, observed_correct=rating >= 3, weight=0.25 + 0.15 * (rating - 1)
        )

        return CardReviewResult(
            card=flashcard_to_schema(card),
            nextDue=new_due.isoformat().replace("+00:00", "Z"),
            reps=card.reps,
            lapses=card.lapses,
        )

    def _schedule(self, card: FlashCard, rating: int):
        try:
            return self._fsrs_schedule(card, rating)
        except Exception:  # noqa: BLE001 — degrade to the simple scheduler
            return self._fallback_schedule(card, rating)

    def _fsrs_schedule(self, card: FlashCard, rating: int):
        from fsrs import Card, Rating, Scheduler  # type: ignore

        mapping = {1: Rating.AGAIN, 2: Rating.HARD, 3: Rating.GOOD, 4: Rating.EASY}
        fc = Card()
        fc.stability = card.stability or 0.0
        fc.difficulty = card.difficulty or 0.0
        fc.reps = card.reps
        fc.lapses = card.lapses
        fc.state = card.state
        if card.last_review is not None:
            fc.last_review = card.last_review
        sched = Scheduler()
        _, updated = sched.review(fc, mapping[rating])
        card.stability = float(updated.stability or 0.0)
        card.difficulty = float(updated.difficulty or 0.0)
        card.state = int(getattr(updated, "state", 0))
        return getattr(updated, "due", now_utc() + timedelta(days=_FALLBACK_DAYS[rating]))

    def _fallback_schedule(self, card: FlashCard, rating: int):
        days = _FALLBACK_DAYS[rating] + card.reps
        return now_utc() + timedelta(days=max(0, days))
