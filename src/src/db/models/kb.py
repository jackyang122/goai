"""Knowledge bases (multi-engine RAG) + chunked documents with pgvector embeddings."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base
from ..vector import vector_column


class KnowledgeBase(Base):
    __tablename__ = "kb"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_learner_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    name: Mapped[str] = mapped_column(Text)
    engine: Mapped[str] = mapped_column(String, default="llamaindex")
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="indexing")  # ready|indexing|error
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class KbDocument(Base):
    """A chunk of an ingested document; one row per chunk for vector search."""

    __tablename__ = "kb_documents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    kb_id: Mapped[str] = mapped_column(String, ForeignKey("kb.id"), index=True)
    title: Mapped[str] = mapped_column(Text, default="")
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    embedding: Mapped[Optional[object]] = mapped_column(vector_column(), nullable=True)
    content: Mapped[str] = mapped_column(Text, default="")
    locator: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # e.g. "p.4"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
