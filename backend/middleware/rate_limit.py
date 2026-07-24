from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class InMemoryRateLimiter:
    def __init__(self, requests_per_window: int, window_seconds: int) -> None:
        self._requests_per_window = requests_per_window
        self._window_seconds = window_seconds
        self._buckets: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = monotonic()
        with self._lock:
            bucket = self._buckets[key]
            while bucket and now - bucket[0] > self._window_seconds:
                bucket.popleft()
            if len(bucket) >= self._requests_per_window:
                return False
            bucket.append(now)
            return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        requests_per_window: int,
        window_seconds: int,
        exempt_prefixes: tuple[str, ...] | None = None,
    ) -> None:
        super().__init__(app)
        self._limiter = InMemoryRateLimiter(requests_per_window=requests_per_window, window_seconds=window_seconds)
        self._exempt_prefixes = exempt_prefixes or (
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics",
        )

    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(prefix) for prefix in self._exempt_prefixes):
            return await call_next(request)

        caller = request.headers.get("X-API-Key") or (request.client.host if request.client else "unknown")
        rate_key = f"{caller}:{request.url.path}"
        if not self._limiter.allow(rate_key):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please retry later."},
                headers={"Retry-After": str(60)},
            )
        return await call_next(request)
