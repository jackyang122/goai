"""ConnectionManager — tracks active WebSocket connections (observability/broadcast hook)."""

from __future__ import annotations

from typing import List, Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._active.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._active.discard(ws)

    @property
    def active_count(self) -> int:
        return len(self._active)

    def all(self) -> List[WebSocket]:
        return list(self._active)


manager = ConnectionManager()
