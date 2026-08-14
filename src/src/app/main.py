"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..api import cards, kbs, learners, memory, quiz, skills, threads
from ..core.config import settings
from ..db.engine import check_db
from ..ws import chat as ws_chat
from .errors import register_handlers
from .lifespan import lifespan


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Personal Learning OS backend — agent-native personalized learning.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_handlers(app)

    # REST routers (thin transport layer).
    for mod in (learners, skills, threads, kbs, quiz, cards, memory):
        app.include_router(mod.router)
    # WebSocket router.
    app.include_router(ws_chat.router)

    @app.get("/api/health", tags=["meta"])
    async def health() -> dict:
        return {
            "status": "ok",
            "app": settings.app_name,
            "db": await check_db(),
            "providers": {
                "llm": app.state.providers.llm.name,
                "embedding": app.state.providers.embedding.name,
                "memory": app.state.providers.memory.name,
                "auth": app.state.providers.auth.name,
                "parser": app.state.providers.parser.name,
            },
        }

    return app


app = create_app()
