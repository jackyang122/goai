"""Personal Learning OS — backend package.

Layered FastAPI backend: ``api``/``ws`` (transport) → ``domain`` (transport-agnostic
logic) → ``db.repositories`` (the only SQL emitters) + ``providers`` (the only external
service callers). ``schemas`` is a 1:1 Pydantic mirror of ``web/lib/api/types.ts``.
"""

__version__ = "0.1.0"
