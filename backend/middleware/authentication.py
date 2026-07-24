from __future__ import annotations

import secrets

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, api_key: str, exempt_prefixes: tuple[str, ...] | None = None) -> None:
        super().__init__(app)
        self._api_key = api_key
        self._enabled = bool(api_key)
        self._exempt_prefixes = exempt_prefixes or (
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics",
        )

    async def dispatch(self, request: Request, call_next):
        if not self._enabled or any(request.url.path.startswith(prefix) for prefix in self._exempt_prefixes):
            return await call_next(request)

        presented = request.headers.get("X-API-Key", "")
        if not presented or not secrets.compare_digest(presented, self._api_key):
            return JSONResponse(status_code=401, content={"detail": "Authentication required."})

        request.state.authenticated_principal = "api-key"
        return await call_next(request)
