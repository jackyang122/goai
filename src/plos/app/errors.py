"""Unified error envelope.

Every error response has the shape::

    {"error": {"code": "...", "message": "...", "details": {...}}}

raised via :class:`ApiError` (or a convenience constructor). Handlers are registered on
the FastAPI app by :func:`register_handlers`.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_payload(self) -> Dict[str, Any]:
        return {"error": {"code": self.code, "message": self.message, "details": self.details}}


# ── Convenience constructors ──────────────────────────────────────────────────

def bad_request(message: str, details: Optional[Dict[str, Any]] = None) -> ApiError:
    return ApiError("bad_request", message, 400, details)


def unauthorized(message: str = "unauthorized") -> ApiError:
    return ApiError("unauthorized", message, 401)


def forbidden(message: str = "forbidden") -> ApiError:
    return ApiError("forbidden", message, 403)


def not_found(message: str, details: Optional[Dict[str, Any]] = None) -> ApiError:
    return ApiError("not_found", message, 404, details)


def conflict(message: str, details: Optional[Dict[str, Any]] = None) -> ApiError:
    return ApiError("conflict", message, 409, details)


def unprocessable(message: str, details: Optional[Dict[str, Any]] = None) -> ApiError:
    return ApiError("unprocessable", message, 422, details)


def not_implemented(message: str, details: Optional[Dict[str, Any]] = None) -> ApiError:
    return ApiError("not_implemented", message, 501, details)


# ── Handlers ──────────────────────────────────────────────────────────────────

async def _api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.to_payload())


async def _validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "request validation failed",
                "details": {"errors": exc.errors()},
            }
        },
    )


async def _unhandled_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal", "message": "internal server error", "details": {}}},
    )


def register_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, _api_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(Exception, _unhandled_handler)
