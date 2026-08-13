"""Embedding provider seam: BGE-M3 (real) ↔ deterministic hash stub.

The stub produces a fixed-dimension, deterministic vector per text so pgvector cosine
search still functions (and tests are reproducible) without a model download.
"""

from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod
from typing import List, Optional

from ..core.config import settings
from ..core.logging import get_logger

log = get_logger(__name__)


class EmbeddingProvider(ABC):
    name = "base"
    is_stub = False
    dim: int = settings.embedding_dim

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        ...

    async def embed_one(self, text: str) -> List[float]:
        return (await self.embed([text]))[0]


class StubEmbedding(EmbeddingProvider):
    name = "stub"
    is_stub = True

    async def embed(self, texts: List[str]) -> List[List[float]]:
        return [self._vec(t) for t in texts]

    def _vec(self, text: str) -> List[float]:
        dim = self.dim
        # Deterministic 1024-dim-ish vector from a bag of hashed n-grams.
        vec = [0.0] * dim
        tokens = text.lower().split()
        grams = tokens + [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]
        for g in grams:
            h = int(hashlib.blake2b(g.encode("utf-8"), digest_size=4).hexdigest(), 16)
            vec[h % dim] += 1.0
            vec[(h >> 8) % dim] += 0.5
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


class BgeEmbedding(EmbeddingProvider):
    name = "bge"

    def __init__(self, model_name: Optional[str] = None) -> None:
        try:
            from FlagEmbedding import BGEM3FlagModel  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("FlagEmbedding not installed (pip install -e .[embed])") from exc
        self._model_name = model_name or settings.bge_model
        self._enc = BGEM3FlagModel(self._model_name, use_fp16=True)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        import anyio

        def _work():
            out = self._enc.encode(texts, batch_size=12, max_length=8192)
            emb = out["dense_vecs"]
            return [list(map(float, row)) for row in emb]

        return await anyio.to_thread.run_sync(_work)
