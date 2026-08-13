"""Three-layer memory (L1 traces / L2 facts / L3 synthesis) + memory graph edges.

The ``memory`` table is the canonical store. When the ``mem0`` provider is configured,
L2 extraction/dedup/merge is delegated to mem0 and a shadow row is mirrored here (with an
``evidence`` pointer) so the frontend's single ``GET /memory`` endpoint always works.
``memory_edge`` captures derived_from / supports / refutes / supersedes relations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base
from ..vector import vector_column


class Memory(Base):
    __tablename__ = "memory"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    learner_id: Mapped[str] = mapped_column(String, ForeignKey("learners.id"), index=True)
    layer: Mapped[str] = mapped_column(String, index=True)  # L1 | L2 | L3
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String, default="")
    topic: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    evidence: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # {derived_from:[ids], …}
    embedding: Mapped[Optional[object]] = mapped_column(vector_column(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class MemoryEdge(Base):
    __tablename__ = "memory_edge"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    learner_id: Mapped[str] = mapped_column(String, index=True)
    src_memory_id: Mapped[str] = mapped_column(String, ForeignKey("memory.id"), index=True)
    dst_memory_id: Mapped[str] = mapped_column(String, ForeignKey("memory.id"), index=True)
    relation: Mapped[str] = mapped_column(String)  # derived_from|supports|refutes|supersedes
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
