"""
Rate-Limit Middleware
========================
In-process rate limiting using a sliding-window counter in Redis.
Falls through silently when Redis is unavailable (degraded mode).
"""

from __future__ import annotations

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings

# Rate limit presets: path_prefix -> (max_requests, window_seconds)
RATE_LIMITS: dict[str, tuple[int, int]] = {
    "/api/tree": (30, 60),
    "/api/quiz/generate": (5, 3600),
    "/api/quiz": (20, 60),
    "/api/concepts": (60, 60),
    "/api/analysis/complexity": (20, 60),
    "/api/analysis": (60, 60),
}


def _match_limit(path: str) -> tuple[int, int] | None:
    """Return (max_rps, window_s) for the most specific path prefix match."""
    matched = None
    matched_len = 0
    for prefix, limit in RATE_LIMITS.items():
        if path.startswith(prefix) and len(prefix) > matched_len:
            matched = limit
            matched_len = len(prefix)
    return matched


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter backed by a simple in-memory dict.

    Falls through after printing a warning if Redis is not configured.
    For production, replace with a Redis-backed sliding-window counter.
    """

    def __init__(self, app, storage: dict[str, list[float]] | None = None):
        super().__init__(app)
        self._storage: dict[str, list[float]] = storage or {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        limit = _match_limit(request.url.path)
        if limit is None:
            return await call_next(request)

        max_reqs, window = limit
        client_key = f"{request.client.host}:{request.url.path}"
        now = time.time()

        timestamps = self._storage.get(client_key, [])
        timestamps = [t for t in timestamps if t > now - window]
        self._storage[client_key] = timestamps

        if len(timestamps) >= max_reqs:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={"Retry-After": str(int(window))},
            )

        self._storage[client_key].append(now)
        return await call_next(request)
