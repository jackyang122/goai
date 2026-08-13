"""Knowledge-base schemas (types.ts: KnowledgeBase) + create/upload/search requests."""

from __future__ import annotations

from typing import List, Optional

from .common import CamelModel, KbEngine, KbStatus
from .skill import Citation


class KnowledgeBase(CamelModel):
    id: str
    name: str
    engine: KbEngine = "llamaindex"
    documentCount: int = 0
    status: KbStatus = "ready"
    createdAt: str


class CreateKbRequest(CamelModel):
    name: str
    engine: KbEngine = "llamaindex"
    ownerLearnerId: Optional[str] = None


class SearchKbRequest(CamelModel):
    query: str
    topK: int = 4
