"""Application lifespan: logging, providers, schema setup, idempotent seed."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from ..core.config import settings
from ..core.logging import configure_logging, get_logger
from ..db.base import Base
from ..db.engine import dispose_engine, ensure_extensions, get_engine, get_session_factory
from ..providers.registry import build_providers

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging("DEBUG" if settings.debug else "INFO")
    app.state.providers = build_providers()

    engine = get_engine()
    try:
        await ensure_extensions()
        if settings.auto_create_tables:
            async with engine.begin() as conn:
                await Base.metadata.create_all(conn)
        log.info("database schema ready")
    except Exception as exc:  # noqa: BLE001
        log.warning("DB schema setup skipped (is Postgres reachable at %s?): %s", settings.database_url, exc)

    if settings.seed_on_start:
        try:
            from ..seed.seed import run as seed_run

            factory = get_session_factory()
            async with factory() as session:
                await seed_run(session, app.state.providers)
        except Exception as exc:  # noqa: BLE001
            log.warning("seed skipped: %s", exc)

    yield
    await dispose_engine()
