"""Deterministic & Semantic Response Cache for Phase 19.

Caches deterministic, high-latency responses with strict TTL freshness, security scopes,
and immediate invalidation for sensitive or dynamic states.
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger("shivani.ai.cache")


@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: float
    ttl_sec: float
    security_scope: str = "general"

    def is_expired(self) -> bool:
        return time.time() > (self.created_at + self.ttl_sec)


class SemanticCache:
    """In-memory cache for deterministic responses and static model metadata."""

    def __init__(self, default_ttl_sec: float = 3600.0):
        self.default_ttl_sec = default_ttl_sec
        self._lock = threading.RLock()
        self._cache: Dict[str, CacheEntry] = {}

    def _generate_key(self, query: str, context_hash: str = "") -> str:
        raw = f"{query.strip().lower()}::{context_hash}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, query: str, context_hash: str = "") -> Optional[Any]:
        """Retrieve cached result if valid and not expired."""
        with self._lock:
            key = self._generate_key(query, context_hash)
            entry = self._cache.get(key)
            if not entry:
                return None

            if entry.is_expired():
                del self._cache[key]
                return None

            logger.info(f"Cache hit for query '{query[:30]}'")
            return entry.value

    def set(
        self,
        query: str,
        value: Any,
        context_hash: str = "",
        ttl_sec: Optional[float] = None,
        security_scope: str = "general",
    ) -> None:
        """Store safe result in cache."""
        # Never cache credentials or tokens
        str_val = str(value)
        if any(s in str_val.lower() for s in ["token", "secret", "password", "key", "bearer"]):
            logger.warning("Refused to cache payload containing potential secret credentials.")
            return

        with self._lock:
            key = self._generate_key(query, context_hash)
            self._cache[key] = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                ttl_sec=ttl_sec or self.default_ttl_sec,
                security_scope=security_scope,
            )

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            logger.info("Cleared semantic response cache.")
