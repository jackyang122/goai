"""Auth provider seam: PocketBase (strict, prod) ↔ Dev (lenient, dev).

In dev (no ``PLOS_POCKETBASE_URL``), the provider accepts the client-supplied
``learnerId`` (the frontend hardcodes ``stu_001``). In prod, it validates the bearer
token against PocketBase and forbids any mismatch with the path/body ``learnerId``.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Optional

import httpx

from ..core.config import settings
from ..core.logging import get_logger

log = get_logger(__name__)


class AuthProvider(ABC):
    name = "base"
    strict = False

    @abstractmethod
    async def resolve_learner(self, token: Optional[str], claimed_id: str) -> str:
        """Return the authoritative learner id for this request."""


class DevAuth(AuthProvider):
    name = "dev"
    strict = False

    async def resolve_learner(self, token: Optional[str], claimed_id: str) -> str:
        return claimed_id or settings.default_learner_id


class PocketBaseAuth(AuthProvider):
    name = "pocketbase"
    strict = True

    def __init__(self, base_url: str, admin_token: Optional[str] = None, ttl: int = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.admin_token = admin_token
        self._ttl = ttl
        self._cache: dict[str, tuple[str, float]] = {}

    async def _verify(self, token: str) -> str:
        now = time.monotonic()
        cached = self._cache.get(token)
        if cached and cached[1] > now:
            return cached[0]
        # Refresh validates the token and returns the record (includes id).
        url = f"{self.base_url}/api/collections/users/auth-refresh"
        headers = {"Authorization": token}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers)
        if resp.status_code >= 400:
            # Some PB installs scope users under a different collection; try /records self.
            record_id = await self._verify_as_admin(token)
        else:
            data = resp.json()
            record = data.get("record", {})
            record_id = record.get("id") or data.get("id")
        if not record_id:
            raise PermissionError("invalid token")
        self._cache[token] = (record_id, now + self._ttl)
        return record_id

    async def _verify_as_admin(self, token: str) -> str:
        if not self.admin_token:
            raise PermissionError("invalid token")
        url = f"{self.base_url}/api/collections/users/records"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                url, headers={"Authorization": self.admin_token}, params={"filter": f"token='{token}'"}
            )
        items = resp.json().get("items", []) if resp.status_code < 400 else []
        if not items:
            raise PermissionError("invalid token")
        return items[0]["id"]

    async def resolve_learner(self, token: Optional[str], claimed_id: str) -> str:
        if not token:
            raise PermissionError("missing token")
        raw = token.strip()
        if raw.lower().startswith("bearer "):
            raw = raw[7:].strip()
        record_id = await self._verify(raw)
        if claimed_id and claimed_id != record_id:
            raise PermissionError("token does not match learnerId")
        return record_id
