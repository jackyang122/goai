"""QuizService — generate questions + grade (writing mastery via MasteryEngine + errors)."""

from __future__ import annotations

from typing import List

from ..core.ids import new_id
from ..core.time import now_utc
from ..db.models.quiz import ErrorBook
from ..db.repositories import ErrorBookRepository, LearnerRepository, QuestionRepository
from ..providers.registry import ProviderContainer
from ..schemas.quiz import Question, QuizResult
from .grading import SemanticGrader
from .mastery.engine import MasteryEngine
from .mapping import question_to_schema
from ..seed.data import QUESTION_BANK


class QuizService:
    def __init__(self, session, providers: ProviderContainer) -> None:
        self.session = session
        self.providers = providers
        self.questions = QuestionRepository(session)
        self.errors = ErrorBookRepository(session)
        self.learners = LearnerRepository(session)
        self.engine = MasteryEngine(session)
        self.grader = SemanticGrader(providers)

    async def generate(self, learner_id: str, topic: str, count: int) -> List[Question]:
        rows = await self.questions.list_by_topic(topic, limit=count)
        out = [question_to_schema(r) for r in rows]
        if len(out) < count:
            for q in QUESTION_BANK.get(topic, QUESTION_BANK["二次函数"])[: count - len(out)]:
                out.append(Question(**q))
        return out[:count]

    async def grade(self, learner_id: str, question: Question, user_answer: str) -> QuizResult:
        outcome = await self.grader.grade(question, user_answer)

        # Authoritative mastery write (single-writer).
        await self.engine.apply_evidence(
            learner_id,
            question.topic,
            observed_correct=outcome.correct,
            error_count_delta=0 if outcome.correct else 1,
        )

        if not outcome.correct:
            snap = question.model_dump()
            self.session.add(
                ErrorBook(
                    id=new_id("err"),
                    learner_id=learner_id,
                    question_id=question.id,
                    question_snapshot=snap,
                    user_answer=user_answer,
                    error_type="待诊断",
                    ts=now_utc(),
                    reviewed=False,
                )
            )
        await self.learners.bump(learner_id, questions=1)
        await self.session.flush()

        return QuizResult(
            questionId=question.id,
            correct=outcome.correct,
            userAnswer=user_answer,
            topic=question.topic,
            score=round(outcome.score, 2),
            rationale=outcome.rationale or question.explanation,
        )
