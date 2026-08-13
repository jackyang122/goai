"""Chat schemas + the ``payload`` discriminated union (8-scenario rich content).

The ``payload`` field is the design-doc contract gap: a message may carry one structured
rich-content block keyed by ``kind`` (plan / coach / quiz / diagnosis / summary). The
frontend renders it by ``kind``; plain-text-only messages simply omit ``payload``.
"""

from __future__ import annotations

from typing import Annotated, List, Literal, Optional, Union

from pydantic import Field

from .common import CamelModel, MessageRole, MessageStatus, PersonaId, SkillId
from .quiz import Question
from .skill import Citation
from .learner import PlanTask
from .skill import StepTrace


# ── payload variants ──────────────────────────────────────────────────────────
class PlanPayload(CamelModel):
    kind: Literal["plan"] = "plan"
    tasks: List[PlanTask] = Field(default_factory=list)
    rationale: Optional[str] = None


class CoachPayload(CamelModel):
    kind: Literal["coach"] = "coach"
    steps: List[StepTrace] = Field(default_factory=list)


class QuizPayload(CamelModel):
    kind: Literal["quiz"] = "quiz"
    question: Question


class DiagnosisInfo(CamelModel):
    cause: str
    evidence: Optional[str] = None
    remedy: Optional[str] = None


class DiagnosisPayload(CamelModel):
    kind: Literal["diagnosis"] = "diagnosis"
    diagnosis: DiagnosisInfo


class ErrorPattern(CamelModel):
    type: str
    count: int = 0
    trend: Optional[str] = None


class SummaryPayload(CamelModel):
    kind: Literal["summary"] = "summary"
    patterns: List[ErrorPattern] = Field(default_factory=list)
    suggestion: Optional[str] = None


ChatPayload = Annotated[
    Union[PlanPayload, CoachPayload, QuizPayload, DiagnosisPayload, SummaryPayload],
    Field(discriminator="kind"),
]


class ChatMessage(CamelModel):
    id: str
    role: MessageRole
    content: str = ""
    createdAt: str
    citations: Optional[List[Citation]] = None
    skill: Optional[SkillId] = None
    status: Optional[MessageStatus] = None
    payload: Optional[ChatPayload] = None  # 〔协议扩展〕 8-scenario rich content


class ChatThread(CamelModel):
    id: str
    title: str = ""
    persona: PersonaId = "teacher"
    messages: List[ChatMessage] = Field(default_factory=list)
    createdAt: str
    updatedAt: str


class SendMessageRequest(CamelModel):
    learnerId: str
    content: str
    persona: PersonaId = "teacher"
