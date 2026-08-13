"""Application settings via pydantic-settings.

Environment variables are prefixed ``PLOS_`` (e.g. ``PLOS_DATABASE_URL``). Provider
seams default to ``stub``/``dev`` so the app boots with zero external services; flip the
``*_engine`` knob + provide credentials to engage the real provider.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PLOS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── General ────────────────────────────────────────────────────────────
    app_name: str = "Personal Learning OS"
    debug: bool = False
    env: str = "dev"  # dev | prod
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])

    # ── Database ───────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://plos:plos@localhost:5432/plos"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False

    # ── Domain constants ───────────────────────────────────────────────────
    weak_threshold: float = 0.6  # mastery level strictly below this => weakPoint
    embedding_dim: int = 1024  # BGE-M3 = 1024; parameterized everywhere
    default_learner_id: str = "stu_001"

    # ── Provider engine selection (config-driven seam) ─────────────────────
    llm_engine: str = "stub"  # stub | litellm
    embedding_engine: str = "stub"  # stub | bge
    rag_engine: str = "stub"  # stub | llamaindex
    memory_engine: str = "stub"  # stub | mem0
    auth_engine: str = "dev"  # dev | pocketbase

    # ── LLM (LiteLLM) ──────────────────────────────────────────────────────
    litellm_model: Optional[str] = None  # e.g. "gpt-4o-mini" or "openai/…"
    litellm_api_key: Optional[str] = None
    litellm_api_base: Optional[str] = None

    # ── Embedding (BGE-M3) ─────────────────────────────────────────────────
    bge_model: str = "BAAI/bge-m3"

    # ── Auth (PocketBase) ──────────────────────────────────────────────────
    pocketbase_url: Optional[str] = None
    pocketbase_admin_token: Optional[str] = None
    auth_token_cache_ttl: int = 60  # seconds to cache PB record.id per token

    # ── Memory pipeline ────────────────────────────────────────────────────
    memory_l2_debounce_sec: float = 4.0
    memory_l3_idle_sec: float = 600.0

    # ── WebSocket ──────────────────────────────────────────────────────────
    ws_ping_interval: int = 20

    # ── Runtime helpers ────────────────────────────────────────────────────
    seed_on_start: bool = True
    # Dev affordance: create tables from the ORM on startup (idempotent). Prod should use
    # Alembic with this off. Requires the pgvector extension (auto-created via lifespan).
    auto_create_tables: bool = True

    @property
    def auth_strict(self) -> bool:
        """Strict auth is engaged only when PocketBase is configured."""
        return self.auth_engine == "pocketbase" and bool(self.pocketbase_url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Convenience module-level accessor.
settings = get_settings()
