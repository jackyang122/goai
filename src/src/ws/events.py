"""NDJSON event serialization for the WS protocol (§8 of API协议.md)."""

from __future__ import annotations

import json
from typing import Any, Dict


def serialize_event(event_type: str, data: Dict[str, Any]) -> str:
    """One NDJSON line: ``{"type": <event_type>, ...data}``."""
    payload = {"type": event_type}
    payload.update(data)
    return json.dumps(payload, ensure_ascii=False, default=str)


def ping_line() -> str:
    return serialize_event("ping", {})


def error_line(code: str, message: str) -> str:
    return serialize_event("error", {"code": code, "message": message})
