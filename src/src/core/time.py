"""Time helpers — UTC ISO-8601 strings with trailing ``Z``."""

from __future__ import annotations

from datetime import datetime, timezone


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    """Current time as ``YYYY-MM-DDTHH:MM:SS.ffffffZ``."""
    return now_utc().isoformat().replace("+00:00", "Z")


def to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))
