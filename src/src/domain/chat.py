"""ChatTurnOrchestrator — the unified chat pipeline, shared by REST and WebSocket.

Pipeline (design doc §4): route skill → retrieve memory → retrieve KB → generate content
(streamed) → attach structured payload + citations → persist user+assistant messages →
write L1 trace → trigger L2 extraction. ``run`` is exactly ``run_stream`` collected into a
single ``ChatMessage`` so REST and WS never diverge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncIterator, Dict, List, Optional

from ..core.ids import new_id
from ..core.time import now_utc
from ..db.models.chat import Message, Thread
from ..db.models.learners import Activity
from ..db.repositories import MessageRepository, ThreadRepository
from ..providers.llm import Message as LLMMessage
from ..providers.registry import ProviderContainer
from ..schemas.chat import (
    ChatMessage,
    ChatPayload,
    CoachPayload,
    DiagnosisInfo,
    DiagnosisPayload,
    ErrorPattern,
    PlanPayload,
    QuizPayload,
    SummaryPayload,
)
from ..schemas.common import PersonaId, SkillId
from ..schemas.learner import LearnerState
from ..schemas.skill import Citation
from .learner_state import LearnerStateService
from .memory import MemoryService
from .rag import RagOrchestrator
from .skills.base import SkillContext
from .skills.router import SkillRouter
from .skills.routing import canned_reply, pick_skill


@dataclass
class ChatEvent:
    type: str
    data: Dict = field(default_factory=dict)


class ChatTurnOrchestrator:
    def __init__(self, session, providers: ProviderContainer) -> None:
        self.session = session
        self.providers = providers
        self.threads = ThreadRepository(session)
        self.messages = MessageRepository(session)
        self.learner_state = LearnerStateService(session)
        self.memory = MemoryService(session, providers)
        self.rag = RagOrchestrator(session, providers)
        self.skills = SkillRouter()

    # ── public entrypoints ──────────────────────────────────────────────────
    async def run(
        self,
        learner_id: str,
        thread_id: str,
        content: str,
        persona: PersonaId = "teacher",
        kb_ids: Optional[List[str]] = None,
    ) -> ChatMessage:
        """Non-streaming turn: collect ``run_stream`` into one ChatMessage."""
        text_parts: List[str] = []
        payload = None
        citations: List[Citation] = []
        message_id = None
        skill_id: Optional[SkillId] = None
        async for ev in self.run_stream(learner_id, thread_id, content, persona, kb_ids):
            if ev.type == "content":
                text_parts.append(ev.data.get("delta", ""))
            elif ev.type == "payload":
                payload = ev.data.get("payload")
            elif ev.type == "citation":
                citations.append(Citation(**ev.data))
            elif ev.type == "skill":
                skill_id = ev.data.get("skill")
            elif ev.type == "done":
                message_id = ev.data.get("messageId")
        return ChatMessage(
            id=message_id or new_id("msg"),
            role="assistant",
            content="".join(text_parts),
            createdAt=now_iso_str(),
            citations=citations or None,
            skill=skill_id,
            status="complete",
            payload=payload,
        )

    async def run_stream(
        self,
        learner_id: str,
        thread_id: str,
        content: str,
        persona: PersonaId = "teacher",
        kb_ids: Optional[List[str]] = None,
    ) -> AsyncIterator[ChatEvent]:
        # 1. Ensure thread exists.
        thread = await self.threads.get(thread_id)
        created_thread = False
        if thread is None:
            thread = Thread(
                id=thread_id,
                learner_id=learner_id,
                title=content[:24] or "新对话",
                persona=persona,
                created_at=now_utc(),
                updated_at=now_utc(),
                seq=0,
            )
            self.session.add(thread)
            await self.session.flush()
            created_thread = True

        # 2. Persist the user message + L1 trace.
        user_msg = await self._add_message(thread_id, learner_id, "user", content)
        l1 = await self.memory.write_l1(
            learner_id, f"用户提问：{content}", source=f"chat:{thread_id}"
        )

        # 3. Route skill + load state.
        skill_id = pick_skill(content)
        yield ChatEvent("skill", {"skill": skill_id})
        state: Optional[LearnerState] = None
        try:
            state = await self.learner_state.get_state(learner_id)
        except Exception:  # noqa: BLE001
            state = None

        # 4. Retrieve memory + KB citations.
        citations: List[Citation] = []
        try:
            citations.extend(await self.memory.retrieve_citations(learner_id, content, k=3))
        except Exception:  # noqa: BLE001
            pass
        if kb_ids:
            try:
                citations.extend(await self.rag.retrieve(content, kb_ids, top_k=3))
            except Exception:  # noqa: BLE001
                pass
        for c in citations:
            yield ChatEvent("citation", c.model_dump())

        # 5. Build structured payload (rich skills reuse the skill's structured output).
        payload = await self._build_payload(skill_id, learner_id, content, state)

        # 6. Generate content (streamed).
        history = await self._history(thread_id, limit=8)
        async for delta in self._generate(skill_id, content, history, citations, persona):
            yield ChatEvent("content", {"delta": delta})
        if payload is not None:
            yield ChatEvent("payload", {"payload": payload.model_dump(mode="json")})

        # 7. Persist assistant message.
        full_text = await self._materialize(skill_id, content, history, citations, persona)
        assistant = await self._add_message(
            thread_id,
            learner_id,
            "assistant",
            full_text,
            skill=skill_id,
            citations=citations or None,
            payload=payload.model_dump(mode="json") if payload else None,
        )
        await self.threads.touch(thread_id, title=None if not created_thread else thread.title)
        # Record a chat activity.
        self.session.add(
            Activity(
                id=new_id("act"),
                learner_id=learner_id,
                type="chat",
                label=content[:48],
                ts=now_utc(),
            )
        )
        await self.session.flush()

        # 8. L2 extraction at turn end (best-effort; never lose L1).
        try:
            await self.memory.extract_and_store_l2(
                learner_id, text=f"用户：{content}\n助手：{full_text}", source=f"chat:{thread_id}",
                evidence_ids=[l1.id],
            )
            await self.session.flush()
        except Exception:  # noqa: BLE001
            pass

        yield ChatEvent("done", {"messageId": assistant.id})

    # ── helpers ──────────────────────────────────────────────────────────────
    async def _add_message(
        self, thread_id, learner_id, role, content, *, skill=None, citations=None, payload=None
    ) -> Message:
        # The ``citations`` JSONB column stores plain JSON, so Pydantic ``Citation``
        # objects must be serialized here at the persistence boundary — the column's
        # default ``json.dumps`` binder cannot encode them and raises
        # "Object of type Citation is not JSON serializable".
        citations_json = [c.model_dump(mode="json") for c in citations] if citations else None
        msg = Message(
            id=new_id("msg"),
            thread_id=thread_id,
            learner_id=learner_id,
            role=role,
            content=content,
            skill=skill,
            status="complete",
            citations=citations_json,
            payload=payload,
            created_at=now_utc(),
        )
        return await self.messages.add(msg)

    async def _history(self, thread_id: str, limit: int = 8) -> List[LLMMessage]:
        rows = await self.messages.list_by_thread(thread_id)
        rows = rows[-limit:]
        return [{"role": r.role, "content": r.content} for r in rows if r.role in ("user", "assistant")]

    async def _build_payload(
        self, skill_id: SkillId, learner_id: str, content: str, state: Optional[LearnerState]
    ) -> Optional[ChatPayload]:
        rich = {"learning-plan", "homework-coach", "adaptive-practice", "error-diagnosis", "mistake-summary"}
        if skill_id not in rich:
            return None
        try:
            ctx = SkillContext(
                session=self.session,
                learner_id=learner_id,
                skill_id=skill_id,
                input=_skill_input(skill_id, content),
                providers=self.providers,
                learner_state=state,
            )
            result = await self.skills.invoke(ctx)
            return _to_payload(skill_id, result.output)
        except Exception:  # noqa: BLE001
            return None

    async def _generate(
        self, skill_id, content, history, citations, persona
    ) -> AsyncIterator[str]:
        if self.providers.llm.is_stub:
            yield canned_reply(content)
            return
        system = (
            "你是亲切的高中老师（teacher 人设），用中文回答。关键公式用 LaTeX $...$。"
            "结合以下记忆与资料作答；如引用，简述来源。"
        )
        ctx_lines = []
        if citations:
            ctx_lines.append("资料/记忆：\n" + "\n".join(f"- {c.snippet}（{c.source}）" for c in citations))
        msgs: List[LLMMessage] = list(history[-6:])
        msgs.append({"role": "user", "content": content})
        async for delta in self.providers.llm.stream(msgs, system=system + ("\n" + "\n".join(ctx_lines) if ctx_lines else "")):
            yield delta

    async def _materialize(self, skill_id, content, history, citations, persona) -> str:
        if self.providers.llm.is_stub:
            return canned_reply(content)
        parts: List[str] = []
        async for d in self._generate(skill_id, content, history, citations, persona):
            parts.append(d)
        return "".join(parts)


def _skill_input(skill_id: SkillId, content: str) -> dict:
    if skill_id == "adaptive-practice":
        return {"topic": "二次函数", "count": 1}
    if skill_id == "homework-coach":
        return {"question": content}
    if skill_id == "error-diagnosis":
        return {"question": {"prompt": content, "answer": ""}, "userAnswer": ""}
    if skill_id == "learning-plan":
        return {"availableMin": 55}
    if skill_id == "personal-explain":
        return {"concept": content.replace("解释", "").replace("讲", "") or "二次函数顶点"}
    return {}


def _to_payload(skill_id: SkillId, output: dict) -> Optional[ChatPayload]:
    try:
        if skill_id == "learning-plan":
            from ..schemas.learner import PlanTask

            tasks = [PlanTask(**t) for t in output.get("plan", [])]
            return PlanPayload(tasks=tasks, rationale=output.get("rationale"))
        if skill_id == "homework-coach":
            from ..schemas.skill import StepTrace

            return CoachPayload(steps=[StepTrace(**s) for s in output.get("steps", [])])
        if skill_id == "adaptive-practice":
            from ..schemas.quiz import Question

            qs = output.get("questions", [])
            return QuizPayload(question=Question(**qs[0])) if qs else None
        if skill_id == "error-diagnosis":
            return DiagnosisPayload(
                diagnosis=DiagnosisInfo(
                    cause=output.get("cause", ""),
                    evidence=output.get("evidence"),
                    remedy=output.get("remedy"),
                )
            )
        if skill_id == "mistake-summary":
            return SummaryPayload(
                patterns=[ErrorPattern(**p) for p in output.get("patterns", [])],
                suggestion=output.get("suggestion"),
            )
    except Exception:  # noqa: BLE001
        return None
    return None


def now_iso_str() -> str:
    return now_utc().isoformat().replace("+00:00", "Z")
