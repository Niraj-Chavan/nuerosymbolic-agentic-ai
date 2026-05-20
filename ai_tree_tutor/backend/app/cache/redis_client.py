"""
Redis Cache Client
===================
Async Redis connection pool, caching decorator, and utilities.
"""

from __future__ import annotations

import asyncio
import functools
import hashlib
import json
import logging
import os
import pickle
from typing import Any, Callable, Optional, TypeVar

try:
    import redis.asyncio as aioredis
except ModuleNotFoundError:  # Redis is optional in local/test environments.
    aioredis = None

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Connection pool (singleton)
# ---------------------------------------------------------------------------

_pool: Optional[Any] = None
_lock = asyncio.Lock()


async def get_redis() -> Any:
    if not os.getenv("REDIS_URL"):
        raise RuntimeError("REDIS_URL is not set; cache is disabled.")
    if aioredis is None:
        raise RuntimeError("Redis package is not installed; cache is disabled.")

    global _pool
    if _pool is None:
        async with _lock:
            if _pool is None:
                _pool = aioredis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=3,
                    socket_timeout=3,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
    return _pool


async def close_redis() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


def _make_cache_key(prefix: str, *args, **kwargs) -> str:
    raw = f"{prefix}:{args}:{sorted(kwargs.items())}"
    return f"ait:{prefix}:{hashlib.sha256(raw.encode()).hexdigest()[:16]}"


# ---------------------------------------------------------------------------
# Decorator: cached(ttl=300)
# ---------------------------------------------------------------------------

F = TypeVar("F", bound=Callable[..., Any])


def cached(ttl: int = 300, prefix: str = "generic"):
    """
    Decorator that caches the return value of an async function in Redis.

    Usage::

        @cached(ttl=600, prefix="concepts")
        async def get_concept_graph(...):
            ...

    The decorated function must be called with keyword arguments only
    for reliable cache key generation.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                redis = await get_redis()
                key = _make_cache_key(prefix, *args, **kwargs)
                cached_val = await redis.get(key)
                if cached_val is not None:
                    return pickle.loads(cached_val) if isinstance(cached_val, bytes) else json.loads(cached_val)
            except Exception as e:
                logger.warning("Cache GET failed (falling through): %s", e)

            result = await func(*args, **kwargs)

            try:
                redis = await get_redis()
                key = _make_cache_key(prefix, *args, **kwargs)
                serialized = json.dumps(result, default=str)
                await redis.setex(key, ttl, serialized)
            except Exception as e:
                logger.warning("Cache SET failed: %s", e)

            return result
        return wrapper  # type: ignore
    return decorator


# ---------------------------------------------------------------------------
# Cache invalidation helpers
# ---------------------------------------------------------------------------

CACHE_PREFIXES = {
    "validation": "val",
    "concepts": "con",
    "quiz": "quiz",
    "complexity": "cpx",
}


async def invalidate_tree_cache(session_id: str, tree_type: str) -> None:
    """Invalidate validation and complexity caches after a tree mutation."""
    try:
        redis = await get_redis()
        pattern = f"ait:val:*{session_id}*{tree_type}*"
        cur, keys = await redis.scan(match=pattern)
        if keys:
            await redis.delete(*keys)
    except Exception as e:
        logger.warning("Cache invalidation failed: %s", e)


async def invalidate_concept_cache() -> None:
    """Invalidate all concept-graph caches (after quiz/tree operation)."""
    try:
        redis = await get_redis()
        cur, keys = await redis.scan(match="ait:con:*")
        if keys:
            await redis.delete(*keys)
    except Exception as e:
        logger.warning("Concept cache invalidation failed: %s", e)


async def invalidate_quiz_cache(session_id: str) -> None:
    """Invalidate quiz-generation caches for a session."""
    try:
        redis = await get_redis()
        pattern = f"ait:quiz:*{session_id}*"
        cur, keys = await redis.scan(match=pattern)
        if keys:
            await redis.delete(*keys)
    except Exception as e:
        logger.warning("Quiz cache invalidation failed: %s", e)
