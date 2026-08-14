"""Skill invocation contract (types.ts: Citation, StepTrace, SkillRequest, SkillResult)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field

from .common import CamelModel, PersonaId, SkillId
from .learner import LearnerStateDelta


class Citation(CamelModel):
    id: str
    source: str
    snippet: str
    locator: Optional[str] = None


class SkillMeta(CamelModel):
    id: SkillId
    name: str
    description: str
    reads: List[str] = Field(default_factory=list)
    writes: List[str] = Field(default_factory=list)


class StepTrace(CamelModel):
    step: str
    detail: Optional[str] = None


class SkillContext(CamelModel):
    kbIds: Optional[List[str]] = None
    sessionId: Optional[str] = None
    persona: Optional[PersonaId] = None


class SkillRequest(CamelModel):
    skill: SkillId
    learnerId: str
    input: Dict[str, Any] = Field(default_factory=dict)
    context: Optional[SkillContext] = None


class SkillResult(CamelModel):
    skill: SkillId
    output: Dict[str, Any] = Field(default_factory=dict)
    sideEffects: LearnerStateDelta = Field(default_factory=LearnerStateDelta)
    citations: Optional[List[Citation]] = None
    trace: Optional[List[StepTrace]] = None
