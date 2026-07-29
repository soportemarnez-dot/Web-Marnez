"""Cache en memoria para listados públicos (blogs / desarrollos)."""

from __future__ import annotations

import time
from threading import Lock
from typing import Any, Callable

_lock = Lock()
_store: dict[str, tuple[float, Any]] = {}
DEFAULT_TTL = 60.0


def cache_get(key: str):
    with _lock:
        item = _store.get(key)
        if not item:
            return None
        expires, value = item
        if time.monotonic() > expires:
            _store.pop(key, None)
            return None
        return value


def cache_set(key: str, value: Any, ttl: float = DEFAULT_TTL) -> None:
    with _lock:
        _store[key] = (time.monotonic() + ttl, value)


def cache_invalidate(*prefixes: str) -> None:
    with _lock:
        if not prefixes:
            _store.clear()
            return
        keys = [k for k in _store if any(k.startswith(p) for p in prefixes)]
        for k in keys:
            _store.pop(k, None)


def cached(key: str, loader: Callable[[], Any], ttl: float = DEFAULT_TTL):
    hit = cache_get(key)
    if hit is not None:
        return hit
    value = loader()
    cache_set(key, value, ttl=ttl)
    return value
