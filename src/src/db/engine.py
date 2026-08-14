"""Async SQLAlchemy 2 engine + session factory + pgvector bootstrap.

Notes
-----
* DSN must use the ``postgresql+asyncpg://`` driver.
* Sessions use ``expire_on_commit=False``: after a commit, attribute access on ORM
  objects must NOT trigger a lazy SQL emit (which would raise ``MissingGreenlet`` under
  async). Keeping attributes live post-commit is essential for the response mapping path.
* ``CREATE EXTENSION vector`` is run once at startup via :func:`ensure_extensions`
  (idempotent). It is intentionally NOT inside an Alembic migration so the migration does
  not require superuser privileges.
"""

from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..core.config import settings
from ..core.logging import get_logger

log = get_logger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def build_connect_args() -> dict:
    """Build asyncpg ``connect_args`` from settings.

    Handles the two integration points needed for hosted Postgres such as Supabase:

    * **SSL** — required on every Supabase connection (pooler and direct). ``db_ssl=auto``
      (default) resolves to ``require`` for any non-localhost host and ``disable`` for
      localhost, so local dev keeps working with no configuration.
    * **Prepared statements** — asyncpg caches them per connection, which is incompatible
      with a transaction-mode pooler (Supabase port 6543 / PgBouncer). Setting
      ``db_pool_mode=pgbouncer`` disables the cache (``statement_cache_size=0``).
    """
    args: dict = {}

    ssl = settings.db_ssl
    if ssl == "auto":
        host = (make_url(settings.database_url).host or "").lower()
        ssl = "disable" if host in _LOCAL_HOSTS else "require"
    if ssl != "disable":
        # asyncpg accepts disable | prefer | require | verify-ca | verify-full (or an
        # ssl.SSLContext). Only pass it when not disabled so localhost stays plain.
        args["ssl"] = ssl

    if settings.db_pool_mode == "pgbouncer":
        args["statement_cache_size"] = 0

    return args


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.db_echo,
            pool_pre_ping=True,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            connect_args=build_connect_args(),
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            class_=AsyncSession,
            autoflush=False,
        )
    return _session_factory


async def ensure_extensions() -> None:
    """Create the pgvector extension if missing. Idempotent; requires CREATE priv."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))


async def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


async def check_db() -> bool:
    """Lightweight connectivity probe for the health endpoint."""
    try:
        factory = get_session_factory()
        async with factory() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("db health check failed: %s", exc)
        return False


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a session; rolls back on exception."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
