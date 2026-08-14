"""Provider registry — assembles the provider container from settings, degrading to
stubs (with a warning) when a real provider is unconfigured or its dependency is absent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..core.config import Settings
from ..core.logging import get_logger
from .auth import AuthProvider, DevAuth, PocketBaseAuth
from .embedding import BgeEmbedding, EmbeddingProvider, StubEmbedding
from .llm import DeepTutorProvider, LLMProvider, LiteLLMProvider, StubLLM
from .memory import Mem0Memory, MemoryProvider, StubMemory
from .parser import DoclingParser, DocumentParser, StubParser

log = get_logger(__name__)


@dataclass
class ProviderContainer:
    llm: LLMProvider
    embedding: EmbeddingProvider
    memory: MemoryProvider
    auth: AuthProvider
    parser: DocumentParser


def _build_llm(s: Settings) -> LLMProvider:
    if s.llm_engine == "deeptutor":
        try:
            return DeepTutorProvider(
                s.deeptutor_base_url,
                s.deeptutor_token,
                s.deeptutor_capability,
                s.deeptutor_language,
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("DeepTutor configuration invalid (%s); falling back to stub LLM.", exc)
    if s.llm_engine == "litellm" and s.litellm_model:
        try:
            return LiteLLMProvider(s.litellm_model, s.litellm_api_key, s.litellm_api_base)
        except Exception as exc:  # noqa: BLE001
            log.warning("LiteLLM unavailable (%s); falling back to stub LLM.", exc)
    elif s.llm_engine == "litellm":
        log.warning("llm_engine=litellm but PLOS_LITELLM_MODEL is unset; using stub LLM.")
    return StubLLM()


def _build_embedding(s: Settings) -> EmbeddingProvider:
    if s.embedding_engine == "bge":
        try:
            return BgeEmbedding(s.bge_model)
        except Exception as exc:  # noqa: BLE001
            log.warning("BGE-M3 unavailable (%s); falling back to stub embedding.", exc)
    return StubEmbedding()


def _build_memory(s: Settings) -> MemoryProvider:
    if s.memory_engine == "mem0":
        try:
            return Mem0Memory()
        except Exception as exc:  # noqa: BLE001
            log.warning("mem0 unavailable (%s); falling back to stub memory.", exc)
    return StubMemory()


def _build_parser(s: Settings) -> DocumentParser:
    # Parser is always present; pick docling only if explicitly enabled via extra presence.
    try:
        return DoclingParser()
    except Exception:  # noqa: BLE001
        return StubParser()


def _build_auth(s: Settings) -> AuthProvider:
    if s.auth_engine == "pocketbase" and s.pocketbase_url:
        return PocketBaseAuth(s.pocketbase_url, s.pocketbase_admin_token, s.auth_token_cache_ttl)
    return DevAuth()


def build_providers(s: Optional[Settings] = None) -> ProviderContainer:
    s = s or Settings()
    container = ProviderContainer(
        llm=_build_llm(s),
        embedding=_build_embedding(s),
        memory=_build_memory(s),
        auth=_build_auth(s),
        parser=_build_parser(s),
    )
    log.info(
        "providers: llm=%s embedding=%s memory=%s auth=%s parser=%s",
        container.llm.name,
        container.embedding.name,
        container.memory.name,
        container.auth.name,
        container.parser.name,
    )
    return container
