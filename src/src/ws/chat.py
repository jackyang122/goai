"""``/ws/chat`` — streaming chat over the unified pipeline.

Client sends JSON messages ``{threadId, learnerId, content, persona?, kbIds?}``; the server
streams NDJSON events (skill → citation → content{delta} → payload → done) produced by
``ChatTurnOrchestrator.run_stream``. A 20s ping keeps the connection alive.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..core.config import settings
from ..core.logging import get_logger
from ..db.engine import get_session_factory
from ..domain.chat import ChatTurnOrchestrator
from .events import error_line, ping_line, serialize_event
from .manager import manager

log = get_logger(__name__)
router = APIRouter()


@router.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    providers = websocket.app.state.providers
    auth = providers.auth

    # Auth: in strict mode this resolves+validates the token; in dev it's a no-op.
    try:
        # Resolve against an empty claimed id (the real id comes per-message).
        default_lid = await auth.resolve_learner(token, "")
    except PermissionError as exc:
        await websocket.accept()
        await websocket.send_text(error_line("unauthorized", str(exc)))
        await websocket.close()
        return

    await manager.connect(websocket)
    ping_task = asyncio.create_task(_pinger(websocket))

    try:
        while True:
            raw = await websocket.receive_text()
            await _handle_message(websocket, raw, auth, providers, token, default_lid)
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # noqa: BLE001
        log.warning("ws/chat error: %s", exc)
        try:
            await websocket.send_text(error_line("internal", str(exc)))
        except Exception:  # noqa: BLE001
            pass
    finally:
        ping_task.cancel()
        manager.disconnect(websocket)


async def _handle_message(websocket, raw: str, auth, providers, token, default_lid: str) -> None:
    import json

    try:
        msg: Dict[str, Any] = json.loads(raw)
    except Exception:  # noqa: BLE001
        await websocket.send_text(error_line("bad_request", "invalid JSON"))
        return

    thread_id = msg.get("threadId")
    claimed = msg.get("learnerId") or default_lid
    content = msg.get("content")
    if not thread_id or content is None:
        await websocket.send_text(error_line("bad_request", "threadId and content required"))
        return
    persona = msg.get("persona", "teacher")
    kb_ids: Optional[List[str]] = msg.get("kbIds")

    try:
        lid = await auth.resolve_learner(token, claimed)
    except PermissionError as exc:
        await websocket.send_text(error_line("forbidden", str(exc)))
        return

    factory = get_session_factory()
    async with factory() as session:
        try:
            orch = ChatTurnOrchestrator(session, providers)
            async for ev in orch.run_stream(lid, thread_id, content, persona, kb_ids):
                await websocket.send_text(serialize_event(ev.type, ev.data))
            await session.commit()
        except Exception as exc:  # noqa: BLE001
            await session.rollback()
            await websocket.send_text(error_line("internal", str(exc)))


async def _pinger(websocket: WebSocket) -> None:
    try:
        while True:
            await asyncio.sleep(settings.ws_ping_interval)
            await websocket.send_text(ping_line())
    except asyncio.CancelledError:
        raise
    except Exception:  # noqa: BLE001
        pass
