"""Shared primitives, type aliases, and the pagination envelope."""

from __future__ import annotations

from typing import Generic, List, Literal, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

# ── Type aliases (mirror types.ts) ─────────────────────────────────────────────
PersonaId = Literal["teacher"]
Trend = Literal["up", "down", "flat"]
SkillId = Literal[
    "learning-plan",
    "homework-coach",
    "error-diagnosis",
    "personal-explain",
    "adaptive-practice",
    "mistake-summary",
]
MessageRole = Literal["user", "assistant", "system", "tool"]
MessageStatus = Literal["streaming", "complete", "error"]
MemoryLayer = Literal["L1", "L2", "L3"]
QuestionType = Literal["choice", "fill", "open"]
KbEngine = Literal["llamaindex", "pageindex", "graphrag", "lightrag", "obsidian"]
KbStatus = Literal["ready", "indexing", "error"]


class CamelModel(BaseModel):
    """Base: camelCase fields, tolerant of extras, constructable from ORM attributes."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore", from_attributes=True)


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Optional pagination envelope. List endpoints return a bare array by default and
    this envelope only when ``?limit=&cursor=`` is present (front-end reads bare arrays)."""

    items: List[T]
    nextCursor: Optional[str] = None


class ErrorResponse(CamelModel):
    code: str
    message: str
    details: dict = {}
