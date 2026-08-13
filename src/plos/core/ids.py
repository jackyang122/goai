"""ID generation: ``<type>_<ulid>`` (lowercase). Falls back to a time-sortable hex id
when the ``python-ulid`` package is unavailable so the app never hard-fails on IDs."""

from __future__ import annotations

import secrets
import time

try:  # python-ulid
    from ulid import ULID as _ULID  # type: ignore

    def _raw() -> str:
        return str(_ULID()).lower()

except Exception:  # pragma: no cover - fallback path
    _ENC = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

    def _raw() -> str:
        # 10ms-precision time (48 bits worth) + randomness → 26 Crockford-ish chars.
        ms = int(time.time() * 1000)
        out = []
        for _ in range(10):
            out.append(_ENC[ms & 0x1F])
            ms >>= 5
        out.reverse()
        rand = secrets.randbits(80)
        for _ in range(16):
            out.append(_ENC[rand & 0x1F])
            rand >>= 5
        out.reverse()
        return "".join(out).lower()


def new_id(type_: str) -> str:
    """Return a typed unique id, e.g. ``msg_01hz…``."""
    return f"{type_}_{_raw()}"
