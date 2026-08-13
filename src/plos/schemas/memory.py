"""Memory schemas: three-layer items, graph, and the write request."""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from .common import CamelModel, MemoryLayer


class MemoryItem(CamelModel):
    id: str
    layer: MemoryLayer
    content: str
    source: str = ""
    createdAt: str
    topic: Optional[str] = None
    confidence: Optional[float] = None


class MemoryEdge(CamelModel):
    id: str
    src: str
    dst: str
    relation: str  # derived_from | supports | refutes | supersedes
    weight: float = 1.0


class MemoryGraph(CamelModel):
    nodes: List[MemoryItem] = Field(default_factory=list)
    edges: List[MemoryEdge] = Field(default_factory=list)


class WriteMemoryRequest(CamelModel):
    learnerId: str
    layer: MemoryLayer
    content: str
    source: str = "manual"
    topic: Optional[str] = None
    confidence: float = 1.0
