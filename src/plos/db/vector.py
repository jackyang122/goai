"""pgvector column type + cosine distance helpers."""

from __future__ import annotations

from typing import List

from pgvector.sqlalchemy import Vector

from ..core.config import settings


def vector_column():
    """Return a ``Vector`` SQLAlchemy type sized to the configured embedding dim."""
    return Vector(settings.embedding_dim)


def cosine_distance_sql(column, embedding: List[float]):
    """Cosine distance expression: ``column <=> embedding`` (0 = identical)."""
    return column.cosine_distance(embedding)
