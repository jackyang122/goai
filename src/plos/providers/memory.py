"""Memory provider seam: mem0 (real) ↔ heuristic stub.

Only the *intelligence* lives here — fact extraction and semantic retrieval. Persistence
is always the DB (via ``MemoryRepository``): the service mirrors anything mem0 produces
into the ``memory`` table so ``GET /memory`` is robust and single-sourced. Every mem0
call is guarded so a misconfigured graph store never loses the L1 trace.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

from ..core.logging import get_logger

log = get_logger(__name__)


@dataclass
class FactCandidate:
    content: str
    topic: Optional[str] = None
    confidence: float = 1.0
    evidence: List[str] = field(default_factory=list)


@dataclass
class RetrievedFact:
    content: str
    source: str = ""
    score: float = 0.0


class MemoryProvider(ABC):
    name = "base"
    is_stub = False

    @abstractmethod
    async def extract(self, text: str, source: str) -> List[FactCandidate]:
        """Pull durable L2 facts out of a span of conversation text."""

    @abstractmethod
    async def search(self, learner_id: str, query: str, *, k: int = 5) -> List[RetrievedFact]:
        """Retrieve the most relevant facts for a query (used for prompt injection)."""


class StubMemory(MemoryProvider):
    name = "stub"
    is_stub = True

    _KEYWORDS = ("学生", "擅长", "弱", "错误", "符号", "混淆", "策略", "偏好", "总是", "容易")

    async def extract(self, text: str, source: str) -> List[FactCandidate]:
        # Heuristic: keep sentences that look like durable observations.
        facts: List[FactCandidate] = []
        for sentence in _split_sentences(text):
            s = sentence.strip()
            if len(s) < 6:
                continue
            if any(k in s for k in self._KEYWORDS):
                facts.append(FactCandidate(content=s, topic=_guess_topic(s), evidence=[source]))
        # De-dup by content.
        seen, out = set(), []
        for f in facts:
            key = f.content
            if key not in seen:
                seen.add(key)
                out.append(f)
        return out[:5]

    async def search(self, learner_id: str, query: str, *, k: int = 5) -> List[RetrievedFact]:
        return []  # service falls back to its own DB embedding/keyword search


class Mem0Memory(MemoryProvider):
    name = "mem0"

    def __init__(self, user_prefix: str = "plos") -> None:
        try:
            from mem0 import Memory  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("mem0ai not installed (pip install -e .[mem0])") from exc
        self._Memory = Memory
        self._user_prefix = user_prefix
        self._client = None

    def _client_get(self):
        if self._client is None:
            self._client = self._Memory.from_config()  # reads MEM0 config / env
        return self._client

    async def extract(self, text: str, source: str) -> List[FactCandidate]:
        try:
            import anyio

            client = self._client_get()

            def _work() -> List[FactCandidate]:
                added = client.add(messages=[{"role": "user", "content": text}], user_id="_extract")
                out: List[FactCandidate] = []
                for item in added.get("results", []) if isinstance(added, dict) else []:
                    mem = item.get("memory", "")
                    if mem:
                        out.append(
                            FactCandidate(content=mem, topic=_guess_topic(mem), evidence=[source])
                        )
                return out

            return await anyio.to_thread.run_sync(_work)
        except Exception as exc:  # noqa: BLE001
            log.warning("mem0.extract failed, degrading to heuristic: %s", exc)
            return await StubMemory().extract(text, source)

    async def search(self, learner_id: str, query: str, *, k: int = 5) -> List[RetrievedFact]:
        try:
            import anyio

            client = self._client_get()
            uid = f"{self._user_prefix}_{learner_id}"

            def _work() -> List[RetrievedFact]:
                res = client.search(query=query, user_id=uid, limit=k)
                rows = res.get("results", []) if isinstance(res, dict) else list(res)
                return [
                    RetrievedFact(content=r.get("memory", ""), source="mem0", score=float(r.get("score", 0.0)))
                    for r in rows
                ]

            return await anyio.to_thread.run_sync(_work)
        except Exception as exc:  # noqa: BLE001
            log.warning("mem0.search failed, degrading: %s", exc)
            return []


def _split_sentences(text: str) -> List[str]:
    import re

    return [s for s in re.split(r"[。！？!?\n]", text) if s.strip()]


def _guess_topic(text: str) -> Optional[str]:
    for kw, topic in [
        ("二次函数", "二次函数"),
        ("几何", "几何证明"),
        ("时态", "时态辨析"),
        ("牛顿", "牛顿第二定律"),
        ("阅读", "阅读理解"),
    ]:
        if kw in text:
            return topic
    return None
