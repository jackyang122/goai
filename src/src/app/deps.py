"""FastAPI dependencies: session, providers, auth."""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, Request

from ..db.engine import get_session
from ..providers.auth import AuthProvider
from ..providers.registry import ProviderContainer


def get_providers(request: Request) -> ProviderContainer:
    return request.app.state.providers


def get_auth(providers: ProviderContainer = Depends(get_providers)) -> AuthProvider:
    return providers.auth


def get_token(authorization: Optional[str] = Header(default=None)) -> Optional[str]:
    return authorization


# Session dependency (re-exported so routers import from one place).
__all__ = ["get_providers", "get_auth", "get_token", "get_session", "Depends", "Header"]
