"""Idempotent seeder — mirrors ``web/lib/api/seed.ts`` into the live DB.

Safe to run repeatedly: each row is inserted only if its id is absent. Embeddings for KB
chunks and memory items are produced via the configured embedding provider so vector
retrieval works immediately (stub embeddings are deterministic and fine for a demo)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import get_logger
from ..core.time import now_utc
from ..db.models.cards import FlashCard
from ..db.models.chat import Message, Thread
from ..db.models.goals import Goal, PlanTask
from ..db.models.kb import KbDocument, KnowledgeBase
from ..db.models.learners import Activity, Learner
from ..db.models.mastery import Mastery, MasteryParam
from ..db.models.memory import Memory
from ..db.models.quiz import ErrorBook, Question
from . import data as D

log = get_logger(__name__)


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


async def _exists(session: AsyncSession, model, id_: str) -> bool:
    res = await session.execute(select(model.id).where(model.id == id_))
    return res.first() is not None


async def run(session: AsyncSession, providers) -> int:
    """Seed all demo data. Returns the number of rows inserted this run."""
    inserted = 0

    async def ensure(model, row):
        nonlocal inserted
        if not await _exists(session, model, row.id):
            session.add(row)
            inserted += 1

    # ── Learner ─────────────────────────────────────────────────────────────
    learner = Learner(
        id=D.LEARNER["id"],
        name=D.LEARNER["name"],
        streak=D.LEARNER["streak"],
        study_time_today_min=D.LEARNER["study_time_today_min"],
        study_time_today_date=date(2026, 8, 9),
        study_time_total_min=D.LEARNER["study_time_total_min"],
        weekly_change=D.LEARNER["weekly_change"],
        session_count=D.LEARNER["session_count"],
        weekly_question_count=D.LEARNER["weekly_question_count"],
        preferences=D.LEARNER["preferences"],
        updated_at=now_utc(),
    )
    await ensure(Learner, learner)

    # ── Mastery + params ────────────────────────────────────────────────────
    for m in D.MASTERY:
        row = Mastery(
            id=m["id"], learner_id=D.LEARNER_ID, topic=m["topic"], subject=m["subject"],
            level=m["level"], trend=m["trend"], error_count=m["error_count"],
            last_practiced_at=_dt(m["last_practiced_at"]),
        )
        await ensure(Mastery, row)
        params = D.MASTERY_PARAMS.get(m["topic"], D.MASTERY_PARAMS["default"])
        prow = MasteryParam(
            id=f"mp_{m['topic']}", learner_id=D.LEARNER_ID, topic=m["topic"],
            l0=params["l0"], t_transit=params["t_transit"], slip=params["slip"], guess=params["guess"],
            updated_at=now_utc(),
        )
        await ensure(MasteryParam, prow)

    # ── Goal + tasks ────────────────────────────────────────────────────────
    goal = Goal(
        id=D.GOAL["id"], learner_id=D.LEARNER_ID, title=D.GOAL["title"], subject=D.GOAL["subject"],
        progress=D.GOAL["progress"], deadline=datetime.strptime(D.GOAL["deadline"], "%Y-%m-%d").date(),
        source=D.GOAL["source"], created_at=now_utc(),
    )
    await ensure(Goal, goal)
    for t in D.PLAN_TASKS:
        row = PlanTask(
            id=t["id"], goal_id=D.GOAL["id"], title=t["title"], est_minutes=t["est_minutes"],
            type=t["type"], done=t["done"], ref=t.get("ref"), ordering=t.get("ordering", 0),
        )
        await ensure(PlanTask, row)

    # ── Flash cards ─────────────────────────────────────────────────────────
    for c in D.FLASH_CARDS:
        row = FlashCard(
            id=c["id"], learner_id=D.LEARNER_ID, front=c["front"], back=c["back"],
            topic=c["topic"], due=_dt(c["due"]), state=0, reps=0, lapses=0,
            created_at=now_utc(),
        )
        await ensure(FlashCard, row)

    # ── Activities ──────────────────────────────────────────────────────────
    for a in D.ACTIVITIES:
        row = Activity(
            id=a["id"], learner_id=D.LEARNER_ID, type=a["type"], label=a["label"], ts=_dt(a["ts"]),
        )
        await ensure(Activity, row)

    # ── Questions (flattened bank) ──────────────────────────────────────────
    for topic, qs in D.QUESTION_BANK.items():
        for q in qs:
            row = Question(
                id=q["id"], type=q["type"], prompt=q["prompt"], options=q.get("options"),
                answer=q["answer"], explanation=q.get("explanation", ""), topic=q["topic"], skill=q.get("skill"),
            )
            await ensure(Question, row)

    # ── Error book ──────────────────────────────────────────────────────────
    for e in D.ERROR_BOOK:
        row = ErrorBook(
            id=e["id"], learner_id=D.LEARNER_ID, question_id=e["question"]["id"],
            question_snapshot=e["question"], user_answer=e["user_answer"], error_type=e["error_type"],
            ts=_dt(e["ts"]), reviewed=e["reviewed"],
        )
        await ensure(ErrorBook, row)

    # ── Knowledge bases + math chunks (embedded) ────────────────────────────
    for kb in D.KNOWLEDGE_BASES:
        row = KnowledgeBase(
            id=kb["id"], owner_learner_id=None, name=kb["name"], engine=kb["engine"],
            document_count=kb["document_count"], status=kb["status"], created_at=_dt(kb["created_at"]),
        )
        await ensure(KnowledgeBase, row)

    math_texts = [c["content"] for c in D.KB_MATH_CHUNKS]
    math_vecs = await providers.embedding.embed(math_texts) if math_texts else []
    for c, vec in zip(D.KB_MATH_CHUNKS, math_vecs):
        row = KbDocument(
            id=c["id"], kb_id=c["kb_id"], title=c["title"], chunk_index=c["chunk_index"],
            embedding=vec, content=c["content"], locator=c.get("locator"), created_at=now_utc(),
        )
        await ensure(KbDocument, row)

    # ── Memory (L1/L2/L3), embed for retrieval ──────────────────────────────
    mem_texts = [m["content"] for m in D.MEMORY_ITEMS]
    mem_vecs = await providers.embedding.embed(mem_texts) if mem_texts else []
    for m, vec in zip(D.MEMORY_ITEMS, mem_vecs):
        row = Memory(
            id=m["id"], learner_id=D.LEARNER_ID, layer=m["layer"], content=m["content"],
            source=m["source"], topic=m.get("topic"), confidence=1.0, evidence=None,
            embedding=vec, created_at=_dt(m["created_at"]),
        )
        await ensure(Memory, row)

    # ── Threads + messages ──────────────────────────────────────────────────
    for th in D.THREADS:
        thread = Thread(
            id=th["id"], learner_id=D.LEARNER_ID, title=th["title"], persona=th["persona"],
            created_at=_dt(th["created_at"]), updated_at=_dt(th["updated_at"]), seq=len(th["messages"]),
        )
        await ensure(Thread, thread)
        for i, msg in enumerate(th["messages"]):
            row = Message(
                id=msg["id"], thread_id=th["id"], learner_id=D.LEARNER_ID, role=msg["role"],
                content=msg["content"], skill=msg.get("skill"), status=msg.get("status", "complete"),
                citations=msg.get("citations"), payload=msg.get("payload"), created_at=_dt(msg["created_at"]),
                seq=i,
            )
            await ensure(Message, row)

    await session.commit()
    log.info("seed complete: %d rows inserted (idempotent)", inserted)
    return inserted
