"""Async TTL cache with single-flight protection.

Modelled on the DQX app's `cache.py` (see Field Engineering's DQX repo).
Pure stdlib — no third-party cache libraries.

Usage:

    from backend.cache import app_cache

    @app_cache.cached("auth:obo:{token_hash}", ttl=45 * 60)
    async def _create_obo_ws(token_hash: str, token: str) -> WorkspaceClient:
        return WorkspaceClient(token=token, auth_type="pat")

The `key_template` is `format_map`-ed against the wrapped function's bound
arguments (excluding `self`). On cache miss, a per-key asyncio.Lock prevents
the thundering-herd where N concurrent callers all trigger the underlying
fetch — only the first proceeds; the rest await the same result.
"""

from __future__ import annotations

import asyncio
import functools
import inspect
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AsyncTTLCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def _get_lock(self, key: str) -> asyncio.Lock:
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock

    async def get(self, key: str) -> Any:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            self._store.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        expires_at = time.monotonic() + (ttl if ttl is not None else 60 * 60)
        self._store[key] = (value, expires_at)

    async def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def cached(
        self, key_template: str, *, ttl: int | None = None
    ) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
        """Cache-aside decorator with single-flight protection."""

        def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            sig = inspect.signature(fn)

            @functools.wraps(fn)
            async def wrapper(*args: Any, **kwargs: Any) -> T:
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                key_args = {k: v for k, v in bound.arguments.items() if k != "self"}
                cache_key = key_template.format_map(key_args)

                hit = await self.get(cache_key)
                if hit is not None:
                    return hit  # type: ignore[no-any-return]

                async with self._get_lock(cache_key):
                    hit = await self.get(cache_key)
                    if hit is not None:
                        return hit  # type: ignore[no-any-return]
                    result = await fn(*args, **kwargs)
                    if result is not None:
                        await self.set(cache_key, result, ttl=ttl)
                    return result

            return wrapper

        return decorator


app_cache = AsyncTTLCache()
