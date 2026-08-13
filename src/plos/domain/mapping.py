"""ORM → schema mappers (pure functions). One place to adjust wire-format details."""

from __future__ import annotations

from typing import List, Optional

from ..core.time import to_iso
from ..db.models.cards import FlashCard
from ..db.models.chat import Message, Thread
from ..db.models.goals import Goal as GoalRow
from ..db.models.goals import PlanTask as PlanTaskRow
from ..db.models.kb import KnowledgeBase as KbRow
from ..db.models.learners import Activity
from ..db.models.mastery import Mastery
from ..db.models.memory import Memory, MemoryEdge
from ..db.models.quiz import ErrorBook, Question
from ..schemas.chat import ChatMessage, ChatThread
from ..schemas.common import PersonaId
from ..schemas.kb import KnowledgeBase
from ..schemas.learner import Activity as ActivitySchema
from ..schemas.learner import FlashCard as FlashCardSchema
from ..schemas.learner import Goal, MasteryPoint, PlanTask, PlanTaskRef
from ..schemas.memory import MemoryEdge as MemoryEdgeSchema
from ..schemas.memory import MemoryItem
from ..schemas.quiz import ErrorBookItem, Question as QuestionSchema


def _opt_iso(dt) -> Optional[str]:
    return to_iso(dt) if dt is not None else None


def mastery_to_point(row: Mastery) -> MasteryPoint:
    return MasteryPoint(
        id=row.id,
        topic=row.topic,
        subject=row.subject or "",
        level=round(row.level, 2),
        trend=row.trend or "flat",
        lastPracticedAt=_opt_iso(row.last_practiced_at),
        errorCount=row.error_count or 0,
    )


def plantask_to_schema(row: PlanTaskRow) -> PlanTask:
    ref = None
    if row.ref:
        try:
            ref = PlanTaskRef(**row.ref)
        except Exception:  # noqa: BLE001
            ref = None
    return PlanTask(
        id=row.id,
        title=row.title,
        estMinutes=row.est_minutes or 0,
        type=row.type or "learn",
        done=bool(row.done),
        ref=ref,
    )


def goal_to_schema(row: GoalRow, tasks: List[PlanTaskRow]) -> Goal:
    return Goal(
        id=row.id,
        title=row.title,
        subject=row.subject or "",
        progress=round(row.progress or 0.0, 2),
        deadline=row.deadline.isoformat() if row.deadline else None,
        source=row.source or "learning-plan",
        tasks=[plantask_to_schema(t) for t in tasks],
    )


def flashcard_to_schema(row: FlashCard) -> FlashCardSchema:
    return FlashCardSchema(
        id=row.id,
        front=row.front,
        back=row.back,
        topic=row.topic,
        due=to_iso(row.due),
    )


def activity_to_schema(row: Activity) -> ActivitySchema:
    return ActivitySchema(id=row.id, type=row.type, label=row.label, ts=to_iso(row.ts))


def question_to_schema(row: Question) -> QuestionSchema:
    return QuestionSchema(
        id=row.id,
        type=row.type,
        prompt=row.prompt,
        options=row.options,
        answer=row.answer,
        explanation=row.explanation or "",
        topic=row.topic,
        skill=row.skill,
    )


def question_from_dict(d: dict) -> QuestionSchema:
    return QuestionSchema(**d)


def errorbook_to_schema(row: ErrorBook) -> ErrorBookItem:
    q = row.question_snapshot or {}
    return ErrorBookItem(
        id=row.id,
        question=QuestionSchema(**q) if isinstance(q, dict) else question_to_schema(q),
        userAnswer=row.user_answer,
        errorType=row.error_type or "待诊断",
        ts=to_iso(row.ts),
        reviewed=bool(row.reviewed),
    )


def memory_to_schema(row: Memory) -> MemoryItem:
    return MemoryItem(
        id=row.id,
        layer=row.layer,
        content=row.content,
        source=row.source or "",
        createdAt=to_iso(row.created_at),
        topic=row.topic,
        confidence=row.confidence,
    )


def memory_edge_to_schema(row: MemoryEdge) -> MemoryEdgeSchema:
    return MemoryEdgeSchema(
        id=row.id,
        src=row.src_memory_id,
        dst=row.dst_memory_id,
        relation=row.relation,
        weight=row.weight,
    )


def message_to_schema(row: Message) -> ChatMessage:
    from ..schemas.chat import ChatPayload  # local import to avoid cycles

    payload = None
    if row.payload:
        try:
            payload = ChatPayload.model_validate(row.payload)
        except Exception:  # noqa: BLE001
            payload = None
    citations = row.citations or []
    return ChatMessage(
        id=row.id,
        role=row.role,
        content=row.content or "",
        createdAt=to_iso(row.created_at),
        citations=citations,
        skill=row.skill,
        status=row.status or "complete",
        payload=payload,
    )


def thread_to_schema(row: Thread, messages: List[Message]) -> ChatThread:
    return ChatThread(
        id=row.id,
        title=row.title or "",
        persona=row.persona or "teacher",  # type: ignore[arg-type]
        messages=[message_to_schema(m) for m in messages],
        createdAt=to_iso(row.created_at),
        updatedAt=to_iso(row.updated_at),
    )


def kb_to_schema(row: KbRow) -> KnowledgeBase:
    return KnowledgeBase(
        id=row.id,
        name=row.name,
        engine=row.engine,  # type: ignore[arg-type]
        documentCount=row.document_count or 0,
        status=row.status,  # type: ignore[arg-type]
        createdAt=to_iso(row.created_at),
    )
